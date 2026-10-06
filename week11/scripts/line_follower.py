#!/usr/bin/env python3
"""line_follower.py - OpenCV line follower for the black floor line of the lab world (Week 11, Lab A).

Pipeline per frame:  cv_bridge -> HSV -> mask (V <= v_max and S <= s_max) in the lower image band -> moments
                     -> centroid -> normalised error e = (cx - w/2)/(w/2) -> PD on yaw rate -> /cmd_vel
Speed is reduced with the error: v = v0 (1 - lam |e|).  Line lost -> creep/turn towards the last error.
Watchdog: no image for 0.5 s -> zero Twist.  Ctrl+C or --duration -> zero Twist (the simulated base
keeps moving on the last command).

Evaluation (simulation only): cross-track error = distance of the TRUE robot position (/ground_truth/odom)
from the line rectangle x -4.0..-1.6, y -0.4..1.6; loop latency = callback time; image age = now - stamp.

Usage (lab world, robot at its default spawn on the line, camera on):
  python3 ~/labs/week11/scripts/line_follower.py --duration 120
  ros2 param set /line_follower kp 2.5          # live tuning from another terminal
  ... --ros-args -p s_max:=255                   # no saturation gate: watch the dark-brown crate capture it
Writes ~/labs/week11/data/line_follow.csv and prints a summary (RMS / max cross-track error, latencies).
"""
import argparse
import csv
import os
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

X0, X1, Y0, Y1 = -4.0, -1.6, -0.4, 1.6      # the line rectangle in the world frame


def cross_track(x, y):
    """Distance from (x, y) to the rectangle outline."""
    dx, dy = max(X0 - x, 0, x - X1), max(Y0 - y, 0, y - Y1)
    if dx or dy:
        return float(np.hypot(dx, dy))
    return min(x - X0, X1 - x, y - Y0, Y1 - y)


class LineFollower(Node):
    def __init__(self, a):
        super().__init__('line_follower', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', value=True)])
        for name, val in (('kp', 1.2), ('kd', 0.1), ('v0', 0.12), ('lam', 0.6),
                          ('v_max', 60), ('s_max', 60), ('roi_top', 0.6), ('a_min_frac', 0.001)):
            self.declare_parameter(name, val)
        self.bridge, self.a = CvBridge(), a
        self.cmd = self.create_publisher(Twist, '/cmd_vel', 1)
        self.create_subscription(Image, '/camera/color/image_raw', self.on_image, 1)
        self.create_subscription(Odometry, '/ground_truth/odom', self.on_truth, 10)
        self.create_timer(0.1, self.watchdog)
        self.e_prev, self.t_prev, self.last_img = 0.0, None, time.monotonic()
        self.truth, self.dist, self.rows, self.t_start = None, 0.0, [], time.monotonic()
        self.lost = 0

    def p(self, name):
        return self.get_parameter(name).value

    def on_truth(self, msg):
        pos = msg.pose.pose.position
        if self.truth is not None:
            self.dist += float(np.hypot(pos.x - self.truth[0], pos.y - self.truth[1]))
        self.truth = (pos.x, pos.y)

    def on_image(self, msg):
        t0 = time.monotonic()
        self.last_img = t0
        img = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        h, w = img.shape[:2]
        top = int(self.p('roi_top') * h)
        hsv = cv2.cvtColor(img[top:], cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, (0, 0, 0), (179, self.p('s_max'), self.p('v_max')))   # dark AND grey
        m = cv2.moments(mask, binaryImage=True)
        stamp = rclpy.time.Time.from_msg(msg.header.stamp)
        now = self.get_clock().now()
        t = now.nanoseconds * 1e-9
        cmd = Twist()
        if m['m00'] < self.p('a_min_frac') * w * (h - top):   # line lost: turn towards it
            self.lost += 1
            cmd.angular.z = -0.4 * np.sign(self.e_prev or 1.0)
            e = self.e_prev
        else:
            e = (m['m10'] / m['m00'] - w / 2) / (w / 2)   # -1 (left) .. +1 (right)
            de = (e - self.e_prev) / (t - self.t_prev) if self.t_prev and t > self.t_prev else 0.0
            cmd.angular.z = -(self.p('kp') * e + self.p('kd') * de)
            cmd.linear.x = self.p('v0') * max(0.0, 1.0 - self.p('lam') * abs(e))
        self.e_prev, self.t_prev = e, t
        self.cmd.publish(cmd)
        x, y = self.truth or (float('nan'), float('nan'))
        self.rows.append((round(t, 3), round(e, 4), round(cross_track(x, y), 4),
                          round((time.monotonic() - t0) * 1e3, 2), round((now - stamp).nanoseconds * 1e-6, 1),
                          round(cmd.linear.x, 3), round(cmd.angular.z, 3), round(x, 3), round(y, 3)))

    def watchdog(self):
        if time.monotonic() - self.last_img > 0.5:
            self.cmd.publish(Twist())
        if time.monotonic() - self.t_start > self.a.duration:
            raise SystemExit

    def summary(self):
        self.cmd.publish(Twist())
        os.makedirs(os.path.dirname(self.a.csv), exist_ok=True)
        with open(self.a.csv, 'w', newline='') as f:
            wr = csv.writer(f)
            wr.writerow(['t_sim', 'e_norm', 'xte_m', 'proc_ms', 'age_ms', 'v', 'w', 'x_true', 'y_true'])
            wr.writerows(self.rows)
        r = np.array([row[1:5] + row[7:9] for row in self.rows[10:]], dtype=float)   # skip start-up
        if len(r) == 0:
            print('no frames received')
            return
        xte = r[:, 1][~np.isnan(r[:, 1])]
        far = np.min([np.hypot(r[:, 4] - cx, r[:, 5] - cy) for cx in (X0, X1) for cy in (Y0, Y1)], axis=0) > 0.6
        straight = r[far, 1][~np.isnan(r[far, 1])]
        print(f'frames {len(self.rows)}, line lost in {self.lost}, distance travelled {self.dist:.2f} m')
        print(f'cross-track error: RMS {1e3 * np.sqrt(np.mean(xte ** 2)):.0f} mm, '
              f'p95 {1e3 * np.percentile(xte, 95):.0f} mm, max {1e3 * xte.max():.0f} mm; '
              f'straights only (> 0.6 m from a corner) RMS {1e3 * np.sqrt(np.mean(straight ** 2)):.0f} mm')
        print(f'processing p50 {np.percentile(r[:, 2], 50):.1f} ms p95 {np.percentile(r[:, 2], 95):.1f} ms; '
              f'image age p50 {np.percentile(r[:, 3], 50):.0f} ms p95 {np.percentile(r[:, 3], 95):.0f} ms')
        print('log written to', self.a.csv)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--duration', type=float, default=120.0, help='wall-clock seconds')
    ap.add_argument('--csv', default=os.path.expanduser('~/labs/week11/data/line_follow.csv'))
    a, ros_args = ap.parse_known_args()
    rclpy.init(args=ros_args, signal_handler_options=SignalHandlerOptions.NO)  # keep ROS alive on Ctrl+C
    node = LineFollower(a)
    try:
        rclpy.spin(node)
    except (SystemExit, KeyboardInterrupt):
        pass
    node.summary()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
