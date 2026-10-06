#!/usr/bin/env python3
"""Sensor inventory of a running ROS 2 graph: topic, type, rate, jitter, frame and message age.

Purpose  Week 1, Laboratory A. `ros2 topic hz` measures one topic at a time; this node listens to every
         sensor topic at once for the same window, so the rows of your inventory table are comparable.
Usage    (simulator running first:  ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false)
           python3 ~/labs/week01/scripts/topic_audit.py                 # default sensor topics, 10 s
           python3 ~/labs/week01/scripts/topic_audit.py --seconds 20 /scan /imu/data_raw
Output   one row per topic: message type, mean rate [Hz] against the wall clock and against simulated time
         (they differ when Gazebo runs slower than real time), interval standard deviation [ms, wall clock],
         header.frame_id, and the mean age of header.stamp against the simulated clock [ms].
         Typical result on the lab robot: /scan 5.5 Hz, laser_link; /imu/data_raw ~100 Hz, imu_link; ...
"""
import argparse
import time

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from rosidl_runtime_py.utilities import get_message

DEFAULT = ['/scan', '/imu/data_raw', '/imu/mag', '/wheel_speeds', '/vel_raw', '/odom_raw',
           '/ground_truth/odom', '/battery', '/voltage', '/power/current']


class Audit(Node):
    def __init__(self, topics):
        super().__init__('topic_audit', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.topics, self.rx = topics, {t: [] for t in topics}     # t -> [(wall, sim, frame, age)]
        self.types, self.subs = {}, []

    def connect(self):
        """Look up each topic's type in the graph and subscribe (best effort: accepts any publisher)."""
        known = dict(self.get_topic_names_and_types())
        for t in self.topics:
            if t in known and t not in self.types:
                self.types[t] = known[t][0]
                cb = (lambda msg, t=t: self.on_msg(t, msg))
                self.subs.append(self.create_subscription(get_message(known[t][0]), t, cb,
                                                          qos_profile_sensor_data))

    def on_msg(self, topic, msg):
        frame, age = '-', float('nan')
        now = self.get_clock().now().nanoseconds
        if now == 0:
            return                              # /clock not received yet: sim time is still 0
        if hasattr(msg, 'header'):
            frame = msg.header.frame_id or "''"
            stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            age = (now * 1e-9 - stamp) * 1e3
        self.rx[topic].append((time.monotonic(), now * 1e-9, frame, age))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('topics', nargs='*', default=DEFAULT)
    ap.add_argument('--seconds', type=float, default=10.0)
    a = ap.parse_args()
    rclpy.init()
    node = Audit(a.topics)
    t_end = time.monotonic() + a.seconds + 2.0          # 2 s for discovery
    while time.monotonic() < t_end:
        node.connect()
        rclpy.spin_once(node, timeout_sec=0.05)
    print('%-18s %-15s %7s %7s %6s %-15s %7s' % ('topic', 'type', 'Hz wall', 'Hz sim', 'sd ms', 'frame_id', 'age ms'))
    for t in a.topics:
        r = node.rx[t]
        if len(r) < 3:
            print('%-18s %-15s   (fewer than 3 messages - is it published?)' % (t, node.types.get(t, '?')))
            continue
        dt = np.diff([x[0] for x in r])                  # wall-clock intervals
        span = r[-1][1] - r[0][1]                        # simulated time spanned
        age = np.mean([x[3] for x in r])                 # nan for messages without a header
        print('%-18s %-15s %7.2f %7.2f %6.1f %-15s %7.1f' % (t, node.types[t].split('/')[-1], 1.0 / dt.mean(),
              (len(r) - 1) / span if span > 0 else float('nan'), dt.std() * 1e3, r[-1][2], age))
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
