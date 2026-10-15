"""Measure how sharp photos are: the variance of the Laplacian (a standard focus / motion-blur measure). A blurred
photo has weak edges and a low value; compare photos of the same scene only (the number depends on the scene).

Usage    python3 sharpness.py ~/mission/*.png
         python3 sharpness.py ~/survey/*.png --csv ~/work/project/sharpness.csv
"""
import argparse
import os

import numpy as np
from PIL import Image


def laplacian_variance(path):
    g = np.asarray(Image.open(path).convert('L'), dtype=np.float64)
    lap = (g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:] - 4.0 * g[1:-1, 1:-1])   # 4-neighbour Laplacian
    return lap.var()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('images', nargs='+')
    ap.add_argument('--csv', help='also write file,sharpness to this CSV')
    a = ap.parse_args()
    rows = [(p, laplacian_variance(p)) for p in a.images]
    for p, v in rows:
        print('%-40s %10.1f' % (os.path.basename(p), v))
    if a.csv:
        with open(a.csv, 'w') as f:
            f.write('file,sharpness\n')
            f.writelines('%s,%.2f\n' % (os.path.basename(p), v) for p, v in rows)
        print('saved', a.csv)


if __name__ == '__main__':
    main()
