#!/usr/bin/env python3
"""drive_loop.py - drive the simulated lab robot round a fixed ~25 m circuit and score the SLAM estimate.

Purpose
  1. Drives the same closed circuit every time (west room -> door -> round the crate in the east room ->
     back through the door -> round the pillar -> back to the start), so two SLAM runs are comparable.
     The driver steers on /ground_truth/odom: it is a test harness, the SLAM node never sees that topic.
  2. While driving it logs three poses: the SLAM estimate (TF map -> base_footprint), wheel odometry
     (/odom_raw) and the truth, and at the end prints the position error of SLAM and of odometry.

Frames: the SLAM map frame starts where the robot started, so  world = map + spawn pose
        (spawn (-3.0, -0.4, 0) in the lab world).

Usage (simulator + a SLAM node already running, everything with sim time):
  python3 ~/labs/week09/scripts/drive_loop.py --ros-args -p use_sim_time:=true
  ... -p speed:=0.15 -p turn_rate:=0.3       slower (Week 10, camera at ~7 Hz)
  ... -p drive:=false                        only score: drive yourself with teleop, Ctrl+C to finish
  ... -p csv:=run1.csv                       also save t, truth, slam and odom poses

Expected output (end of the run)
  loop finished: 25.1 m in 162 s
  error at the end [m]   SLAM 0.03   odometry 0.52
  RMS error        [m]   SLAM 0.04   odometry 0.29
"""
import math
import time
import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from tf2_ros import Buffer, TransformListener

# circuit in WORLD coordinates (lab world); the robot starts at (-3.0, -0.4) facing +x
CIRCUIT = [(-0.2, -1.5), (2.0, -1.2), (2.0, 1.5), (4.0, 0.6), (3.4, -0.9), (2.0, -1.2), (-0.2, -1.5),
           (-0.5, 1.6), (-2.5, 2.1), (-3.6, 2.1), (-3.6, -0.4), (-3.0, -0.4)]


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


class DriveLoop(Node):
    def __init__(self):
        super().__init__('drive_loop')
        p = self.declare_parameter
        self.drive = p('drive', True).value
        self.speed, self.turn = p('speed', 0.25).value, p('turn_rate', 0.4).value
        self.spawn = (p('spawn_x', -3.0).value, p('spawn_y', -0.4).value, p('spawn_yaw', 0.0).value)
        self.map_frame = p('map_frame', 'map').value
        self.csv = p('csv', '').value
        self.truth = self.odom = None
        self.rows, self.wp, self.done, self.dist, self.last = [], 0, False, 0.0, None
        self.tf = Buffer()
        TransformListener(self.tf, self)
        self.cmd = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Odometry, '/ground_truth/odom', self.on_truth, 10)
        self.create_subscription(Odometry, '/odom_raw', self.on_odom, 10)
        self.create_timer(0.05, self.control)     # 20 Hz driver
        self.create_timer(0.5, self.log)          # 2 Hz error log
        self.t0 = None

    def on_truth(self, m):
        pp = m.pose.pose
        self.truth = (pp.position.x, pp.position.y, yaw_of(pp.orientation))

    def on_odom(self, m):
        pp = m.pose.pose
        self.odom = (pp.position.x, pp.position.y, yaw_of(pp.orientation))

    def truth_in_map(self):
        """World pose -> start (map) frame: subtract the spawn pose."""
        x, y, th = self.truth
        sx, sy, sth = self.spawn
        dx, dy = x - sx, y - sy
        c, s = math.cos(-sth), math.sin(-sth)
        return c * dx - s * dy, s * dx + c * dy, wrap(th - sth)

    def control(self):
        if not self.drive or self.truth is None or self.done:
            return
        x, y, th = self.truth
        if self.last:
            self.dist += math.hypot(x - self.last[0], y - self.last[1])
        self.last = (x, y)
        if self.t0 is None:
            self.t0 = self.get_clock().now()
        gx, gy = CIRCUIT[self.wp]
        d = math.hypot(gx - x, gy - y)
        err = wrap(math.atan2(gy - y, gx - x) - th)
        cmd = Twist()
        if d < 0.08:
            self.wp += 1
            if self.wp == len(CIRCUIT):
                self.done = True
                self.cmd.publish(Twist())                 # no command timeout: stop explicitly
                sec = (self.get_clock().now() - self.t0).nanoseconds * 1e-9
                self.get_logger().info('loop finished: %.1f m in %.0f s' % (self.dist, sec))
                self.report()
            return
        if abs(err) > 0.15:                               # turn on the spot towards the waypoint
            cmd.angular.z = max(-self.turn, min(self.turn, 1.5 * err))
        else:                                             # drive, slowing for the last 0.4 m
            cmd.linear.x = self.speed * min(1.0, d / 0.4 + 0.2)
            cmd.angular.z = max(-self.turn, min(self.turn, 1.5 * err))
        self.cmd.publish(cmd)

    def log(self):
        if self.truth is None or self.odom is None:
            return
        try:
            tr = self.tf.lookup_transform(self.map_frame, 'base_footprint', rclpy.time.Time())
        except Exception:                                 # no SLAM running yet: log odometry only
            slam = (math.nan, math.nan)
        else:
            slam = (tr.transform.translation.x, tr.transform.translation.y)
        t = self.get_clock().now().nanoseconds * 1e-9
        self.rows.append((t,) + self.truth_in_map()[:2] + slam + self.odom[:2])

    def report(self):
        if not self.rows:
            print('no data logged - is the simulator running with use_sim_time?')
            return
        def err(i):
            e = [math.hypot(r[i] - r[1], r[i + 1] - r[2]) for r in self.rows]
            ok = [v for v in e if not math.isnan(v)]
            return (e[-1], math.sqrt(sum(v * v for v in ok) / len(ok)), max(ok)) if ok else (math.nan,) * 3
        s, o = err(3), err(5)
        lost = sum(math.isnan(r[3]) for r in self.rows)
        print('samples: %d at 2 Hz (no map -> base_footprint TF in %d of them)' % (len(self.rows), lost))
        print('error at the end [m]   SLAM %.3f   odometry %.3f' % (s[0], o[0]))
        print('RMS error        [m]   SLAM %.3f   odometry %.3f' % (s[1], o[1]))
        print('max error        [m]   SLAM %.3f   odometry %.3f' % (s[2], o[2]))
        if self.csv:
            with open(self.csv, 'w') as f:
                f.write('t,truth_x,truth_y,slam_x,slam_y,odom_x,odom_y\n')
                f.writelines(','.join('%.3f' % v for v in r) + '\n' for r in self.rows)
            print('saved', self.csv)


def main():
    # keep the ROS context alive on Ctrl+C so that the final zero Twist can still be published
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = DriveLoop()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        node.report()
    finally:
        stop_robot(node)
        node.destroy_node()
        rclpy.try_shutdown()


def stop_robot(node):
    """The simulated robot has no command timeout: always leave it with a zero Twist."""
    for _ in range(5):
        node.cmd.publish(Twist())
        time.sleep(0.02)

if __name__ == '__main__':
    main()
