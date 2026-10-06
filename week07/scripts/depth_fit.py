"""Fit sigma = k * Z^2 to the output of range_test.py (or to your own real-camera CSV with the same columns).

Prints Table 1 (bias, sigma, fill rate per range), the fitted k, the effective sub-pixel disparity noise
sigma_d = k * f * b, the range at which sigma reaches 100 mm, and saves Figure 1 (sigma against Z with the fit).

Usage:
    python3 ~/labs/week07/scripts/depth_fit.py range_test.csv            # f = 446.8 px, b = 0.095 m
    python3 ~/labs/week07/scripts/depth_fit.py range_test.csv --f 446.8 --b 0.095 --fig fig1_sigma.png
Columns needed: z_true_m, mean_mm, sigma_mm, fill (one row per frame).
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')                                  # no window needed: the figure is saved to a file
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument('csv')
ap.add_argument('--f', type=float, default=446.8, help='focal length in pixels (camera_info k[0])')
ap.add_argument('--b', type=float, default=0.095, help='stereo baseline in metres')
ap.add_argument('--fig', default='fig1_sigma_vs_range.png')
a = ap.parse_args()

d = pd.read_csv(a.csv).dropna()
t = d.groupby('z_true_m').agg(mean_mm=('mean_mm', 'mean'), sigma_mm=('sigma_mm', 'mean'),
                              fill=('fill', 'mean'), n=('frame', 'count')).reset_index()
t['bias_mm'] = t.mean_mm - 1000 * t.z_true_m
t['bias_pct'] = 100 * t.bias_mm / (1000 * t.z_true_m)

z, s = t.z_true_m.values, t.sigma_mm.values / 1000.0
k = np.sum(s * z**2) / np.sum(z**4)                    # least squares through the origin: s = k z^2
sigma_d = k * a.f * a.b
z100 = np.sqrt(0.100 / k)

print(t[['z_true_m', 'n', 'mean_mm', 'bias_mm', 'bias_pct', 'sigma_mm', 'fill']].round(3).to_string(index=False))
print('fitted k        = %.3e 1/m' % k)
print('sigma_d = k f b = %.3f px   (f = %.1f px, b = %.3f m)' % (sigma_d, a.f, a.b))
print('sigma at 4 m    = %.1f mm = %.2f %% of range' % (1000 * k * 16, 100 * k * 4))
print('sigma = 100 mm at Z = %.2f m' % z100)

zz = np.linspace(0, max(z) * 1.05, 100)
plt.figure(figsize=(5, 3.5))
plt.plot(z, 1000 * s, 'o', label='measured (mean of per-frame sigma)')
plt.plot(zz, 1000 * k * zz**2, '-', label='fit  sigma = %.2e Z$^2$' % k)
plt.xlabel('range Z (m)')
plt.ylabel('sigma (mm)')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(a.fig, dpi=150)
print('saved', a.fig)
