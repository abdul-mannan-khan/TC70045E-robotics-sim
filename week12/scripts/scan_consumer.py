#!/usr/bin/env python3
"""scan_consumer.py - the downstream "algorithm" that shows the symptom (Week 12, Lab B).

Node /obstacle_monitor subscribes /robot1/scan_filtered (RELIABLE, depth 5, simulated time), transforms
each scan's frame into --target at the scan's stamp (as a costmap does) and reports every 2 s:
  messages received, TF lookups OK / failed, nearest obstacle distance - or NO DATA.
It never says WHY - that is your job (ros2 node list / topic info -v / topic hz / tf2_echo / param get).
Usage:  python3 ~/labs/week12/scripts/scan_consumer.py
"""
import argparse
import math
import time

import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformException, TransformListener


class Monitor(Node):
    def __init__(self, a):
        super().__init__('obstacle_monitor', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', value=True)])
        self.a, self.n, self.ok, self.fail, self.near, self.err, self.pending = a, 0, 0, 0, math.inf, '', []
        self.buf, self.t_start = Buffer(), time.monotonic()
        self.tl = TransformListener(self.buf, self)
        self.create_subscription(LaserScan, a.topic, self.on_scan,
                                 QoSProfile(depth=5, reliability=ReliabilityPolicy.RELIABLE))
        self.create_timer(0.02, self.process)
        self.create_timer(2.0, self.report)

    def on_scan(self, m):
        self.n += 1
        self.near = min([r for r in m.ranges if m.range_min < r < m.range_max], default=math.inf)
        self.pending.append((rclpy.time.Time.from_msg(m.header.stamp), m.header.frame_id, time.monotonic()))

    def process(self):
        """Transform each scan once TF has caught up; give up after 0.2 s (a costmap's transform_tolerance)."""
        keep = []
        warm = time.monotonic() - self.t_start < 3.0          # TF buffer still filling after start-up
        for stamp, frame, t_in in self.pending:
            try:
                self.buf.lookup_transform(self.a.target, frame, stamp)
                self.ok += 1
            except TransformException as e:
                if time.monotonic() - t_in < 0.2:
                    keep.append((stamp, frame, t_in))
                else:
                    if not warm:
                        self.fail += 1
                        self.err = self.err or str(e).split(chr(10))[0][:120]
        self.pending = keep

    def report(self):
        if self.n == 0:
            print('NO DATA on', self.a.topic, flush=True)
        else:
            print(f'{self.n} scans, TF OK {self.ok} / failed {self.fail}, nearest {self.near:.2f} m  {self.err}',
                  flush=True)
        self.n, self.ok, self.fail, self.err = 0, 0, 0, ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--topic', default='/robot1/scan_filtered')
    ap.add_argument('--target', default='robot1/odom')
    a = ap.parse_args()
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)   # clean Ctrl+C
    try:
        rclpy.spin(Monitor(a))
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
