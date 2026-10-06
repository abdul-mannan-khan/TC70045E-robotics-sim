#!/usr/bin/env python3
"""Week 4, Lab A - bias, noise density and Allan deviation of one channel of a static IMU log.

Usage:
  python3 ~/labs/week04/scripts/allan_deviation.py imu_static.csv --col gz
  python3 ~/labs/week04/scripts/allan_deviation.py static_imu.csv --col gz --plot allan_gz.png
  python3 ~/labs/week04/scripts/allan_deviation.py static_imu.csv --col gz --overlap
Input: a CSV with a header line, a time column t [s] and the channel in deg/s (gx, gy, gz) or m/s^2 (ax ...),
e.g. from imu_capture_static.py or from `ros2 run tc70045e_sim imu_noise_model`.

Prints: sample rate, bias (mean), sigma, noise density sigma/sqrt(fs/2), then the Allan deviation for
tau = t0 * m (m = 1, 2, 5, 10, 20 ...) with the number of clusters K and the relative uncertainty
1/sqrt(2(K-1)). Points with K < 3 are not computed. Finally it reads the three coefficients off the curve:
  N (white noise / angle random walk) = adev at tau = 1 s               [-1/2 slope]
  B (bias instability)                = min(adev) / 0.664               [flat floor, points with K >= 9]
  K (rate random walk)                = adev(tau) * sqrt(3 / tau) at the longest usable tau  [+1/2 slope]
"""
import argparse

import numpy as np
import pandas as pd


def allan(x, t0, ms, overlap=False):
    """Allan deviation of x (sample interval t0) for cluster sizes ms. Returns rows (tau, K, adev)."""
    c = np.concatenate(([0.0], np.cumsum(x)))           # running sum: cluster means in O(1) each
    rows = []
    for m in ms:
        K = len(x) // m
        if K < 3:
            break
        step = 1 if overlap else m
        y = (c[m::step] - c[:-m:step][:len(c[m::step])]) / m      # cluster means (overlapping or not)
        d = y[m:] - y[:-m] if overlap else np.diff(y)
        rows.append((m * t0, K, np.sqrt(0.5 * np.mean(d ** 2))))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv')
    ap.add_argument('--col', default='gz')
    ap.add_argument('--overlap', action='store_true', help='overlapping clusters (smaller error bars)')
    ap.add_argument('--plot', default='', help='PNG file for the log-log plot')
    a = ap.parse_args()

    d = pd.read_csv(a.csv)
    x, t = d[a.col].to_numpy(), d['t'].to_numpy()
    t0 = np.median(np.diff(t))
    unit = 'deg/s' if a.col.startswith('g') else 'm/s^2'
    print('%s: %d samples, t0 = %.4f s -> fs = %.1f Hz, length %.0f s'
          % (a.col, len(x), t0, 1 / t0, t[-1] - t[0]))
    sd = x.std(ddof=1)
    print('bias = %+.5f %s   sigma = %.5f %s' % (x.mean(), unit, sd, unit))
    print('noise density = sigma/sqrt(fs/2) = %.5f %s/sqrt(Hz)' % (sd / np.sqrt(0.5 / t0), unit))

    ms = np.unique(np.round(np.logspace(0, 7, 43)).astype(int))
    rows = allan(x - x.mean(), t0, ms, a.overlap)
    print('%9s %8s %11s %7s' % ('tau [s]', 'K', 'adev', '+/-'))
    for tau, K, av in rows:
        if K > 2 and (tau >= 0.1 or tau == rows[0][0]):
            print('%9.2f %8d %11.6f %6.0f%%' % (tau, K, av, 100 / np.sqrt(2 * (K - 1))))

    tau, K, av = (np.array(c) for c in zip(*rows))
    n = np.interp(0.0, np.log(tau), np.log(av))                  # adev at tau = 1 s (log interpolation)
    ok = np.where(K >= 9)[0]                                       # points with <= 25 % uncertainty
    i, usable = ok[np.argmin(av[ok])], ok[-1]
    print('\nN = adev(1 s) = %.5f %s/sqrt(Hz)' % (np.exp(n), unit), end='')
    if unit == 'deg/s':
        print('  = %.3f deg/sqrt(h) angle random walk' % (np.exp(n) * 60))
    else:
        print('  = %.1f ug/sqrt(Hz)' % (np.exp(n) / 9.80665e-6))
    print('B = min adev/0.664 = %.5f %s (tau %.1f s, K %d, +/-%.0f %%)'
          % (av[i] / 0.664, unit, tau[i], K[i], 100 / np.sqrt(2 * (K[i] - 1))), end='')
    print(' = %.1f deg/h' % (av[i] / 0.664 * 3600) if unit == 'deg/s' else '')
    print('K = adev*sqrt(3/tau) at tau = %.0f s: %.6f %s/sqrt(s) (only if rising)'
          % (tau[usable], av[usable] * np.sqrt(3 / tau[usable]), unit))
    if a.plot:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        err = av / np.sqrt(2 * (K - 1))
        plt.figure(figsize=(7, 5))
        plt.errorbar(tau, av, yerr=err, fmt='o-', ms=3, capsize=2, label=a.col)
        plt.loglog(tau, np.exp(n) / np.sqrt(tau), 'k--', lw=0.8, label='-1/2 slope through N')
        plt.xscale('log'); plt.yscale('log'); plt.grid(True, which='both', lw=0.3)
        plt.xlabel('cluster time tau [s]'); plt.ylabel('Allan deviation [%s]' % unit); plt.legend()
        plt.tight_layout(); plt.savefig(a.plot, dpi=120)
        print('wrote', a.plot)


if __name__ == '__main__':
    main()
