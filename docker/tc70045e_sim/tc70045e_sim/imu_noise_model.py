"""Generate a long static IMU log in seconds, with a known MEMS error model, for Allan-variance work.

A real Allan-deviation study needs hours of still data. This script writes that data to CSV instantly, from a
model whose true parameters you know, so you can check that your analysis recovers them:

  gyro  = b0 + b_BI(t) + K(t) + white,   white noise density N  [deg/s/sqrt(Hz)]  -> angle random walk
                                          b_BI: bias instability (sum of first-order Gauss-Markov terms, flicker-like)
                                          K:    rate random walk, K [deg/s/sqrt(s)]
Usage:
  ros2 run tc70045e_sim imu_noise_model --hours 2 --rate 100 --out static_imu.csv
  ros2 run tc70045e_sim imu_noise_model --hours 2 --noise-density 0.015 --bias-instability 0.005 --rrw 0.0002
Columns: t [s], gx gy gz [deg/s], ax ay az [m/s^2], temp [degC]
"""
import argparse

import numpy as np
from scipy.signal import lfilter


def gauss_markov(n, dt, sigma, tau, rng):
    a = np.exp(-dt / tau)
    w = rng.standard_normal(n) * sigma * np.sqrt(1 - a * a)
    w[0] = rng.standard_normal() * sigma
    return lfilter([1.0], [1.0, -a], w)          # x[k] = a x[k-1] + w[k]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--hours', type=float, default=2.0)
    ap.add_argument('--rate', type=float, default=100.0, help='sample rate [Hz]')
    ap.add_argument('--noise-density', type=float, default=0.015, help='gyro white noise [deg/s/sqrt(Hz)]')
    ap.add_argument('--bias-instability', type=float, default=0.005, help='gyro bias instability [deg/s]')
    ap.add_argument('--rrw', type=float, default=0.0002, help='gyro rate random walk [deg/s/sqrt(s)]')
    ap.add_argument('--accel-density', type=float, default=230e-6, help='accel noise [g/sqrt(Hz)]')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', default='static_imu.csv')
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    dt = 1.0 / a.rate
    n = int(a.hours * 3600 * a.rate)
    t = np.arange(n) * dt
    cols = [t]
    for axis in range(3):
        white = rng.standard_normal(n) * a.noise_density * np.sqrt(a.rate)
        bi = sum(gauss_markov(n, dt, a.bias_instability / np.sqrt(3) / 0.664, tau, rng) for tau in (20.0, 200.0, 2000.0))
        rrw = np.cumsum(rng.standard_normal(n)) * a.rrw * np.sqrt(dt)
        b0 = rng.normal(0.0, 0.1)
        cols.append(b0 + bi + rrw + white)
    g = 9.80665
    for axis, mean in enumerate((0.0, 0.0, g)):
        cols.append(mean + rng.normal(0, 0.05) + rng.standard_normal(n) * a.accel_density * g * np.sqrt(a.rate))
    cols.append(28.0 + 3.0 * (1 - np.exp(-t / 900.0)))
    data = np.column_stack(cols)
    np.savetxt(a.out, data, delimiter=',', fmt='%.6f', header='t,gx,gy,gz,ax,ay,az,temp', comments='')
    print('wrote %d samples (%.1f h at %.0f Hz) to %s' % (n, a.hours, a.rate, a.out))
    print('model values (B is approximate: flicker noise is emulated by three Gauss-Markov terms): N = %.4f deg/s/sqrt(Hz) = %.3f deg/sqrt(h) ARW, B = %.4f deg/s, K = %.5f deg/s/sqrt(s)'
          % (a.noise_density, a.noise_density * 60, a.bias_instability, a.rrw))


if __name__ == '__main__':
    main()
