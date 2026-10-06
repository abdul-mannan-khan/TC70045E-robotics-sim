#!/usr/bin/env python3
"""staleness_demo.py - measure how queue depth turns into data age when a consumer is too slow.

TC70045E Week 5, Laboratory A. One process, two nodes: a publisher at --rate Hz (like the IMU) that
stamps every message with the host clock, and a subscriber whose callback takes --work-ms to run
(a slow estimator). Both use RELIABLE, KEEP_LAST(--depth). The subscriber prints the age of the samples
it is handed (now - stamp). Theory: once the queue is full the age settles near depth / rate.
No simulator needed.

Usage:
  python3 ~/labs/week05/scripts/staleness_demo.py --depth 1
  python3 ~/labs/week05/scripts/staleness_demo.py --depth 10
  python3 ~/labs/week05/scripts/staleness_demo.py --depth 100 --seconds 12
Expected (100 Hz, 15 ms of work, measured in the module container): median age 0.006 s at depth 1,
0.096 s at depth 10, 1.007 s at depth 100 - and 40-46 % of the samples are never processed at any depth.
"""
import argparse
import statistics
import threading
import time

import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import Header


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rate', type=float, default=100.0)
    ap.add_argument('--depth', type=int, default=10)
    ap.add_argument('--work-ms', type=float, default=15.0)
    ap.add_argument('--seconds', type=float, default=8.0)
    a = ap.parse_args()

    rclpy.init()
    qos = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=a.depth)
    pub_node = rclpy.create_node('fast_sensor')
    sub_node = rclpy.create_node('slow_estimator')
    pub = pub_node.create_publisher(Header, 'staleness_demo', qos)
    sent, ages = [0], []

    def publish():
        h = Header()
        t = time.time()
        h.stamp.sec, h.stamp.nanosec = int(t), int((t % 1) * 1e9)
        pub.publish(h)
        sent[0] += 1

    def consume(h):
        ages.append(time.time() - (h.stamp.sec + h.stamp.nanosec * 1e-9))
        time.sleep(a.work_ms / 1000.0)            # the "estimator" is busy

    pub_node.create_timer(1.0 / a.rate, publish)
    sub_node.create_subscription(Header, 'staleness_demo', consume, qos)
    ex = MultiThreadedExecutor(num_threads=2)
    ex.add_node(pub_node)
    ex.add_node(sub_node)
    threading.Thread(target=ex.spin, daemon=True).start()
    time.sleep(a.seconds)

    half = ages[len(ages) // 2:]                  # steady state only
    print('rate %.0f Hz, depth %d, work %.0f ms/sample -> consumer capacity %.0f Hz'
          % (a.rate, a.depth, a.work_ms, 1000.0 / a.work_ms))
    print('sent %d, processed %d (%.0f %% dropped by KEEP_LAST)'
          % (sent[0], len(ages), 100.0 * (1 - len(ages) / max(sent[0], 1))))
    print('age of processed samples (steady state): median %.3f s, max %.3f s;  depth/rate = %.3f s'
          % (statistics.median(half), max(half), a.depth / a.rate))
    ex.shutdown()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
