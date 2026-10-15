"""Turn a project results file into a bar chart for the report: one bar per configuration (the average of its runs),
with a line from the smallest to the largest run and the number of runs above it.

Usage    python3 plot_results.py results.csv --list                                  (show the columns it found)
         python3 plot_results.py results.csv --metric end_error_m --out fig1.png
         python3 plot_results.py results.csv --metric end_error_m --ylabel "EKF error at the end [m]"
The file needs a column `config` (one name per configuration) and one row per run; every other column that holds
numbers can be plotted. Empty cells are skipped. Configurations appear in the order of their first row.
"""
import argparse
import csv
import statistics
import sys

import matplotlib
matplotlib.use('Agg')                      # no window needed: the figure is written to a file
import matplotlib.pyplot as plt


def number(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv')
    ap.add_argument('--metric', help='the column to plot')
    ap.add_argument('--ylabel', help='axis label (default: the column name)')
    ap.add_argument('--title', default='')
    ap.add_argument('--out', default='figure.png')
    ap.add_argument('--list', action='store_true', help='print the columns and configurations, then stop')
    a = ap.parse_args()

    with open(a.csv, newline='', encoding='utf-8-sig') as f:
        rows = [r for r in csv.DictReader(f) if any((v or '').strip() for v in r.values())]
    if not rows or 'config' not in rows[0]:
        sys.exit('no rows, or no column called "config" in %s' % a.csv)
    numeric = [c for c in rows[0] if c != 'config' and any(number(r.get(c)) is not None for r in rows)]
    configs = list(dict.fromkeys(r['config'].strip() for r in rows if r['config'].strip()))
    if a.list or not a.metric:
        print('configurations:', ', '.join(configs))
        print('columns with numbers (use one with --metric):', ', '.join(numeric))
        return
    if a.metric not in numeric:
        sys.exit('no numbers in column "%s"; columns with numbers: %s' % (a.metric, ', '.join(numeric)))

    values = {c: [number(r[a.metric]) for r in rows if r['config'].strip() == c and number(r[a.metric]) is not None]
              for c in configs}
    configs = [c for c in configs if values[c]]
    means = [statistics.mean(values[c]) for c in configs]
    low = [m - min(values[c]) for m, c in zip(means, configs)]
    high = [max(values[c]) - m for m, c in zip(means, configs)]

    fig, ax = plt.subplots(figsize=(max(4.0, 1.3 * len(configs) + 1.5), 3.6))
    x = range(len(configs))
    ax.bar(x, means, color='#4c78a8', width=0.6)
    ax.errorbar(x, means, yerr=[low, high], fmt='none', ecolor='black', capsize=5, linewidth=1.2)
    top = max(m + h for m, h in zip(means, high))
    for i, c in enumerate(configs):
        ax.text(i, means[i] + high[i] + 0.02 * abs(top), 'n=%d' % len(values[c]), ha='center', va='bottom', fontsize=8)
    ax.set_ylim(min(0.0, min(m - lo for m, lo in zip(means, low)) * 1.1), top * 1.15 if top > 0 else 1.0)
    ax.set_xticks(list(x))
    ax.set_xticklabels(configs, rotation=20, ha='right', fontsize=9)
    ax.set_ylabel(a.ylabel or a.metric)
    ax.set_title(a.title, fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    ax.text(0.99, 0.98, 'simulated', transform=ax.transAxes, ha='right', va='top', fontsize=8, color='0.4')
    fig.tight_layout()
    fig.savefig(a.out, dpi=200)
    for c, m in zip(configs, means):
        print('%-28s n=%d  mean %.3f  min %.3f  max %.3f' % (c, len(values[c]), m, min(values[c]), max(values[c])))
    print('saved', a.out)


if __name__ == '__main__':
    main()
