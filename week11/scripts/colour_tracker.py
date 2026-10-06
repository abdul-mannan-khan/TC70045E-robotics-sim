#!/usr/bin/env python3
"""colour_tracker.py - find the red box, turn to it and hold a stand-off distance using depth (Week 11, Lab A).

  colour:  HSV mask for saturated red (hue wraps: 0-4 and 175-179, S >= 200, V >= 60) -> largest blob -> centroid
           (S >= 200 rejects the brick walls, S up to ~180; H <= 4 rejects the wood crate/posters, H 6-17)
  range:   median of the aligned depth (16UC1 mm) inside the blob -> d [m]
  control: w = -kp_yaw * e  (e = normalised horizontal error),  v = kp_d * (d - d_ref), |v| <= 0.15 m/s
  search:  no blob -> turn on the spot at 0.3 rad/s clockwise
Stops (zero Twist) when settled for 3 s, after --duration, or on Ctrl+C.

Truth for evaluation: /ground_truth/odom and the box position (-1.5, -2.8), half size 0.15 m.
Usage (lab world, spawned 2.3 m north of the box and facing it - from the default spawn crate_1 blocks the way):
  ros2 launch tc70045e_sim sim.launch.py gui:=false camera_width:=424 camera_height:=240 x:=-1.5 y:=-0.5 yaw:=-1.5708
  python3 ~/labs/week11/scripts/colour_tracker.py --d-ref 1.0
Prints time to acquire, the measured and the TRUE stand-off, the bearing error and the latencies.
"""
import argparse
import math
import time

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import Image

BOX = (-1.5, -2.8)
CAM_X = 0.14  # camera ahead of base_footprint [m]


class Tracker(Node):
    def __init__(self, a):
        super().__init__('colour_tracker', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', value=True)])
        self.a, self.bridge, self.depth, self.truth = a, CvBridge(), None, None
        self.cmd = self.create_publisher(Twist, '/cmd_vel', 1)
        self.create_subscription(Image, '/camera/color/image_raw', self.on_image, 1)
        self.create_subscription(Image, '/camera/aligned_depth_to_color/image_raw', self.on_depth, 1)
        self.create_subscription(Odometry, '/ground_truth/odom', self.on_truth, 10)
        self.t0, self.t_acq, self.settled_since, self.log = time.monotonic(), None, None, []
        self.create_timer(0.5, self.check_time)

    def check_time(self):
        if time.monotonic() - self.t0 > self.a.duration:
            raise SystemExit

    def on_depth(self, msg):
        self.depth = self.bridge.imgmsg_to_cv2(msg, 'passthrough')

    def on_truth(self, msg):
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        self.truth = (p.x, p.y, math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2)))

    def on_image(self, msg):
        t_cb = time.monotonic()
        img = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lo, hi = (0, self.a.s_min, 60), (4, 255, 255)          # pure red only: wood textures sit at H 6-17
        mask = cv2.inRange(hsv, lo, hi) | cv2.inRange(hsv, (175,) + lo[1:], (179,) + hi[1:])
        n, lab, stats, cent = cv2.connectedComponentsWithStats(mask)
        cmd, e, d = Twist(), float('nan'), float('nan')
        if n > 1 and stats[1:, cv2.CC_STAT_AREA].max() >= self.a.a_min_frac * mask.size:
            k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            e = (cent[k][0] - img.shape[1] / 2) / (img.shape[1] / 2)
            if self.depth is not None and self.depth.shape == mask.shape:
                z = self.depth[lab == k]
                z = z[z > 0]
                d = float(np.median(z)) * 1e-3 if z.size > 20 else float('nan')
            self.t_acq = self.t_acq or time.monotonic() - self.t0
            cmd.angular.z = -self.a.kp_yaw * e
            if not math.isnan(d) and abs(e) < 0.2:
                cmd.linear.x = float(np.clip(self.a.kp_d * (d - self.a.d_ref), -0.15, 0.15))
            ok = not math.isnan(d) and abs(d - self.a.d_ref) < 0.05 and abs(e) < 0.05
            self.settled_since = (self.settled_since or time.monotonic()) if ok else None
        else:
            cmd.angular.z = -0.3                      # search (clockwise: the box is to the right of the spawn)
        self.cmd.publish(cmd)
        age = (self.get_clock().now() - rclpy.time.Time.from_msg(msg.header.stamp)).nanoseconds * 1e-6
        self.log.append((e, d, (time.monotonic() - t_cb) * 1e3, age))
        done = self.settled_since and time.monotonic() - self.settled_since > 3.0
        if done or time.monotonic() - self.t0 > self.a.duration:
            raise SystemExit

    def summary(self):
        self.cmd.publish(Twist())
        r = np.array(self.log, dtype=float)
        print(f'frames {len(r)}, acquired after {self.t_acq if self.t_acq else float("nan"):.1f} s, '
              f'stopped after {time.monotonic() - self.t0:.1f} s')
        if len(r):
            print(f'processing p50 {np.nanpercentile(r[:, 2], 50):.1f} ms, '
                  f'image age p50 {np.nanpercentile(r[:, 3], 50):.0f} ms p95 {np.nanpercentile(r[:, 3], 95):.0f} ms')
            print(f'last: e = {r[-1, 0]:+.3f}, measured stand-off d = {r[-1, 1]:.3f} m (target {self.a.d_ref})')
        if self.truth:
            x, y, yaw = self.truth
            bearing = math.atan2(BOX[1] - y, BOX[0] - x)
            true_d = math.hypot(BOX[0] - x, BOX[1] - y) - CAM_X - 0.15
            err = math.degrees(math.atan2(math.sin(bearing - yaw), math.cos(bearing - yaw)))
            print(f'truth: camera-to-box-face {true_d:.3f} m, bearing error {err:+.1f} deg')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--d-ref', type=float, default=1.0)
    ap.add_argument('--kp-yaw', type=float, default=0.8)
    ap.add_argument('--kp-d', type=float, default=0.5)
    ap.add_argument('--s-min', type=int, default=200)   # the brick walls reach S = 180
    ap.add_argument('--a-min-frac', type=float, default=0.0004, help='min blob area / image area')
    ap.add_argument('--duration', type=float, default=120.0)
    a, ros_args = ap.parse_known_args()
    rclpy.init(args=ros_args, signal_handler_options=SignalHandlerOptions.NO)
    node = Tracker(a)
    try:
        rclpy.spin(node)
    except (SystemExit, KeyboardInterrupt):
        pass
    node.summary()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
