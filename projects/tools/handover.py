"""Hand-over between your Part A robot and your Part B drone: read the points your robot wrote to a CSV file (an alarm
log, a stock list) and turn them into drone waypoints.

The robot's map and the drone's world are different places, so the points are moved and scaled into the drone's flying
area:  drone_x = (x - x0) * scale,  drone_y = (y - y0) * scale   (metres from the drone's take-off point).

Use in a drone script (e.g. your copy of mission_node.py), instead of the fixed WAYPOINTS list:
    import os, sys
    sys.path.insert(0, os.path.expanduser('~/labs/projects/tools'))
    from handover import load_points
    WAYPOINTS = load_points('~/work/project/alarms.csv', scale=3.0) + [(0.0, 0.0)]     # ... and home at the end

Check first, without flying:   python3 ~/labs/projects/tools/handover.py ~/work/project/alarms.csv --scale 3
The CSV needs columns x and y (metres, the robot's map frame). Optional: a column `status` – with --only FAILED only
those rows are used; a column `name` is printed.
"""
import argparse
import csv
import math
import os


def load_points(path, scale=1.0, x0=0.0, y0=0.0, only=None, max_radius=30.0):
    """Return [(x, y), ...] in the drone's frame. Rows with `status` different from `only` are skipped (if `only`).
    A point farther than max_radius metres from take-off raises ValueError: check your scale before you fly."""
    pts = []
    with open(os.path.expanduser(path), newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if only and row.get('status', '').strip().upper() != only.upper():
                continue
            x, y = (float(row['x']) - x0) * scale, (float(row['y']) - y0) * scale
            if math.hypot(x, y) > max_radius:
                raise ValueError('point (%.1f, %.1f) m is more than %.0f m from take-off - reduce the scale'
                                 % (x, y, max_radius))
            pts.append((round(x, 2), round(y, 2)))
    return pts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv')
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--x0', type=float, default=0.0)
    ap.add_argument('--y0', type=float, default=0.0)
    ap.add_argument('--only', help='use only rows whose status is this, e.g. FAILED')
    a = ap.parse_args()
    pts = load_points(a.csv, a.scale, a.x0, a.y0, a.only)
    print('%d waypoints for the drone (metres from take-off):' % len(pts))
    for p in pts:
        print('  (%.2f, %.2f)' % p)
    print('WAYPOINTS =', pts + [(0.0, 0.0)])


if __name__ == '__main__':
    main()
