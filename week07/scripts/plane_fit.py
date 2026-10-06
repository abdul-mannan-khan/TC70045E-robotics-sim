"""Fit a plane to a region of the depth image: target tilt, noise about the plane, and fill rate.

A patch standard deviation mixes two things on a tilted target: sensor noise and the real change of depth across
the patch. Deprojecting the pixels to 3-D points and fitting a plane separates them:
  X = (u - cx) Z / fx,  Y = (v - cy) Z / fy   ->  least-squares plane (SVD)  ->  normal n, RMS residual.
The tilt is the angle between the plane normal and the optical axis (0 deg = target facing the camera).

Usage (range world; drive in front of a target first, e.g. move_to.py 0.0 3.3 for the 30 degree target):
    python3 ~/labs/week07/scripts/plane_fit.py                 # 10 frames, default region of interest
    python3 ~/labs/week07/scripts/plane_fit.py --frames 20 --roi 150 230 380 470
Expected output (30 degree target, camera 1.33 m away):
    tilt 30.0 deg   Z 1.334 m   plane RMS  3.4 mm   naive patch sigma 105.0 mm   fill 0.98   (10 frames)
"""
import argparse

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import Image, CameraInfo

ap = argparse.ArgumentParser()
ap.add_argument('--frames', type=int, default=10)
ap.add_argument('--roi', type=int, nargs=4, default=[150, 230, 380, 470], metavar=('ROW0', 'ROW1', 'COL0', 'COL1'))
a = ap.parse_args()
R0, R1, C0, C1 = a.roi


def fit(z_mm, K):
    """Return tilt (deg), mean Z (m), plane RMS (mm), naive sigma (mm), fill for the region of interest."""
    fx, cx, fy, cy = K[0], K[2], K[4], K[5]
    v, u = np.mgrid[R0:R1, C0:C1]
    z = z_mm[R0:R1, C0:C1].astype(np.float64) / 1000.0
    ok = z > 0
    Z = z[ok]
    P = np.column_stack(((u[ok] - cx) * Z / fx, (v[ok] - cy) * Z / fy, Z))     # N x 3 points, metres
    c = P.mean(axis=0)
    _, _, vt = np.linalg.svd(P - c, full_matrices=False)
    n = vt[2]                                                                   # normal = smallest singular vector
    resid = (P - c) @ n
    tilt = np.degrees(np.arccos(abs(n[2])))
    return tilt, Z.mean(), 1000 * resid.std(), 1000 * Z.std(ddof=1), ok.mean()


class PlaneFit(Node):
    def __init__(self):
        super().__init__('plane_fit', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.K, self.rows = None, []
        self.create_subscription(CameraInfo, '/camera/aligned_depth_to_color/camera_info', self.on_info, 5)
        self.create_subscription(Image, '/camera/aligned_depth_to_color/image_raw', self.on_depth, 5)

    def on_info(self, m):
        self.K = m.k

    def on_depth(self, m):
        if self.K is None:
            return
        z = np.frombuffer(m.data, dtype=np.uint16).reshape(m.height, m.width)
        self.rows.append(fit(z, self.K))
        print('tilt %5.1f deg   Z %.3f m   plane RMS %5.1f mm   naive patch sigma %6.1f mm   fill %.2f'
              % self.rows[-1], flush=True)


def main():
    rclpy.init()
    node = PlaneFit()
    while rclpy.ok() and len(node.rows) < a.frames:
        rclpy.spin_once(node, timeout_sec=0.1)
    t, z, r, s, f = np.mean(node.rows, axis=0)
    print('MEAN: tilt %.1f deg   Z %.3f m   plane RMS %.1f mm   naive patch sigma %.1f mm   fill %.2f   (%d frames)'
          % (t, z, r, s, f, len(node.rows)))
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
