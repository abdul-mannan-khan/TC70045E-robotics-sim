#!/usr/bin/env python3
"""grab_frames.py - save simulated camera frames to disk for offline tests and benchmarks (Week 11).

Usage (simulator running with the camera on):
  python3 ~/labs/week11/scripts/grab_frames.py --n 40 --out ~/labs/week11/data/frames
  python3 ~/labs/week11/scripts/grab_frames.py --n 40 --spin 0.3     # turn slowly while grabbing (varied views)

Saves frame_000.png ... as BGR PNG files and prints one line per saved frame.
With --spin the robot turns at that rate [rad/s] and a zero Twist is sent at the end.
"""
import argparse
import os

import cv2
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import Image


class Grabber(Node):
    def __init__(self, a):
        super().__init__('grab_frames')
        self.a, self.i, self.bridge = a, 0, CvBridge()
        os.makedirs(a.out, exist_ok=True)
        self.cmd = self.create_publisher(Twist, '/cmd_vel', 1)
        self.create_subscription(Image, '/camera/color/image_raw', self.on_image, 5)

    def on_image(self, msg):
        if self.a.spin:
            t = Twist()
            t.angular.z = self.a.spin
            self.cmd.publish(t)
        path = os.path.join(self.a.out, 'frame_%03d.png' % self.i)
        cv2.imwrite(path, self.bridge.imgmsg_to_cv2(msg, 'bgr8'))
        print('saved', path, flush=True)
        self.i += 1
        if self.i >= self.a.n:
            self.cmd.publish(Twist())  # stop: the simulated base has no command timeout
            raise SystemExit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=40)
    ap.add_argument('--out', default=os.path.expanduser('~/labs/week11/data/frames'))
    ap.add_argument('--spin', type=float, default=0.0)
    a = ap.parse_args()
    a.out = os.path.expanduser(a.out)
    rclpy.init()
    node = Grabber(a)
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
