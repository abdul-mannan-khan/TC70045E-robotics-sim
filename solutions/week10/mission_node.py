#!/usr/bin/env python3
"""mission_node.py - a waypoint mission with photographs, written as an ordinary ROS 2 node (Week 10, SOLUTION).

Needs the simulator and BOTH bridges (three terminals):
   drone-sim start --world blocks
   python3 ~/labs/week10/scripts/03_airsim_ros2_bridge.py       (AirSim sensors -> ROS 2 topics)
   python3 ~/labs/week10/scripts/04_px4_ros2_bridge.py          (ROS 2 commands -> PX4 autopilot)
Then:      python3 ~/labs/week10/scripts/mission_node.py

What it does
  1. take off           service /drone/takeoff (the PX4 bridge climbs to 5 m)
  2. fly                to each waypoint with a velocity command on /drone/cmd_vel: the error is in the map frame
                        (ENU), the command in the body frame (FLU) - rotate it by the drone's yaw          (TODO 1)
  3. face + photo       turn the camera towards the middle of the square (so the drone's yaw changes - which is
                        why TODO 1 matters), hover until (nearly) still, then save the newest /drone/front/image_raw
                        to ~/mission/wpNN.png - a photo taken while moving is blurred and points elsewhere  (TODO 2)
  4. watchdog           if /drone/odom stops arriving for 1 s (a bridge died), stop and land at once       (TODO 3)
  5. land               service /drone/land; print time, distance flown and the worst waypoint miss

Pipeline:  this node --/drone/cmd_vel, /drone/takeoff, /drone/land--> PX4 bridge --> PX4 --> AirSim
           AirSim --> AirSim bridge --/drone/odom, /drone/front/image_raw--> this node
"""
import math
import os
import time

import cv2
import numpy as np
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_srvs.srv import Trigger

# waypoints in the map frame (ENU, metres from the take-off point): x east, y north
WAYPOINTS = [(10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
SPEED, TOL, STILL = 2.0, 0.5, 0.2         # m/s max, "reached" radius [m], "still" below this speed [m/s]
WP_TIMEOUT = 60.0                         # s: a waypoint not reached by then ends the mission (land)


class Mission(Node):
    def __init__(self):
        super().__init__('mission')
        self.pos, self.yaw, self.vel, self.t_odom, self.img = None, 0.0, 0.0, 0.0, None
        self.create_subscription(Odometry, '/drone/odom', self.on_odom, 10)
        self.create_subscription(Image, '/drone/front/image_raw', lambda m: setattr(self, 'img', m), 2)
        self.pub = self.create_publisher(Twist, '/drone/cmd_vel', 10)
        self.folder = os.path.expanduser('~/mission')
        os.makedirs(self.folder, exist_ok=True)

    def on_odom(self, m):
        p, q, v = m.pose.pose.position, m.pose.pose.orientation, m.twist.twist.linear
        self.pos = (p.x, p.y, p.z)
        self.yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        self.vel = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
        self.t_odom = time.monotonic()

    def trigger(self, name):
        cli = self.create_client(Trigger, name)
        cli.wait_for_service()
        fut = cli.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, fut)
        self.get_logger().info('%s: %s' % (name, fut.result().message))
        return fut.result().success

    def odom_ok(self):
        # SOLUTION TODO 3: watchdog - no odometry for 1 s means we are flying blind
        return time.monotonic() - self.t_odom < 1.0

    def go_to(self, x, y):
        """Fly to (x, y) in the map frame. Returns 'ok', 'watchdog' (no odometry) or 'timeout' (not there in time)."""
        next_cmd, t0 = 0.0, time.monotonic()
        while rclpy.ok():
            if time.monotonic() - t0 > WP_TIMEOUT:
                self.pub.publish(Twist())
                return 'timeout'
            rclpy.spin_once(self, timeout_sec=0.02)
            if not self.odom_ok():
                self.pub.publish(Twist())
                return 'watchdog'
            if time.time() < next_cmd:
                continue
            next_cmd = time.time() + 0.1                  # command at 10 Hz
            ex, ey = x - self.pos[0], y - self.pos[1]
            d = math.hypot(ex, ey)
            if d < TOL:
                break
            k = min(SPEED, 0.6 * d) / d                    # slow down for the last few metres
            # SOLUTION TODO 1: map-frame error -> body-frame velocity: rotate by -yaw
            c, s = math.cos(self.yaw), math.sin(self.yaw)
            cmd = Twist()
            cmd.linear.x = (c * ex + s * ey) * k
            cmd.linear.y = (-s * ex + c * ey) * k
            self.pub.publish(cmd)
        self.pub.publish(Twist())
        return 'ok'

    def face(self, x, y):
        """Turn on the spot until the front camera points at (x, y) in the map frame (given code)."""
        t0 = time.monotonic()
        while rclpy.ok() and time.monotonic() - t0 < 15.0:
            rclpy.spin_once(self, timeout_sec=0.05)
            err = math.atan2(y - self.pos[1], x - self.pos[0]) - self.yaw
            err = math.atan2(math.sin(err), math.cos(err))
            if abs(err) < math.radians(5):
                break
            cmd = Twist()
            cmd.angular.z = max(-0.6, min(0.6, 1.0 * err))
            self.pub.publish(cmd)
        self.pub.publish(Twist())

    def photo(self, n):
        # SOLUTION TODO 2: wait until the drone is (nearly) still, then take the NEXT image (not an old one)
        t0 = time.monotonic()
        while rclpy.ok() and self.vel > STILL and time.monotonic() - t0 < 10.0:
            self.pub.publish(Twist())
            rclpy.spin_once(self, timeout_sec=0.05)
        self.img = None
        t0 = time.monotonic()
        while rclpy.ok() and self.img is None and time.monotonic() - t0 < 2.0:
            rclpy.spin_once(self, timeout_sec=0.05)
        if self.img is None:
            return None, self.vel                         # no camera: the AirSim bridge has died
        m = self.img
        bgr = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, -1)[:, :, :3]
        if m.encoding == 'rgb8':
            bgr = bgr[:, :, ::-1]
        path = os.path.join(self.folder, 'wp%02d.png' % n)
        cv2.imwrite(path, bgr)
        return path, self.vel


