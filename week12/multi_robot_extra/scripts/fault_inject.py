#!/usr/bin/env python3
"""fault_inject.py - a pipeline stage with a fault you can switch on (Week 12, Lab B).

Node /robot1/scan_filter: /robot1/scan -> clip ranges beyond 4 m -> /robot1/scan_filtered.
  --fault none      works
  --fault frame     publishes frame_id 'laser' (a frame that does not exist in TF)
  --fault qos       publishes BEST_EFFORT (the consumer asks for RELIABLE -> incompatible, silent)
  --fault simtime   node runs WITHOUT use_sim_time and re-stamps with the wall clock
  --fault stop      the node dies after 15 s
  --fault random    one of the four, chosen secretly; the answer is written to /tmp/fault_answer.txt
Start the consumer (scan_consumer.py) in another terminal and find the fault with the ROS 2 instruments.
Usage:  python3 ~/labs/week12/scripts/fault_inject.py --fault random
"""
import argparse
import random
import sys
import time

import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

FAULTS = ['frame', 'qos', 'simtime', 'stop']


class ScanFilter(Node):
    def __init__(self, fault):
        super().__init__('scan_filter', namespace='robot1', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', value=fault != 'simtime')])
        rel = ReliabilityPolicy.BEST_EFFORT if fault == 'qos' else ReliabilityPolicy.RELIABLE
        self.fault, self.t0 = fault, time.monotonic()
        self.pub = self.create_publisher(LaserScan, 'scan_filtered', QoSProfile(depth=5, reliability=rel))
        self.create_subscription(LaserScan, 'scan', self.on_scan, qos_profile_sensor_data)

    def on_scan(self, m):
        m.ranges = [r if r <= 4.0 else float('inf') for r in m.ranges]
        if self.fault == 'frame':
            m.header.frame_id = 'laser'
        if self.fault == 'simtime':
            m.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(m)
        if self.fault == 'stop' and time.monotonic() - self.t0 > 15.0:
            sys.exit(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fault', choices=['none', 'random'] + FAULTS, default='none')
    a = ap.parse_args()
    fault = random.choice(FAULTS) if a.fault == 'random' else a.fault
    if a.fault == 'random':
        with open('/tmp/fault_answer.txt', 'w') as f:
            f.write(fault + '\n')
        print('a random fault is injected - the answer is in /tmp/fault_answer.txt (do not look)')
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)   # clean Ctrl+C
    try:
        rclpy.spin(ScanFilter(fault))
    except (KeyboardInterrupt, SystemExit, ExternalShutdownException):
        pass
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
