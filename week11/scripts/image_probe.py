#!/usr/bin/env python3
"""image_probe.py - measure an image topic the way a vision node sees it (Week 11, Lab A).

Subscribes with a QoS you choose, converts every frame with cv_bridge and reports:
encoding, size, rate, bandwidth and the age of each frame (now - header.stamp, simulated time).

Usage (simulator running with the camera on):
  python3 ~/labs/week11/scripts/image_probe.py                                  # colour, RELIABLE, 60 frames
  python3 ~/labs/week11/scripts/image_probe.py --qos best_effort
  python3 ~/labs/week11/scripts/image_probe.py --topic /camera/aligned_depth_to_color/image_raw

Expected output (software rendering, ~7 Hz):
  encoding=rgb8 848x480 ... rate 6.9 Hz, 8.4 MB/s, age p50 ... ms p95 ... ms
For a depth topic it also prints the centre pixel in metres (16UC1 millimetres x 0.001).
"""
import argparse
import time

import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image


class Probe(Node):
    def __init__(self, a):
        super().__init__('image_probe', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', value=True)])
        rel = ReliabilityPolicy.RELIABLE if a.qos == 'reliable' else ReliabilityPolicy.BEST_EFFORT
        qos = QoSProfile(reliability=rel, history=HistoryPolicy.KEEP_LAST, depth=a.depth)
        self.bridge, self.n, self.ages, self.bytes, self.t = CvBridge(), a.n, [], 0, []
        self.create_subscription(Image, a.topic, self.on_image, qos)
        self.get_logger().info(f'{a.topic} with {a.qos.upper()} depth {a.depth}')

    def on_image(self, msg):
        stamp = rclpy.time.Time.from_msg(msg.header.stamp)
        self.ages.append((self.get_clock().now() - stamp).nanoseconds * 1e-6)
        self.t.append(time.monotonic())
        self.bytes += len(msg.data)
        img = self.bridge.imgmsg_to_cv2(msg, 'passthrough' if msg.encoding == '16UC1' else 'bgr8')
        if len(self.t) == 1:
            print(f'encoding={msg.encoding} {msg.width}x{msg.height} step={msg.step} '
                  f'frame_id={msg.header.frame_id} -> numpy {img.dtype} {img.shape}')
            if msg.encoding == '16UC1':
                c = img[msg.height // 2, msg.width // 2]
                print(f'centre pixel raw={c} -> {c * 0.001:.3f} m (0 = no data)')
        if len(self.t) >= self.n:
            dt = self.t[-1] - self.t[0]
            a = np.array(self.ages)
            print(f'{len(self.t)} frames: rate {(len(self.t) - 1) / dt:.2f} Hz (wall clock), '
                  f'{self.bytes / dt / 1e6:.1f} MB/s, age p50 {np.percentile(a, 50):.1f} ms '
                  f'p95 {np.percentile(a, 95):.1f} ms (simulated time)')
            raise SystemExit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--topic', default='/camera/color/image_raw')
    ap.add_argument('--qos', choices=['reliable', 'best_effort'], default='reliable')
    ap.add_argument('--depth', type=int, default=5)
    ap.add_argument('--n', type=int, default=60)
    a = ap.parse_args()
    rclpy.init()
    node = Probe(a)
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