def main():
    rclpy.init()
    n = Mission()
    while n.pos is None:
        rclpy.spin_once(n, timeout_sec=0.2)
    start = n.pos
    if not n.trigger('/drone/takeoff'):
        return
    t0, dist, worst, last = time.monotonic(), 0.0, 0.0, (start[0], start[1])
    for i, (dx, dy) in enumerate(WAYPOINTS, 1):
        x, y = start[0] + dx, start[1] + dy
        result = n.go_to(x, y)
        if result == 'watchdog':
            print('WATCHDOG: no odometry for 1 s - landing now', flush=True)
            break
        if result == 'timeout':
            print('waypoint %d/%d  NOT reached in %.0f s (%.1f m away) - landing now'
                  % (i, len(WAYPOINTS), WP_TIMEOUT, math.hypot(n.pos[0] - x, n.pos[1] - y)), flush=True)
            break
        miss = math.hypot(n.pos[0] - x, n.pos[1] - y)
        worst = max(worst, miss)
        dist += math.hypot(n.pos[0] - last[0], n.pos[1] - last[1])
        last = (n.pos[0], n.pos[1])
        n.face(start[0] + 5.0, start[1] + 5.0)          # the camera looks at the middle of the square
        path, v = n.photo(i)
        if path is None:
            print('WATCHDOG: no camera image for 2 s - landing now', flush=True)
            break
        print('waypoint %d/%d  east %5.1f  north %5.1f  miss %.2f m  photo at %.2f m/s -> %s'
              % (i, len(WAYPOINTS), dx, dy, miss, v, path), flush=True)
    n.trigger('/drone/land')
    print('RESULT %.0f s, %.1f m flown, worst waypoint miss %.2f m, finished %.2f m from the start'
          % (time.monotonic() - t0, dist, worst, math.hypot(n.pos[0] - start[0], n.pos[1] - start[1])), flush=True)
    n.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
