#!/usr/bin/env python3
"""Week 4, Lab C - aliasing of motor vibration when an IMU is decimated to a low report rate.

Usage:  python3 ~/labs/week04/inertial_sensing/scripts/aliasing_demo.py [--fs 25] [--plot aliasing.png]

A numerical experiment (no ROS needed). The IMU samples internally at 1125 Hz. The accelerometer sees
  - a real, slow body motion: 0.5 Hz, 0.20 m/s^2 amplitude            (what you want to keep)
  - motor vibration at f_v = (v / 2 pi r) * G  with r = 0.0375 m, G = 56, amplitude 0.50 m/s^2
  - white noise, 0.02 m/s^2 rms
and is reported at --fs Hz in four ways:
  A  pick every n-th sample (no filter)             - what a firmware that just reads the latest value does
  B  mean of the n samples since the last report   - a boxcar (sinc) filter: better, not enough
  C  anti-alias FIR low-pass at 0.4 fs, THEN decimate  (scipy.signal.decimate) - the correct order
  D  A followed by a 2 Hz low-pass in software       - filtering AFTER decimation: too late
For wheel speeds 0.1 ... 0.5 m/s it prints the amplitude found at the alias frequency |f_v - k fs|
(and, for D, how much of the real 0.5 Hz motion survives).
"""
import argparse

import numpy as np
from scipy import signal

F_INT, R, G = 1125.0, 0.0375, 56


def amp_at(x, fs, f):
    """Amplitude of the sinusoid at frequency f in x (Hann window, zero padded)."""
    n = len(x)
    X = np.fft.rfft((x - x.mean()) * np.hanning(n), 16 * n)
    fr = np.fft.rfftfreq(16 * n, 1 / fs)
    k = np.argmin(np.abs(fr - f))
    return 2 * np.abs(X[k - 8:k + 9]).max() / np.hanning(n).sum()


def report(x, n, fs):
    """The four ways of turning the internal-rate signal x into a fs-rate report."""
    b, a = signal.butter(4, 2.0 / (fs / 2))
    return {'A pick': x[::n],
            'B boxcar': x[:len(x) // n * n].reshape(-1, n).mean(axis=1),
            'C FIR+decim': signal.decimate(x, n, ftype='fir'),
            'D pick+2Hz LPF': signal.filtfilt(b, a, x[::n])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fs', type=float, default=25.0, help='report rate [Hz]')
    ap.add_argument('--plot', default='', help='PSD plot of the four reports at 0.3 m/s')
    a = ap.parse_args()
    n = int(round(F_INT / a.fs))
    fs = F_INT / n
    rng = np.random.default_rng(0)
    t = np.arange(int(60 * F_INT)) / F_INT                    # 60 s at the internal rate
    print('internal rate %.0f Hz, report %.1f Hz (Nyquist %.1f Hz), vibration 0.500 m/s^2'
          % (F_INT, fs, fs / 2))
    print('                    | amplitude at the alias [m/s^2]  | 0.5 Hz')
    print('    v  f_vib f_alias |  A pick  B box  C FIR  D LPF  | in D')
    for v in (0.1, 0.2, 0.3, 0.4, 0.5):
        fv = v / (2 * np.pi * R) * G
        f_alias = abs(fv - round(fv / fs) * fs)
        x = 0.2 * np.sin(2 * np.pi * 0.5 * t) + 0.5 * np.sin(2 * np.pi * fv * t)
        x += 0.02 * rng.standard_normal(len(t))
        out = report(x, n, fs)
        amps = [amp_at(y, fs, f_alias) for y in out.values()]
        print('%5.2f %6.1f %7.2f | %7.3f %6.3f %6.3f %6.3f  | %.3f'
              % (v, fv, f_alias, *amps, amp_at(out['D pick+2Hz LPF'], fs, 0.5)))
        if v == 0.3:
            keep = out
    print('(the real motion is 0.200 m/s^2 at 0.5 Hz; A, B and C keep it within 1 %)')
    if a.plot:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.figure(figsize=(9, 4))
        for name, y in keep.items():
            f, p = signal.welch(y, fs, nperseg=256)
            plt.semilogy(f, p, label=name)
        plt.xlabel('frequency [Hz]'); plt.ylabel('PSD [(m/s^2)^2/Hz]'); plt.grid(True); plt.legend()
        plt.title('0.3 m/s: 71.3 Hz vibration reported at %.0f Hz' % fs)
        plt.tight_layout(); plt.savefig(a.plot, dpi=120)
        print('wrote', a.plot)


if __name__ == '__main__':
    main()
