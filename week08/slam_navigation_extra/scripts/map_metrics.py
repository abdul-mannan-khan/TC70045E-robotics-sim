#!/usr/bin/env python3
"""map_metrics.py - measure a saved occupancy grid (map_saver_cli .pgm + .yaml) against the known lab room.

The lab world's room is 10.0 m x 8.0 m between the inner faces of its outer walls. A 2D LiDAR only ever hits
the inner face, so the outermost occupied cells ARE the inner faces. The script:
  1. finds the map rotation that makes the walls axis-aligned (smallest bounding box, +-5 deg, 0.1 deg steps),
  2. measures the room width and depth between the outermost occupied cells (robust percentiles),
  3. measures the wall thickness (occupied cells across the north wall), and counts free/occupied/unknown cells.
Quantisation: every length carries +-1 cell (+-0.05 m at 0.05 m resolution) of uncertainty.

Usage (no ROS needed, runs in a plain python3):
  python3 ~/labs/week09/scripts/map_metrics.py ~/maps/lab_slamtb.yaml
  python3 ~/labs/week09/scripts/map_metrics.py ~/maps/lab_carto.yaml --true 10.0 8.0

Expected output (slam_toolbox, one loop of drive_loop.py)
  resolution 0.050 m, 229 x 187 cells, occupied 2931, free 29172, unknown 10754
  map rotation relative to the walls: +0.1 deg
  room width  10.00 m (true 10.00 m)  scale error +0.0 %  (+-0.5 %)
  ...
"""
import argparse
import os
import numpy as np
import yaml


def read_pgm(path):
    with open(path, 'rb') as f:
        data = f.read()
    parts, i = [], 0
    while len(parts) < 4:                               # magic, width, height, maxval (skip # comments)
        while data[i:i + 1].isspace():
            i += 1
        if data[i:i + 1] == b'#':
            i = data.index(b'\n', i)
            continue
        j = i
        while not data[j:j + 1].isspace():
            j += 1
        parts.append(data[i:j]); i = j
    w, h = int(parts[1]), int(parts[2])
    return np.frombuffer(data[i + 1:i + 1 + w * h], np.uint8).reshape(h, w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('map_yaml')
    ap.add_argument('--true', nargs=2, type=float, default=[10.0, 8.0], metavar=('WIDTH', 'DEPTH'))
    a = ap.parse_args()
    meta = yaml.safe_load(open(a.map_yaml))
    img = read_pgm(os.path.join(os.path.dirname(os.path.abspath(a.map_yaml)), meta['image']))
    res, (ox, oy) = meta['resolution'], meta['origin'][:2]
    p = (255 - img.astype(float)) / 255.0               # negate: 0 -> occupancy probability
    occ, free = p > meta['occupied_thresh'], p < meta['free_thresh']
    if meta.get('mode') == 'trinary':                   # map_saver writes unknown as grey 205
        free &= img != 205
    h, w = img.shape
    print('resolution %.3f m, %d x %d cells, occupied %d, free %d, unknown %d'
          % (res, w, h, occ.sum(), free.sum(), (~occ & ~free).sum()))
    r, c = np.nonzero(occ)
    pts = np.column_stack([ox + (c + 0.5) * res, oy + (h - 1 - r + 0.5) * res])   # row 0 is the top

    def extent(q):                                      # robust size: 0.5 / 99.5 percentiles
        lo, hi = np.percentile(q, [0.5, 99.5], axis=0)
        return hi - lo, lo, hi
    best = min(np.arange(-5, 5.01, 0.1),
               key=lambda d: np.prod(extent(pts @ rot(np.radians(d)))[0]))
    q = pts @ rot(np.radians(best))
    size, lo, hi = extent(q)
    print('map rotation relative to the walls: %+.1f deg' % -best)
    for name, meas, true in (('width', size[0], a.true[0]), ('depth', size[1], a.true[1])):
        print('room %s %6.2f m (true %.2f m)  scale error %+.1f %%  (+-%.1f %%)'
              % (name, meas, true, 100 * (meas - true) / true, 100 * res / true))
    band = q[q[:, 1] > hi[1] - 0.3]                     # north wall: cells in the top 0.3 m
    cols = np.floor(band[:, 0] / res).astype(int)
    per_col = np.bincount(cols - cols.min())
    t = np.median(per_col[per_col > 0])
    print('north wall thickness: median %.0f cells = %.2f m' % (t, t * res))
    print('known (free + occupied) area: %.1f m^2 of %.1f m^2 room'
          % ((occ.sum() + free.sum()) * res * res, a.true[0] * a.true[1]))


def rot(t):
    """Row-vector rotation: points @ rot(t) rotates them by -t."""
    return np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])


if __name__ == '__main__':
    main()
