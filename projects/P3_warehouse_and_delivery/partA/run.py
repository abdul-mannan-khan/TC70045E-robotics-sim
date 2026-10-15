#!/usr/bin/env python3
"""P3 Warehouse and delivery - Part A: the stock-taking robot.
Run:  python3 ~/labs/projects/P3_warehouse_and_delivery/partA/run.py

The robot tours the store room by itself; the parcel finder looks at every camera picture, picks out the red and the
green parcel by colour, measures their distance with the D455 depth camera and puts them on the map (cubes in RViz).
At the end it compares each parcel's position with the truth.
Writes ~/work/P3/partA/results.csv, figure.png, run_NN_<label>/ and stock.csv - the HAND-OVER to Part B.
"""
import os
import re
import signal
import sys

sys.path.insert(0, os.path.expanduser('~/labs/projects/tools'))
import projlib as P   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
COLUMNS = ['config', 'run', 'date', 'computer', 'camera_range_m', 'smallest_blob_px', 'turn_speed', 'red_detections',
           'red_error_m', 'green_detections', 'green_error_m', 'mean_error_m', 'parcels_found', 'notes']


def main():
    s = P.load_settings(os.path.join(HERE, 'settings.yaml'), ['label', 'camera_range', 'smallest_blob', 'turn_speed'])
    wd = P.workdir('P3', 'partA')
    n, rd = P.new_run_dir(wd, s['label'])
    P.say('run %d "%s": camera range %s m, smallest blob %s px, turn speed %s rad/s'
          % (n, s['label'], s['camera_range'], s['smallest_blob'], s['turn_speed']))

    P.step(1, 3, 'start the store room, the robot and RViz; the robot tours the room (about 3 minutes)')
    finder_src = os.path.join(P.LABS, 'solutions/week06/box_finder.py')
    finder = P.make_copy(finder_src, os.path.join(rd, 'parcel_finder.py'), [
        ('MAX_RANGE = 3.5', 'MAX_RANGE = %.2f' % float(s['camera_range'])),
        ('MIN_AREA = 80', 'MIN_AREA = %d' % int(s['smallest_blob']))])
    log = os.path.join(rd, 'finder.log')
    tour, ok = P.robot_launch('ros2 launch ~/labs/week06/launch/perception.launch.py tour:=true turn_rate:=%s'
                              % s['turn_speed'], os.path.join(rd, 'tour.log'), r'tour finished', 900, 'the tour',
                              companion=lambda: P.start('python3 -u %s --ros-args -p use_sim_time:=true' % finder, log))
    fp = P.robot_launch.companion
    if not ok:
        P.say('the tour did not finish - using what was seen so far')
    else:
        P.say('tour finished')

    P.step(2, 3, 'the parcel finder\'s summary')
    P.stop(fp, signal.SIGINT, wait=20)
    P.clean_robot_sim()
    out = P.read(log)
    rows = {}
    for colour in ('red', 'green'):
        m = re.search(r'^%s\s+(\d+)\s+\(\s*([-\d.]+),\s*([-\d.]+)\)\s+\(([-\d.]+), ([-\d.]+)\)\s+([\d.]+)' % colour, out, re.M)
        rows[colour] = m.groups() if m else None
        P.say('%-6s %s' % (colour, 'detections %s, on the map at (%s, %s), true (%s, %s), error %s m' % m.groups()
                           if m else 'NOT FOUND'))
    if not any(rows.values()):
        P.stop_with('no parcel was found - see %s/finder.log' % rd)

    P.step(3, 3, 'results, stock list and figure')
    with open(os.path.join(wd, 'stock.csv'), 'w') as f:
        f.write('name,x,y,detections\n')
        for colour, r in rows.items():
            if r:
                f.write('%s parcel,%s,%s,%s\n' % (colour, r[1], r[2], r[0]))
    errs = [float(r[5]) for r in rows.values() if r]
    g = lambda c, i: rows[c][i] if rows[c] else ''   # noqa: E731
    P.append_result(wd, COLUMNS, {
        'config': s['label'], 'run': n, 'date': P.now(), 'computer': P.computer(), 'camera_range_m': s['camera_range'],
        'smallest_blob_px': s['smallest_blob'], 'turn_speed': s['turn_speed'], 'red_detections': g('red', 0) or 0,
        'red_error_m': g('red', 5), 'green_detections': g('green', 0) or 0, 'green_error_m': g('green', 5),
        'mean_error_m': '%.3f' % (sum(errs) / len(errs)), 'parcels_found': len(errs)})
    P.bar_figure(wd, 'mean_error_m', 'parcel position error [m]', 'P3 Part A - stock-taking robot')
    P.finish(wd, 'RUN %d "%s": %d of 2 parcels found, mean position error %.3f m\nStock list (hand-over to Part B): %s'
             % (n, s['label'], len(errs), sum(errs) / len(errs), os.path.join(wd, 'stock.csv')))


if __name__ == '__main__':
    main()
