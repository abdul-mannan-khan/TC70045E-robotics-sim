#!/usr/bin/env python3
"""bag_jitter.py - inter-sample interval statistics and histogram of one topic in a rosbag2 bag.

TC70045E Week 5, Laboratory C. Reads the bag with rosbag2_py (MCAP or SQLite3), and compares two clocks:
  stamp   - header.stamp written by the publisher (simulated time in the simulator)
  receive - the time the recorder received the message (the bag's own timestamp)
Prints mean rate, interval standard deviation (jitter), 99th percentile and maximum for both, and saves a
histogram PNG next to the bag - a much better report figure than a single mean.

Usage:   python3 ~/labs/week05/scripts/bag_jitter.py ~/bags/w5_run1 --topic /imu/data_raw
Expected (simulator, bag recorded with --use-sim-time, measured in the module container): /imu/data_raw
100.00 Hz with jitter 0.000 ms on both clocks - the recorder's clock is simulated time too, so host-side
jitter does not appear in the bag. On a busier host Gazebo can skip updates (tail to 20+ ms).
"""
import argparse
import os
import warnings

import numpy as np
import yaml
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

warnings.filterwarnings('ignore', message='Unable to import Axes3D')
import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402


def read_topic(bag, topic):
    meta = yaml.safe_load(open(os.path.join(bag, 'metadata.yaml')))['rosbag2_bagfile_information']
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=bag, storage_id=meta['storage_identifier']),
                rosbag2_py.ConverterOptions('cdr', 'cdr'))
    types = {t.name: t.type for t in reader.get_all_topics_and_types()}
    reader.set_filter(rosbag2_py.StorageFilter(topics=[topic]))
    msg_type = get_message(types[topic])
    stamp, recv = [], []
    while reader.has_next():
        _, data, t = reader.read_next()
        m = deserialize_message(data, msg_type)
        stamp.append(m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)
        recv.append(t * 1e-9)
    return np.array(stamp), np.array(recv)


def stats(name, t):
    d = np.diff(t) * 1e3                                   # ms
    print('%-8s n=%5d  rate %7.2f Hz  mean %6.2f ms  jitter(sd) %6.3f ms  p99 %6.2f ms  max %7.2f ms'
          % (name, len(t), 1e3 / d.mean(), d.mean(), d.std(), np.percentile(d, 99), d.max()))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bag')
    ap.add_argument('--topic', default='/imu/data_raw')
    a = ap.parse_args()
    stamp, recv = read_topic(a.bag, a.topic)
    d_s, d_r = stats('stamp', stamp), stats('receive', recv)
    plt.figure(figsize=(7, 3.5))
    bins = np.linspace(0, max(np.percentile(d_r, 99.5), np.percentile(d_s, 99.5)) * 1.2, 80)
    plt.hist(d_r, bins=bins, alpha=0.6, label='receive (recorder clock)')
    plt.hist(d_s, bins=bins, alpha=0.6, label='header stamp (sensor clock)')
    plt.yscale('log')
    plt.xlabel('inter-sample interval [ms]')
    plt.ylabel('count')
    plt.title('%s  (%d samples)' % (a.topic, len(stamp)))
    plt.legend()
    plt.tight_layout()
    out = os.path.join(a.bag, 'jitter_%s.png' % a.topic.strip('/').replace('/', '_'))
    plt.savefig(out, dpi=150)
    print('histogram saved to', out)


if __name__ == '__main__':
    main()
