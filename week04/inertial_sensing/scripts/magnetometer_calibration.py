#!/usr/bin/env python3
"""Week 4, Lab B - hard- and soft-iron calibration of the magnetometer, and heading error before/after.

Usage:  python3 ~/labs/week04/inertial_sensing/scripts/magnetometer_calibration.py mag_cal.csv [--plot mag_cal.png]
Input:  mag_cal.csv from mag_spin_capture.py (t, mx, my, mz [uT], yaw_true [deg], x, y).

A ground robot only turns about z, so only the horizontal components (mx, my) trace a closed curve; mz stays
almost constant and its hard/soft iron cannot be observed from this data (you would need to tilt the robot).
Three horizontal corrections are compared:
  raw      no correction
  min-max  b = (max + min)/2 (hard iron), g = mean(s)/s with s = (max - min)/2 (diagonal soft iron)
  ellipse  least-squares conic a x^2 + b xy + c y^2 + d x + e y = 1 -> centre and full 2x2 soft-iron matrix
Heading: with REP-103 axes (x forward, y left, z up) and ENU world axes, yaw = atan2(mx, my) when magnetic north
is +y, i.e. the compass heading (clockwise from north) is atan2(my, mx). Error = yaw_mag - yaw_true.
"""
import argparse

import numpy as np
import pandas as pd


def minmax(h):
    b = (h.max(0) + h.min(0)) / 2
    s = (h.max(0) - h.min(0)) / 2
    return b, np.diag(s.mean() / s)


def ellipse(h):
    """Fit a x^2 + b xy + c y^2 + d x + e y = 1; return centre and the matrix W that maps it to a circle."""
    x, y = h[:, 0], h[:, 1]
    A = np.c_[x * x, x * y, y * y, x, y]
    a, b, c, d, e = np.linalg.lstsq(A, np.ones(len(x)), rcond=None)[0]
    Q = np.array([[a, b / 2], [b / 2, c]])
    centre = np.linalg.solve(2 * Q, -np.array([d, e]))
    Q = Q / (1 + centre @ Q @ centre)                  # now (h - centre)^T Q (h - centre) = 1
    val, vec = np.linalg.eigh(Q)
    W = vec @ np.diag(np.sqrt(val)) @ vec.T            # symmetric square root: circle of radius 1
    radius = 1 / np.sqrt(np.sqrt(val).prod())          # keep the geometric-mean radius in uT
    return centre, W * radius


def heading_error(h, yaw_true):
    yaw = np.degrees(np.arctan2(h[:, 0], h[:, 1]))
    return (yaw - yaw_true + 180) % 360 - 180


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv')
    ap.add_argument('--plot', default='')
    a = ap.parse_args()
    d = pd.read_csv(a.csv)
    h, yaw_true = d[['mx', 'my']].to_numpy(), d['yaw_true'].to_numpy()
    print('%d samples, %.0f deg of rotation; mz = %.2f +/- %.2f uT (unobservable)'
          % (len(d), np.abs(np.diff(np.unwrap(np.radians(yaw_true)))).sum() * 57.2958, d.mz.mean(), d.mz.std()))
    b_mm, G = minmax(h)
    c_el, W = ellipse(h)
    print('min-max : hard iron (%.2f, %.2f) uT, soft-iron gains (%.3f, %.3f)' % (*b_mm, G[0, 0], G[1, 1]))
    print('ellipse : hard iron (%.2f, %.2f) uT, soft iron [[%.3f %.3f] [%.3f %.3f]]'
          % (*c_el, *(W / np.sqrt(np.linalg.det(W))).ravel()))
    cases = {'raw': h, 'min-max': (h - b_mm) @ G.T, 'ellipse': (h - c_el) @ W.T}
    print('\nheading error [deg]  mean     RMS  max|err|  radius sd/mean')
    for name, hc in cases.items():
        e = heading_error(hc, yaw_true)
        r = np.linalg.norm(hc, axis=1)
        print('%-18s %7.2f %7.2f %8.2f %12.2f %%' % (name, e.mean(), np.sqrt(np.mean(e ** 2)),
                                                    np.abs(e).max(), r.std() / r.mean() * 100))
    hh = np.linalg.norm(cases['ellipse'], axis=1).mean()
    print('\nhorizontal field %.1f uT; max error from the hard iron alone asin(|b|/H) = %.1f deg'
          % (hh, np.degrees(np.arcsin(min(1.0, np.linalg.norm(c_el) / hh)))))
    if a.plot:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 5))
        for name, hc in cases.items():
            ax[0].plot(hc[:, 0], hc[:, 1], '.', ms=2, label=name)
            ax[1].plot(yaw_true, heading_error(hc, yaw_true), '.', ms=2, label=name)
        ax[0].set_aspect('equal'); ax[0].set_xlabel('mx [uT]'); ax[0].set_ylabel('my [uT]')
        ax[1].set_xlabel('true yaw [deg]'); ax[1].set_ylabel('heading error [deg]')
        for x in ax:
            x.grid(True); x.legend()
        fig.tight_layout(); fig.savefig(a.plot, dpi=120)
        print('wrote', a.plot)


if __name__ == '__main__':
    main()
