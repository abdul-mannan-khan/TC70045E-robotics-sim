#!/usr/bin/env python3
"""map_check.py - score a saved map against the true lab world: which objects did the robot's sensors see?

The lab world (tc70045e_sim/worlds/lab.world) is a list of boxes and cylinders. This script reads it, draws each
object's outline into the map's grid (map = world - spawn pose; spawn (-3.0, -0.4)), and then reports, object by
object, whether the saved map marks it as an obstacle. It also counts "phantom" obstacle cells: occupied cells more
than 0.15 m from any real object or wall (noise, floor seen as obstacle, smeared walls).

Objects worth watching:
  low_step    8 cm high      - under the LiDAR beam, only the depth camera can see it
  table_top   0.73-0.77 m    - above the LiDAR beam; the LiDAR only sees four 5 cm legs
  crates, pillars, benches   - both sensors see these

Usage (no ROS needed):
  python3 ~/labs/week04/scripts/map_check.py ~/maps/w4_toolbox.yaml
  python3 ~/labs/week04/scripts/map_check.py ~/maps/w4_lidar.yaml ~/maps/w4_lidar_d455.yaml     # side by side
"""
import argparse
import math
import os
import re
import xml.etree.ElementTree as ET

import numpy as np
import yaml

SPAWN = (-3.0, -0.4)
WATCH = ['low_step', 'table_top', 'table_leg_0', 'crate_1', 'crate_2', 'crate_3', 'pillar_1', 'pillar_2',
         'bench_1', 'bench_2', 'cabinet']


def world_file():
    try:
        from ament_index_python.packages import get_package_share_directory
        return os.path.join(get_package_share_directory('tc70045e_sim'), 'worlds', 'lab.world')
    except Exception:                                   # not in a ROS shell: use the copy in the repository
        return os.path.join(os.path.dirname(__file__), '..', '..', 'docker', 'tc70045e_sim', 'worlds', 'lab.world')


def read_objects(path):
    """name -> (kind, x, y, yaw, size_x, size_y, z_low, z_high) in world coordinates."""
    objects = {}
    for m in ET.parse(path).getroot().iter('model'):
        pose, geo = m.find('pose'), m.find('link/collision/geometry')
        if pose is None or geo is None:
            continue
        x, y, z, _, _, yaw = (float(v) for v in pose.text.split())
        if geo.find('box') is not None:
            sx, sy, sz = (float(v) for v in geo.find('box/size').text.split())
            objects[m.get('name')] = ('box', x, y, yaw, sx, sy, z - sz / 2, z + sz / 2)
        elif geo.find('cylinder') is not None:
            r, h = float(geo.find('cylinder/radius').text), float(geo.find('cylinder/length').text)
            objects[m.get('name')] = ('cyl', x, y, 0.0, 2 * r, 2 * r, z - h / 2, z + h / 2)
    return objects


def read_map(yaml_path):
    meta = yaml.safe_load(open(yaml_path))
    pgm = os.path.join(os.path.dirname(os.path.abspath(yaml_path)), meta['image'])
    data = open(pgm, 'rb').read()
    head = re.match(rb'P5\s+(?:#.*\s+)*(\d+)\s+(\d+)\s+(\d+)\s', data)
    w, h = int(head.group(1)), int(head.group(2))
    img = np.frombuffer(data[head.end():head.end() + w * h], np.uint8).reshape(h, w)[::-1]   # row 0 = bottom
    occ = img < 100                                      # map_saver: 0 = occupied, 254 = free, 205 = unknown
    return occ, meta['resolution'], meta['origin'][0], meta['origin'][1]


def footprint(obj, xs, ys, margin):
    """True for grid cells (cell centres xs, ys in world coordinates) inside the object's footprint + margin."""
    kind, x, y, yaw, sx, sy = obj[:6]
    dx, dy = xs - x, ys - y
    if kind == 'cyl':
        return np.hypot(dx, dy) <= sx / 2 + margin
    c, s = math.cos(yaw), math.sin(yaw)
    u, v = c * dx + s * dy, -s * dx + c * dy
    return (np.abs(u) <= sx / 2 + margin) & (np.abs(v) <= sy / 2 + margin)


def score(yaml_path, objects):
    occ, res, ox, oy = read_map(yaml_path)
    rows, cols = np.indices(occ.shape)
    xs = ox + (cols + 0.5) * res + SPAWN[0]              # cell centres in WORLD coordinates
    ys = oy + (rows + 0.5) * res + SPAWN[1]
    out, near_any = {}, np.zeros_like(occ)
    for name, obj in objects.items():
        if name == 'ground_plane':
            continue
        near_any |= footprint(obj, xs, ys, 0.15)
        if name in WATCH:
            cells = footprint(obj, xs, ys, 1.5 * res) & ~footprint(obj, xs, ys, -1.5 * res)   # the outline, 3 cells wide
            out[name] = (occ[cells].mean() if cells.any() else 0.0, cells.sum())   # (a LiDAR only sees outlines)
    phantom = int((occ & ~near_any).sum())
    return out, phantom, int(occ.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('maps', nargs='+', help='map .yaml files from map_saver_cli')
    a = ap.parse_args()
    objects = read_objects(world_file())
    results = [score(m, objects) for m in a.maps]
    names = [os.path.splitext(os.path.basename(m))[0] for m in a.maps]
    print('%-12s %-14s' % ('object', 'height [m]') + ''.join('%22s' % n[:21] for n in names))
    for name in WATCH:
        o = objects[name]
        line = '%-12s %4.2f - %4.2f   ' % (name, o[6], o[7])
        for r in results:
            frac = r[0][name][0]
            line += '%22s' % ('%s (%3.0f %% of outline)' % ('SEEN  ' if frac >= 0.15 else 'MISSED', 100 * frac))
        print(line)
    print('%-27s' % 'phantom obstacle cells' + ''.join('%22d' % r[1] for r in results))
    print('%-27s' % 'occupied cells in total' + ''.join('%22d' % r[2] for r in results))
    print('SEEN = at least 15 % of the cells along the object\'s outline are marked occupied. '
          'Phantom = occupied more than 0.15 m from any real object or wall.')


if __name__ == '__main__':
    main()
