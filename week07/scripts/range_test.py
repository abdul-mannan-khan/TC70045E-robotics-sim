"""Depth-accuracy benchmark in the range world: bias, sigma and fill rate of the depth camera at known ranges.

What it does, for each requested range Z (camera optical centre to the target wall):
  1. drives the robot (move_to.py) so that the camera is Z metres from the wall face (x = 6.95 m);
  2. waits until the robot has stopped, then takes FRAMES depth images from /camera/aligned_depth_to_color/image_raw;
  3. in each image, takes a patch of the wall ABOVE the image centre (rows ROW0..ROW1) - below row ~249 you see the
     floor at long range - and records the mean, the standard deviation and the fill rate (valid pixels / all pixels);
  4. the reference ("tape") is Z_true = 6.95 - (x_robot + 0.14) from /ground_truth/odom.
One line per frame goes to the CSV file; a summary line per range is printed. Fit k with depth_fit.py afterwards.

Usage (simulator started with world:=range x:=0 y:=0):
    python3 ~/labs/week07/scripts/range_test.py                          # ranges 1 2 3 4 6 m, 20 frames each
    python3 ~/labs/week07/scripts/range_test.py --ranges 0.4 0.6 --frames 10 --out minz.csv
Expected output (simulated D455 model, one line per range, about 4 minutes in total):
    Z_true 2.000 m  mean 2000.1 mm  bias   0.1 mm  sigma   7.6 mm  fill 0.975  (20 frames)
"""
import argparse
import csv
import warnings

import numpy as np
import rclpy
from sensor_msgs.msg import Image

from move_to import Mover

WALL_X = 6.95                 # m, face of the target wall in the range world
CAM_X = 0.14                  # m, camera optical centre ahead of base_footprint
ROW0, ROW1 = 216, 236         # patch rows (above the centre row 240: always on the wall)
COL0, COL1 = 414, 435         # patch columns (around the centre column 424)
TOPIC = '/camera/aligned_depth_to_color/image_raw'
warnings.filterwarnings('ignore', 'Mean of empty slice')   # inside MinZ every pixel is 0


def patch_stats(msg):
    """Mean and standard deviation (mm) of the valid pixels in the patch, and the fill rate."""
    z = np.frombuffer(msg.data, dtype=np.uint16).reshape(msg.height, msg.width)
    p = z[ROW0:ROW1, COL0:COL1].astype(np.float64)
    good = p[p > 0]                                    # 0 means "no depth" in a 16UC1 depth image
    fill = good.size / p.size
    if good.size < 2:
        return float('nan'), float('nan'), fill
    return good.mean(), good.std(ddof=1), fill


def collect(node, n_frames):
    """Take n_frames depth images stamped at least 0.5 s after the robot stopped."""
    t_stop = node.get_clock().now().nanoseconds * 1e-9 + 0.5
    frames = []

    def cb(msg):
        if msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9 > t_stop:
            frames.append(patch_stats(msg))
    sub = node.create_subscription(Image, TOPIC, cb, 5)
    while rclpy.ok() and len(frames) < n_frames:
        node.ex.spin_once(timeout_sec=0.1)
    node.destroy_subscription(sub)
    return frames[:n_frames]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ranges', type=float, nargs='+', default=[1.0, 2.0, 3.0, 4.0, 6.0])
    ap.add_argument('--frames', type=int, default=20)
    ap.add_argument('--out', default='range_test.csv')
    a = ap.parse_args()
    rclpy.init()
    node = Mover()                                     # the drive-to-pose node from move_to.py
    with open(a.out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['z_true_m', 'frame', 'mean_mm', 'sigma_mm', 'fill'])
        for z in a.ranges:
            node.go(WALL_X - CAM_X - z, 0.0)
            x = node.pose[0]
            z_true = WALL_X - (x + CAM_X)
            rows = collect(node, a.frames)
            for i, (m, s, fl) in enumerate(rows):
                w.writerow(['%.4f' % z_true, i, '%.2f' % m, '%.3f' % s, '%.4f' % fl])
            m, s, fl = (np.nanmean([r[k] for r in rows]) for k in range(3))
            print('Z_true %.3f m  mean %7.1f mm  bias %5.1f mm  sigma %5.1f mm  fill %.3f  (%d frames)'
                  % (z_true, m, m - 1000 * z_true, s, fl, len(rows)), flush=True)
    node.go(0.0, 0.0)                                  # back to the start, and stop
    print('saved', a.out)
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
