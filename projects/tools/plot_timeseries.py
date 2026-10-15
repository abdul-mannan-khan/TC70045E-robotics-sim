"""Plot columns of a log file against time, one panel per column (for example the ACC log ~/acc.csv).

Usage    python3 plot_timeseries.py ~/acc.csv --list
         python3 plot_timeseries.py ~/acc.csv --columns speed_kmh,lead_kmh,true_gap_m --out fig2.png
         python3 plot_timeseries.py run1.csv run2.csv --columns true_gap_m --labels "gap 1 s,gap 2 s"
The file needs a time column (default `t`, change it with --time). With several files each panel shows one line per
file, so two versions of your code can be compared on the same axes.
"""
import argparse
import csv
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def load(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit('no rows in %s' % path)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv', nargs='+')
    ap.add_argument('--columns', help='comma-separated column names, one panel each')
    ap.add_argument('--labels', help='comma-separated legend names, one per file')
    ap.add_argument('--time', default='t')
    ap.add_argument('--out', default='timeseries.png')
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()

    files = [load(p) for p in a.csv]
    if a.list or not a.columns:
        print('columns:', ', '.join(files[0][0].keys()))
        return
    cols = [c.strip() for c in a.columns.split(',') if c.strip()]
    labels = [s.strip() for s in a.labels.split(',')] if a.labels else a.csv
    for c in cols + [a.time]:
        if c not in files[0][0]:
            sys.exit('no column "%s"; columns: %s' % (c, ', '.join(files[0][0].keys())))

    fig, axes = plt.subplots(len(cols), 1, sharex=True, figsize=(6.5, 1.9 * len(cols) + 0.6), squeeze=False)
    for ax, c in zip(axes[:, 0], cols):
        for rows, lab in zip(files, labels):
            t = [float(r[a.time]) for r in rows if r[c] not in ('', None)]
            y = [float(r[c]) for r in rows if r[c] not in ('', None)]
            ax.plot(t, y, linewidth=1.3, label=lab)
        ax.set_ylabel(c, fontsize=9)
        ax.grid(alpha=0.3)
    if len(files) > 1:
        axes[0, 0].legend(fontsize=8)
    axes[-1, 0].set_xlabel('%s [s]' % a.time)
    axes[0, 0].text(0.99, 0.95, 'simulated', transform=axes[0, 0].transAxes, ha='right', va='top', fontsize=8,
                    color='0.4')
    fig.tight_layout()
    fig.savefig(a.out, dpi=200)
    print('saved', a.out)


if __name__ == '__main__':
    main()
