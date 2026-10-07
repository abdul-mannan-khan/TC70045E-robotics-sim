#!/usr/bin/env python3
"""AirSim WITH ROS 2 - a mission written as an ordinary ROS 2 node (no MAVSDK, no AirSim API in this file).

Needs the simulator and BOTH bridges running:
   drone-sim start --world blocks
   python3 ~/labs/examples/airsim/03_airsim_ros2_bridge.py     (sensors -> ROS 2)
   python3 ~/labs/examples/airsim/04_px4_ros2_bridge.py        (ROS 2 -> autopilot)
Then run:  python3 ~/labs/examples/airsim/05_fly_square_ros2.py [--side 5]

Takes off, flies a square by velocity commands while watching /drone/odom (the simulator's ground truth),
lands, and prints how far from the start it finished.

Pipeline:   this node --/drone/cmd_vel--> px4 bridge --> PX4 --> AirSim --> airsim bridge --/drone/odom--> this node
"""
import argparse
import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_srvs.srv import Trigger


class Square(Node):
    def __init__(self):
        super().__init__('fly_square')
        self.pos = None
        self.yaw = 0.0
        self.create_subscription(Odometry, '/drone/odom', self.on_odom, 10)
        self.pub = self.create_publisher(Twist, '/drone/cmd_vel', 10)

    def on_odom(self, m):
        self.pos = (m.pose.pose.position.x, m.pose.pose.position.y, m.pose.pose.position.z)
        q = m.pose.pose.orientation
        self.yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))

    def trigger(self, name):
        cli = self.create_client(Trigger, name)
        cli.wait_for_service()
        fut = cli.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, fut)
        self.get_logger().info('%s: %s' % (name, fut.result().message))
        return fut.result().success

    def go_to(self, x, y, speed=1.0):
        """Fly to (x, y) in the map frame (ENU) with a simple proportional velocity command."""
        next_cmd = 0.0
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.02)
            if time.time() < next_cmd:                 # command at 10 Hz, read odometry as fast as it comes
                continue
            next_cmd = time.time() + 0.1
            ex, ey = x - self.pos[0], y - self.pos[1]
            if math.hypot(ex, ey) < 0.3:
                break
            # The error is in the map frame; /drone/cmd_vel is in the body frame, so rotate it by -yaw.
            scale = min(speed, 0.5 * math.hypot(ex, ey)) / math.hypot(ex, ey)
            c, s = math.cos(self.yaw), math.sin(self.yaw)
            cmd = Twist()
            cmd.linear.x = (c * ex + s * ey) * scale
            cmd.linear.y = (-s * ex + c * ey) * scale
            self.pub.publish(cmd)
        self.pub.publish(Twist())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--side', type=float, default=5.0)
    a, _ = ap.parse_known_args()
    rclpy.init()
    n = Square()
    while n.pos is None:
        rclpy.spin_once(n, timeout_sec=0.2)
    start = n.pos
    if not n.trigger('/drone/takeoff'):
        return
    s = a.side
    for dx, dy in [(s, 0), (s, s), (0, s), (0, 0)]:
        n.get_logger().info('-> corner %+.1f m east, %+.1f m north' % (dx, dy))
        n.go_to(start[0] + dx, start[1] + dy)
    time.sleep(1)
    n.trigger('/drone/land')
    rclpy.spin_once(n, timeout_sec=0.5)
    print('RESULT finished %.2f m (horizontal) from the start of the square' %
          math.hypot(n.pos[0] - start[0], n.pos[1] - start[1]))
    n.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
