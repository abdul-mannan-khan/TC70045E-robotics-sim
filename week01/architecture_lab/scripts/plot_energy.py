#!/usr/bin/env python3
"""Plot the endurance run logged by energy_log.py: pack voltage, current and state of charge against battery time.

Usage    python3 ~/labs/week01/scripts/plot_energy.py                    # reads ~/labs/week01/energy_log.csv
         python3 ~/labs/week01/scripts/plot_energy.py my_run.csv
Output   energy_log.png next to the CSV (a figure for your report - label it SIMULATED in the caption).
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')                                     # no window needed; write a file
import matplotlib.pyplot as plt
import pandas as pd

path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/labs/week01/energy_log.csv')
d = pd.read_csv(path)
fig, ax = plt.subplots(3, 1, sharex=True, figsize=(7, 6))
ax[0].plot(d.t_battery_h, d.voltage_V)
ax[0].axhline(9.6, ls='--', c='r')
ax[0].set_ylabel('pack voltage [V]')
ax[1].plot(d.t_battery_h, d.current_A, lw=0.6)
ax[1].set_ylabel('pack current [A]')
ax[2].plot(d.t_battery_h, 100 * d.soc)
ax[2].set_ylabel('state of charge [%]')
ax[2].set_xlabel('battery time [h]  (simulated time x time_scale)')
for a in ax:
    a.grid(alpha=0.3)
fig.suptitle('Lab robot battery model, drive_pattern.py duty cycle (SIMULATED)')
out = os.path.splitext(path)[0] + '.png'
fig.tight_layout()
fig.savefig(out, dpi=150)
print('mean current %.2f A, mean power %.1f W, %d samples -> %s'
      % (d.current_A.mean(), d.power_W.mean(), len(d), out))
