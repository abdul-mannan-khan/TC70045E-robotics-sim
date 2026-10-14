#!/usr/bin/env python3
"""clock_skew_demo.py - what a clock offset does to TF lookups across robots (Week 12, Lab A).

Takes each scan from --topic, pretends it was stamped by a machine whose clock is --offset seconds
ahead (+) or behind (-), and asks TF for the laser pose in the shared --target frame AT THAT STAMP,
exactly as rviz2, a costmap or a map merger would.  --wall-clock re-stamps with this node's wall clock
instead: the classic "one node forgot use_sim_time" fault.
Like a tf2 message filter or a costmap, it waits up to --tolerance (0.2 s) for the transform to arrive.
Needs a common frame: publish world -> robot1/odom and world -> robot2/odom first (see the lecture).
Usage:
  python3 ~/labs/week12/scripts/clock_skew_demo.py --offset 0.0
  python3 ~/labs/week12/scripts/clock_skew_demo.py --offset 0.2       # 200 ms ahead
  python3 ~/labs/week12/scripts/clock_skew_demo.py --wall-clock
Prints every 5 s: lookups OK / failed, and the first TF error text.
"""
import argparse
import time

import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.executors import ExternalShutdownException
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformException, TransformListener


class SkewDemo(Node):
    def __init__(self, a):
        super().__init__('clock_skew_demo', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', value=not a.wall_clock)])
        self.a, self.ok, self.fail, self.err, self.pending = a, 0, 0, '', []
        self.buf, self.t_start = Buffer(), time.monotonic()
        self.tl = TransformListener(self.buf, self)
        self.create_subscription(LaserScan, a.topic, self.on_scan, qos_profile_sensor_data)
        self.create_timer(0.02, self.process)
        self.create_timer(5.0, self.report)

    def on_scan(self, m):
        if self.a.wall_clock:
            stamp = self.get_clock().now()                       # wall time, while TF runs on /clock
        else:
            stamp = rclpy.time.Time.from_msg(m.header.stamp) + Duration(nanoseconds=int(self.a.offset * 1e9))
        self.pending.append((stamp, m.header.frame_id, time.monotonic()))

    def process(self):
        """Like a tf2 message filter or a costmap: wait up to --tolerance for TF to catch up, then give up."""
        keep = []
        warm = time.monotonic() - self.t_start < 3.0          # TF buffer still filling after start-up
        for stamp, frame, t_in in self.pending:
            try:
                self.buf.lookup_transform(self.a.target, frame, stamp)
                self.ok += 1
            except TransformException as e:
                if time.monotonic() - t_in < self.a.tolerance:
                    keep.append((stamp, frame, t_in))
                else:
                    if not warm:
                        self.fail += 1
                        self.err = self.err or str(e).split(chr(10))[0][:160]
        self.pending = keep

    def report(self):
        print(f'offset {self.a.offset:+.3f} s{" (wall clock)" if self.a.wall_clock else ""}: '
              f'{self.ok} OK, {self.fail} failed  {self.err}', flush=True)
        self.ok, self.fail, self.err = 0, 0, ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--topic', default='/robot2/scan')
    ap.add_argument('--target', default='world')
    ap.add_argument('--offset', type=float, default=0.0)
    ap.add_argument('--wall-clock', action='store_true')
    ap.add_argument('--tolerance', type=float, default=0.2, help='how long to wait for TF [s], like transform_tolerance')
    a = ap.parse_args()
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)   # clean Ctrl+C
    try:
        rclpy.spin(SkewDemo(a))
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
