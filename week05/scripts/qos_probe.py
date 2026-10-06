#!/usr/bin/env python3
"""qos_probe.py - subscribe to a topic with a QoS profile YOU choose and report whether it matches.

TC70045E Week 5, Laboratory A. It counts the messages received in a fixed time and prints every
"incompatible QoS" event, i.e. the diagnosis that `ros2 topic echo` only hints at.

Usage:
  python3 ~/labs/week05/scripts/qos_probe.py /imu/data_raw sensor_msgs/msg/Imu --reliability best_effort
  python3 ~/labs/week05/scripts/qos_probe.py /imu/data_raw sensor_msgs/msg/Imu --durability transient_local
  python3 ~/labs/week05/scripts/qos_probe.py /imu/data_raw sensor_msgs/msg/Imu --deadline-ms 20
  python3 ~/labs/week05/scripts/qos_probe.py /tf_static tf2_msgs/msg/TFMessage --durability volatile
Options: --reliability reliable|best_effort  --durability volatile|transient_local  --depth N
         --deadline-ms T (0 = none)  --seconds S (default 5)
Expected: a compatible profile prints "received ~500 messages in 5.0 s (100.0 Hz)"; an incompatible one
prints "INCOMPATIBLE QoS: policy DURABILITY ..." and "received 0 messages".
"""
import argparse
import importlib
import time

import rclpy
from rclpy.duration import Duration
try:                                       # Humble name; Iron and later: rclpy.event_handler
    from rclpy.qos_event import SubscriptionEventCallbacks
except ImportError:
    from rclpy.event_handler import SubscriptionEventCallbacks
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy


def load_type(name):                       # 'sensor_msgs/msg/Imu' -> class
    pkg, _, cls = name.split('/')
    return getattr(importlib.import_module(pkg + '.msg'), cls)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('topic')
    ap.add_argument('type')
    ap.add_argument('--reliability', default='reliable', choices=['reliable', 'best_effort'])
    ap.add_argument('--durability', default='volatile', choices=['volatile', 'transient_local'])
    ap.add_argument('--depth', type=int, default=10)
    ap.add_argument('--deadline-ms', type=float, default=0.0)
    ap.add_argument('--seconds', type=float, default=5.0)
    a = ap.parse_args()

    qos = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=a.depth,
                     reliability=ReliabilityPolicy[a.reliability.upper()],
                     durability=DurabilityPolicy[a.durability.upper()])
    if a.deadline_ms > 0:
        qos.deadline = Duration(nanoseconds=int(a.deadline_ms * 1e6))

    rclpy.init()
    node = rclpy.create_node('qos_probe')
    count = [0]
    missed = [0]

    def on_incompatible(ev):
        print('INCOMPATIBLE QoS: policy %s, %d incompatible publisher(s)'
              % (str(getattr(ev.last_policy_kind, 'name', ev.last_policy_kind)).replace('RMW_QOS_POLICY_', ''),
                 ev.total_count))

    def on_deadline(ev):
        missed[0] = ev.total_count

    events = SubscriptionEventCallbacks(incompatible_qos=on_incompatible,
                                        deadline=on_deadline if a.deadline_ms > 0 else None)
    node.create_subscription(load_type(a.type), a.topic, lambda m: count.__setitem__(0, count[0] + 1),
                             qos, event_callbacks=events)
    print('requesting %s: %s, %s, depth %d, deadline %s'
          % (a.topic, a.reliability, a.durability, a.depth,
             '%.0f ms' % a.deadline_ms if a.deadline_ms > 0 else 'none'))
    t_end = time.monotonic() + a.seconds
    while time.monotonic() < t_end:
        rclpy.spin_once(node, timeout_sec=0.05)
    print('received %d messages in %.1f s (%.1f Hz)' % (count[0], a.seconds, count[0] / a.seconds))
    if a.deadline_ms > 0:
        print('deadline missed %d times' % missed[0])
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
