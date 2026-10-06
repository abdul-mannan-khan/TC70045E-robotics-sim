#!/usr/bin/env python3
"""Week 3, Lab A - open-loop system identification of one wheel on the motor test bench.

Terminal 1 (the plant):   ros2 run tc70045e_sim motor_bench
Terminal 2 (this script): python3 ~/labs/week03/scripts/step_test.py

What it does (about 20 s):
  1. dead-zone staircase: duty 0, 1, 2 ... 12 % for 0.5 s each -> the first duty that turns the wheel
  2. three repeats of the duty sequence 0 -> 30 -> 60 -> 0 %, logging motor/speed (the encoder, m/s)
     and motor/speed_true (only a simulator has this - use it to check your identification)
  3. fits v(t) = v0 + dv (1 - exp(-(t - Td)/tau)) to every step and prints K, tau and Td
Files: step_test.csv (t, duty, v_enc, v_true) and step_test.png (the data with the fitted curves).
Options: --low 30 --high 60 --repeats 3 --hold 1.5

Expected output with the default bench: speed quantum 0.0096 m/s, first moving duty 7 %,
incremental K about 0.0084 (m/s)/%, apparent K (0 -> 30 %) about 0.0067, tau about 0.115 s, Td about 0.03 s.
"""
import argparse
import math
import time

import numpy as np
import rclpy
from rclpy.node import Node
from scipy.optimize import curve_fit
from std_msgs.msg import Float32


class StepTest(Node):
    """Plays a duty schedule on motor/duty and logs every motor/speed sample."""

    def __init__(self, schedule):
        super().__init__('step_test')
        self.schedule = schedule                  # list of (start time s, duty %)
        self.pub = self.create_publisher(Float32, 'motor/duty', 10)
        self.create_subscription(Float32, 'motor/speed', self.on_speed, 50)
        self.create_subscription(Float32, 'motor/speed_true', self.on_true, 50)
        self.t0 = None                            # the schedule starts with the first speed sample
        self.duty = 0.0
        self.v_true = 0.0
        self.rows = []
        self.events = []                          # (time the duty was actually published, duty)
        self.create_timer(0.005, self.tick)

    def now(self):
        return 0.0 if self.t0 is None else time.monotonic() - self.t0

    def tick(self):
        if self.t0 is None:
            return
        t = self.now()
        due = [d for (ts, d) in self.schedule if ts <= t]
        if due and due[-1] != self.duty:
            self.duty = due[-1]
            self.pub.publish(Float32(data=float(self.duty)))
            self.events.append((t, self.duty))

    def on_true(self, msg):
        self.v_true = msg.data

    def on_speed(self, msg):
        if self.t0 is None:
            self.t0 = time.monotonic()
        self.rows.append((self.now(), self.duty, msg.data, self.v_true))


def model(t, v0, dv, tau, td):
    """First order plus dead time, step applied at t = 0."""
    return v0 + dv * (1.0 - np.exp(-np.clip(t - td, 0.0, None) / tau))


def fit_step(t, v, t_step, hold):
    """Fit one step that starts at t_step and lasts hold seconds. Returns v0, dv, tau, td."""
    sel = (t >= t_step - 0.2) & (t < t_step + hold)
    ts, vs = t[sel] - t_step, v[sel]
    v0 = vs[ts < 0].mean()
    dv = vs[ts > 0.7 * hold].mean() - v0
    p, _ = curve_fit(model, ts, vs, p0=[v0, dv, 0.1, 0.03],
                     bounds=([-2, -2, 0.005, 0.0], [2, 2, 2.0, 0.5]))
    return p


