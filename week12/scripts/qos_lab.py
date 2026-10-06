#!/usr/bin/env python3
"""qos_lab.py - what reliability and queue depth do to the AGE of the data you act on (Week 12, Lab A).

  pub : publishes /qos_lab/image (sensor_msgs/Image, --size bytes) at --rate Hz; frame_id = sequence number
  sub : subscribes with --qos reliable|best_effort and --depth N, spends --work seconds on each message
        (a slow algorithm), prints every 5 s: messages received, sequence gaps (lost or overwritten),
        and the age of the data when processing STARTS (now - header.stamp)
Two terminals:
  python3 ~/labs/week12/scripts/qos_lab.py pub --qos reliable
  python3 ~/labs/week12/scripts/qos_lab.py sub --qos reliable --depth 10 --work 0.1
Try: depth 10 vs depth 1; best_effort vs reliable; pub best_effort + sub reliable (incompatible -> nothing).
Wall-clock time only; no simulator needed.
"""
import argparse
import time

import numpy as np
import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image


def qos(a):
    rel = ReliabilityPolicy.RELIABLE if a.qos == 'reliable' else ReliabilityPolicy.BEST_EFFORT
    return QoSProfile(reliability=rel, history=HistoryPolicy.KEEP_LAST, depth=a.depth)


class Pub(Node):
    def __init__(self, a):
        super().__init__('qos_lab_pub')
        self.pub, self.seq = self.create_publisher(Image, '/qos_lab/image', qos(a)), 0
        self.msg = Image(height=1, width=a.size, encoding='mono8', step=a.size, data=bytes(a.size))
        self.create_timer(1.0 / a.rate, self.tick)

    def tick(self):
        self.msg.header.stamp = self.get_clock().now().to_msg()
        self.msg.header.frame_id = str(self.seq)
        self.pub.publish(self.msg)
        self.seq += 1


class Sub(Node):
    def __init__(self, a):
        super().__init__('qos_lab_sub')
        self.a, self.last, self.gaps, self.ages, self.t = a, None, 0, [], time.monotonic()
        self.create_subscription(Image, '/qos_lab/image', self.on_msg, qos(a))
        self.create_timer(5.0, self.report)
        self.get_logger().info(f'{a.qos} depth {a.depth}, work {a.work * 1e3:.0f} ms per message')

    def on_msg(self, m):
        seq = int(m.header.frame_id)
        if self.last is not None and seq != self.last + 1:
            self.gaps += seq - self.last - 1
        self.last = seq
        self.ages.append((self.get_clock().now() - rclpy.time.Time.from_msg(m.header.stamp)).nanoseconds * 1e-6)
        time.sleep(self.a.work)                      # the "algorithm"

    def report(self):
        if not self.ages:
            print(f'0 msgs in {time.monotonic() - self.t:.1f} s - NO DATA (check the QoS of both ends)', flush=True)
            self.t = time.monotonic()
            return
        a = np.array(self.ages)
        print(f'{len(self.ages)} msgs in {time.monotonic() - self.t:.1f} s, {self.gaps} skipped, '
              f'age p50 {np.median(a):.0f} ms p95 {np.percentile(a, 95):.0f} ms', flush=True)
        self.ages, self.gaps, self.t = [], 0, time.monotonic()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('role', choices=['pub', 'sub'])
    ap.add_argument('--qos', choices=['reliable', 'best_effort'], default='reliable')
    ap.add_argument('--depth', type=int, default=10)
    ap.add_argument('--rate', type=float, default=30.0)
    ap.add_argument('--size', type=int, default=1_000_000)
    ap.add_argument('--work', type=float, default=0.1)
    a = ap.parse_args()
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)   # clean Ctrl+C
    try:
        rclpy.spin(Pub(a) if a.role == 'pub' else Sub(a))
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
