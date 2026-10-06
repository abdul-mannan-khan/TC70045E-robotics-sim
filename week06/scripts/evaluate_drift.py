#!/usr/bin/env python3
"""evaluate_drift.py - score pose estimates in a rosbag2 bag against the simulator's ground truth.

TC70045E Week 6. For every estimate topic it prints the final position error e, e as a % of the true path
length L, the final heading error, and two calibration ratios:
  distance ratio = true distance / estimated distance     (-> wheel-radius correction)
  rotation ratio = true net rotation / estimated net rotation   (-> effective lx+ly correction)
Everything is expressed relative to the pose at the start of the bag, so the spawn offset of
/ground_truth/odom (world frame) cancels. nav_msgs/Odometry topics are scored on position and heading,
sensor_msgs/Imu topics (e.g. Madgwick output) on heading only.

Usage:
  python3 ~/labs/week06/scripts/evaluate_drift.py ~/bags/w6_square_1 --est /odom_raw /odom
  python3 ~/labs/week06/scripts/evaluate_drift.py ~/bags/w6_beta --est /imu/data_b0p01 /imu/data_b0p3 --absolute
  add --plot to save xy.png (and heading.png) into the bag folder
Expected (measured, uncalibrated /odom_raw, 2 m square, cw): e = 0.36 m, e/L ~4.5 %, heading error ~ -14 to -16 deg,
distance ratio ~1.010, rotation ratio ~0.96; straight 2 m: distance ratio ~1.010; spin 720 deg: rotation ratio ~0.972.
"""
import argparse
import math
import os
import warnings

import numpy as np
import yaml
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def read(bag, topics):
    meta = yaml.safe_load(open(os.path.join(bag, 'metadata.yaml')))['rosbag2_bagfile_information']
    r = rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=bag, storage_id=meta['storage_identifier']),
           rosbag2_py.ConverterOptions('cdr', 'cdr'))
    types = {t.name: t.type for t in r.get_all_topics_and_types()}
    missing = [t for t in topics if t not in types]
    if missing:
        raise SystemExit('not in the bag: %s  (the bag has: %s)' % (missing, sorted(types)))
    r.set_filter(rosbag2_py.StorageFilter(topics=topics))
    out = {t: [] for t in topics}
    while r.has_next():
        topic, data, _ = r.read_next()
        m = deserialize_message(data, get_message(types[topic]))
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        pose = m.pose.pose if hasattr(m, 'pose') else None
        if pose is not None:
            out[topic].append((t, pose.position.x, pose.position.y, yaw_of(pose.orientation)))
        else:
            out[topic].append((t, math.nan, math.nan, yaw_of(m.orientation)))
    return {k: np.array(v) for k, v in out.items()}, types


def relative(a):
    """Express a (t, x, y, yaw) track relative to its first pose; yaw is unwrapped."""
    t, x, y, th = a.T
    th = np.unwrap(th)
    c, s = math.cos(th[0]), math.sin(th[0])
    dx, dy = x - x[0], y - y[0]
    return np.column_stack([t, c * dx + s * dy, -s * dx + c * dy, th - th[0]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bag')
    ap.add_argument('--truth', default='/ground_truth/odom')
    ap.add_argument('--est', nargs='+', default=['/odom_raw'])
    ap.add_argument('--absolute', action='store_true', help='compare absolute yaw (magnetometer runs)')
    ap.add_argument('--plot', action='store_true')
    a = ap.parse_args()

    data, types = read(a.bag, [a.truth] + a.est)
    gt = data[a.truth]
    t0 = max(d[0, 0] for d in data.values())                 # common start (all topics present)
    gt = gt[gt[:, 0] >= t0]
    g = relative(gt)
    L = float(np.sum(np.hypot(np.diff(g[:, 1]), np.diff(g[:, 2]))))
    g_rot = float(g[-1, 3] - g[0, 3])                       # net rotation (unwrapped), rad
    print('bag %s   truth %s: path length L = %.3f m, total rotation = %.1f deg, duration %.1f s'
          % (os.path.basename(a.bag.rstrip('/')), a.truth, L, math.degrees(g_rot), g[-1, 0] - g[0, 0]))
    rot_ok = abs(g_rot) > math.radians(30)                   # a ratio needs a real rotation
    print('%-22s %9s %8s %10s %10s %9s %9s' % ('estimate', 'e [m]', 'e/L [%]', 'dpsi [deg]',
                                              'max e [m]', 'dist.rat', 'rot.rat'))
    rows = {}
    for topic in a.est:
        d = data[topic]
        d = d[d[:, 0] >= t0]
        is_imu = types[topic] == 'sensor_msgs/msg/Imu'
        r = relative(d)
        ts = r[:, 0]
        gx, gy = np.interp(ts, g[:, 0], g[:, 1]), np.interp(ts, g[:, 0], g[:, 2])
        gth = np.interp(ts, g[:, 0], g[:, 3])
        if a.absolute:                                     # absolute yaw (e.g. magnetometer-aided)
            gth = gth + np.unwrap(gt[:, 3])[0]
            r[:, 3] = np.unwrap(d[:, 3])
        dpsi = np.degrees(np.arctan2(np.sin(r[:, 3] - gth), np.cos(r[:, 3] - gth)))
        rot_ratio = g_rot / (r[-1, 3] - r[0, 3]) if rot_ok else math.nan
        if is_imu:
            print('%-22s %9s %8s %+10.2f %10s %9s %9.4f   (heading only; RMS %.2f deg)'
                  % (topic, '-', '-', dpsi[-1], '-', '-', rot_ratio, float(np.sqrt(np.mean(dpsi ** 2)))))
        else:
            err = np.hypot(r[:, 1] - gx, r[:, 2] - gy)
            dist = float(np.sum(np.hypot(np.diff(r[:, 1]), np.diff(r[:, 2]))))
            print('%-22s %9.3f %8.2f %+10.2f %10.3f %9.4f %9.4f'
                  % (topic, err[-1], 100 * err[-1] / L, dpsi[-1], err.max(), L / dist, rot_ratio))
        rows[topic] = (r, gth)
    if a.plot:
        plot(a, g, rows, types)


def plot(a, g, rows, types):
    warnings.filterwarnings('ignore', message='Unable to import Axes3D')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.figure(figsize=(5.5, 5))
    plt.plot(g[:, 1], g[:, 2], 'k-', lw=2, label='ground truth')
    for topic, (r, _) in rows.items():
        if types[topic] != 'sensor_msgs/msg/Imu':
            plt.plot(r[:, 1], r[:, 2], label=topic)
    plt.axis('equal')
    plt.xlabel('x from start [m]')
    plt.ylabel('y from start [m]')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(a.bag, 'xy.png'), dpi=150)
    plt.figure(figsize=(7, 3.5))
    for topic, (r, gth) in rows.items():
        plt.plot(r[:, 0] - g[0, 0], np.degrees(np.arctan2(np.sin(r[:, 3] - gth), np.cos(r[:, 3] - gth))),
                 label=topic)
    plt.xlabel('time [s]')
    plt.ylabel('heading error [deg]')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(a.bag, 'heading.png'), dpi=150)
    print('plots saved to', os.path.join(a.bag, 'xy.png'), 'and heading.png')


if __name__ == '__main__':
    main()