def main():
    ap = argparse.ArgumentParser(description='open-loop step test on the motor bench')
    ap.add_argument('--low', type=float, default=30.0)
    ap.add_argument('--high', type=float, default=60.0)
    ap.add_argument('--repeats', type=int, default=3)
    ap.add_argument('--hold', type=float, default=1.5)
    a = ap.parse_args()

    stair = [(0.5 + 0.5 * i, float(i)) for i in range(13)]          # 0 ... 12 %, 0.5 s each
    sched, t = stair + [(7.0, 0.0)], 8.0
    steps = []                                                     # (from %, to %) in schedule order
    for _ in range(a.repeats):
        for frm, to in ((0.0, a.low), (a.low, a.high), (a.high, 0.0)):
            sched.append((t, to))
            steps.append((frm, to))
            t += a.hold
    sched.append((t, 0.0))

    rclpy.init()
    node = StepTest(sched)
    t_wait = time.monotonic()
    while rclpy.ok() and node.now() < t + 0.5:
        rclpy.spin_once(node, timeout_sec=0.01)
        if node.t0 is None and time.monotonic() - t_wait > 10.0:
            break                                                  # no bench: give up after 10 s
    node.pub.publish(Float32(data=0.0))
    d = np.array(node.rows)
    ev = [e for e in node.events if e[0] >= 7.5]                    # the steps (after the staircase)
    node.destroy_node()
    rclpy.shutdown()
    if len(d) < 100:
        raise SystemExit('only %d speed samples - is motor_bench running (same ROS_DOMAIN_ID)?' % len(d))
    np.savetxt('step_test.csv', d, delimiter=',', fmt='%.5f', header='t,duty,v_enc,v_true', comments='')
    tt, duty, v = d[:, 0], d[:, 1], d[:, 2]

    lv = np.unique(np.round(np.abs(v[v != 0]), 5))
    print('samples %d over %.1f s -> %.1f Hz' % (len(d), tt[-1] - tt[0], (len(d) - 1) / (tt[-1] - tt[0])))
    print('speed quantum: smallest |v| > 0 = %.4f m/s (theory 2 pi r/(C_rev Ts) = %.4f)'
          % (lv[0], 2 * math.pi * 0.0375 / (2464 * 0.01)))
    for i in range(13):                                             # dead-zone staircase
        m = (tt > 0.75 + 0.5 * i) & (tt < 1.0 + 0.5 * i)
        if m.any() and v[m].mean() > 0.004:
            print('dead zone: wheel first turns at %d %% duty (%.4f m/s)' % (i, v[m].mean()))
            break

    print('\n step          dv[m/s]   K[(m/s)/%]  tau[s]   Td[s]')
    res = {}
    fits = []
    for (te, _), (frm, to) in zip(ev, steps):
        v0, dv, tau, td = fit_step(tt, v, te, a.hold)
        k = dv / (to - frm)
        res.setdefault((frm, to), []).append((k, tau, td))
        fits.append((te, v0, dv, tau, td))
        print(' %4.0f -> %-4.0f %%  %+.4f   %.5f     %.3f    %.3f' % (frm, to, dv, k, tau, td))
    print('\nmean +/- sd over %d repeats (K in (m/s)/%%, tau and Td in s):' % a.repeats)
    for key, r in res.items():
        r = np.array(r)
        print('%3.0f->%-3.0f%% K %.5f +/- %.5f  tau %.3f +/- %.3f  Td %.3f +/- %.3f'
              % (key + tuple(np.c_[r.mean(0), r.std(0, ddof=1)].ravel())))
    k_inc = np.mean([r[0] for r in res[(a.low, a.high)]])
    v_low = np.mean([f[1] + f[2] for f, s in zip(fits, steps) if s == (0.0, a.low)])
    print('dead zone from the intercept: u0 = low - v(low)/K = %.1f %%' % (a.low - v_low / k_inc))
    plot(d, fits, a.hold)


def plot(d, fits, hold):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(d[:, 0], d[:, 2], '.', ms=2, label='motor/speed (encoder)')
    ax.plot(d[:, 0], d[:, 3], lw=0.8, label='motor/speed_true')
    for te, v0, dv, tau, td in fits:
        ts = np.linspace(0, hold, 200)
        ax.plot(te + ts, model(ts, v0, dv, tau, td), 'k', lw=1)
    ax.set_xlabel('time [s]'); ax.set_ylabel('wheel speed [m/s]'); ax.grid(True); ax.legend()
    fig.tight_layout(); fig.savefig('step_test.png', dpi=120)
    print('wrote step_test.csv and step_test.png')


if __name__ == '__main__':
    main()
