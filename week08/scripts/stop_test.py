"""Safety-envelope experiment: drive at the wall of the range world, brake on the LiDAR, measure the real clearance.

Each run: the robot starts at x = --x0 (LiDAR 6.93 m from the wall), drives straight at --v, and as soon as the
nearest VALID beam in the front +/-10 deg sector reads less than --d it brakes with a constant deceleration --a
(a ramp of commanded speed). The final clearance between the FRONT EDGE of the body (0.15 m ahead of the base) and the
wall (x = 6.95 m) is measured from /ground_truth/odom, together with where the robot really was when it decided.
--delay adds an artificial sensor-chain latency, as in reactive.py.

Usage (simulator started with world:=range x:=0 y:=0 camera:=false):
    python3 ~/labs/week08/scripts/stop_test.py --v 0.3 --d 0.6 --a 1.0 --runs 3
    python3 ~/labs/week08/scripts/stop_test.py --v 0.5 --d 0.6 --a 1.0 --delay 0.2
Expected output (one line per run):
    v 0.30  d 0.60  a 1.0  delay 0.00 | read 0.595 m (true 0.614, age 0.000 s) | after decision 0.052 m | clearance 0.431 m
"""
import argparse
import math

import numpy as np
import rclpy
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan

from move_to import Mover

WALL_X, LIDAR_X, FRONT_X = 6.95, 0.02, 0.15    # wall face; LiDAR and body front ahead of base_footprint (m)

ap = argparse.ArgumentParser()
ap.add_argument('--v', type=float, default=0.3)
ap.add_argument('--d', type=float, default=0.6, help='trigger distance measured by the LiDAR, m')
ap.add_argument('--a', type=float, default=1.0, help='commanded deceleration, m/s^2')
ap.add_argument('--delay', type=float, default=0.0, help='extra latency added to every scan, s')
ap.add_argument('--runs', type=int, default=1)
ap.add_argument('--x0', type=float, default=0.0)
a = ap.parse_args()


def front_min(s):
    r = np.asarray(s.ranges, dtype=np.float64)
    ang = s.angle_min + np.arange(r.size) * s.angle_increment
    ok = np.isfinite(r) & (r > 0) & (r >= s.range_min) & (r <= s.range_max)
    ok &= np.abs(np.arctan2(np.sin(ang), np.cos(ang))) <= math.radians(10)   # wrapped angle
    return r[ok].min() if ok.any() else math.inf


scans = []                                                      # (arrival time, stamp, front range)


def on_scan(node, s):
    scans.append((node.get_clock().now().nanoseconds * 1e-9,
                  s.header.stamp.sec + 1e-9 * s.header.stamp.nanosec, front_min(s)))


def run_once(node):
    node.go(a.x0, 0.0)                                          # back to the start line (and stopped)
    now = lambda: node.get_clock().now().nanoseconds * 1e-9
    scans.clear()                                               # forget scans taken before this run
    cmd, t_dec, last = Twist(), None, 0.0
    read = age = x_dec = math.nan                               # stay nan if the wall abort fires first
    while rclpy.ok():
        node.ex.spin_once(timeout_sec=0.005)
        t = now()
        if t_dec is None:                                       # driving: look at scans old enough to "arrive"
            cmd.linear.x = a.v
            while scans and t - scans[0][0] >= a.delay:
                _, stamp, r = scans.pop(0)
                if r < a.d:
                    t_dec, read, age, x_dec = t, r, t - stamp, node.pose[0]
                    break
        if t_dec is not None:                                   # braking: constant-deceleration ramp
            cmd.linear.x = max(0.0, a.v - a.a * (t - t_dec))
        if node.pose[0] + FRONT_X > WALL_X - 0.005:             # about to touch the wall: abort
            cmd.linear.x = 0.0
            t_dec = t_dec or t
        if t - last >= 0.02 or cmd.linear.x == 0.0:             # publish at 50 Hz
            node.pub.publish(cmd)
            last = t
        if t_dec is not None and cmd.linear.x == 0.0:
            break
    node.stop()
    t_end = now() + 1.0
    while now() < t_end:                                        # let the robot settle, then read the truth
        node.ex.spin_once(timeout_sec=0.05)
    clearance = WALL_X - (node.pose[0] + FRONT_X)
    print('v %.2f  d %.2f  a %.1f  delay %.2f | read %.3f m (true %.3f, age %.3f s) | after decision %.3f m'
          ' | clearance %.3f m' % (a.v, a.d, a.a, a.delay, read, WALL_X - x_dec - LIDAR_X, age,
                                   node.pose[0] - x_dec, clearance), flush=True)
    return clearance


def main():
    rclpy.init()
    node = Mover()
    node.create_subscription(LaserScan, '/scan', lambda s: on_scan(node, s), qos_profile_sensor_data)
    c = [run_once(node) for _ in range(a.runs)]
    print('clearance over %d runs: mean %.3f m  min %.3f m  max %.3f m' % (len(c), np.mean(c), min(c), max(c)))
    node.go(a.x0, 0.0)
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
