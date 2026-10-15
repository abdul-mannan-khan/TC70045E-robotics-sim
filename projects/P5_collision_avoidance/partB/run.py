#!/usr/bin/env python3
"""P5 Collision avoidance - Part B: the car that cannot crash.
Run:  python3 ~/labs/projects/P5_collision_avoidance/partB/run.py

A self-driving car on CARLA's motorway follows a car that slows down at 25 s and speeds up again at 45 s. Its radar
adaptive cruise control keeps the set speed and a time gap, and an emergency brake acts when a crash is close - the
course's rule, or with use_my_rule: yes your robot's reaction time from Part A (~/work/P5/partA/safety_rule.csv).
Writes ~/work/P5/partB/results.csv, figure.png and run_NN_<label>/ (log and plot).
"""
import csv
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.expanduser('~/labs/projects/tools'))
import projlib as P   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
COLUMNS = ['config', 'run', 'date', 'computer', 'use_my_rule', 'reaction_time_s', 'time_gap_s', 'car_ahead_slows_to_kmh',
           'smallest_gap_m', 'smallest_time_gap_s', 'smallest_ttc_s', 'speed_before_kmh', 'collision', 'notes']


def main():
    s = P.load_settings(os.path.join(HERE, 'settings.yaml'), ['label', 'use_my_rule', 'time_gap', 'car_ahead_slows_to'])
    mine = str(s['use_my_rule']).strip().lower() in ('yes', 'true', '1')
    slow = float(s['car_ahead_slows_to'])
    if not 0 <= slow <= 50:
        P.stop_with('car_ahead_slows_to must be between 0 and 50 km/h')
    wd = P.workdir('P5', 'partB')
    tr = 0.0
    if mine:
        rule = os.path.expanduser('~/work/P5/partA/safety_rule.csv')
        if s.get('use_course_example'):
            rule = os.path.join(wd, 'example_safety_rule.csv')
            open(rule, 'w').write('reaction_time_s,stop_distance_m,from_run\n0.300,0.45,course example\n')
        if not os.path.exists(rule):
            P.stop_with('your safety rule %s is not on this computer.\nCopy it from your Part A computer into '
                        '~/work/P5/partA/ (Firefox -> your OneDrive -> download), or set use_course_example: true' % rule)
        tr = float(list(csv.DictReader(open(rule)))[0]['reaction_time_s'])
    n, rd = P.new_run_dir(wd, s['label'])

    P.step(1, 3, 'hand-over: emergency brake = %s' % (
        'time-to-collision < 1.5 s, or closer than 5 m + speed x %.2f s (your rule)' % tr if mine
        else 'time-to-collision < 1.5 s, or closer than 5 m (course rule)'))
    P.step(2, 3, 'start CARLA, then 70 s of motorway driving - watch the window')
    P.carla_start(rd)
    prog = P.make_copy(os.path.join(P.LABS, 'solutions/week11/acc.py'), os.path.join(rd, 'acc_car.py'), [
        ('return 25.0 if 25.0 <= t < 45.0 else 50.0', 'return %.1f if 25.0 <= t < 45.0 else 50.0' % slow),
        ('if ttc < 1.5 or gap < 5.0:', 'if ttc < 1.5 or gap < 5.0 + kmh / 3.6 * %.3f:' % tr),
    ])
    log = os.path.join(rd, 'car.log')
    car = P.start('python3 -u %s --show --time-gap %s' % (prog, s['time_gap']), log, ros=False)
    P.wait_for(log, r'RESULT .*', 600, car, what='the drive')
    P.stop(car)
    P.carla_stop(rd)
    out = P.read(log)
    m = re.search(r'RESULT smallest true gap ([-\d.]+) m, smallest time gap ([-\d.]+) s, smallest radar TTC ([\d.]+|inf) s, '
                  r'speed before the slow-down ([\d.]+) km/h', out)
    if not m or not os.path.exists(os.path.expanduser('~/acc.csv')):
        P.stop_with('the drive printed no RESULT line - see %s/car.log' % rd)
    shutil.copy(os.path.expanduser('~/acc.csv'), os.path.join(rd, 'acc_log.csv'))

    P.step(3, 3, 'results and figures')
    crash = 'YES' if float(m.group(1)) <= 0 else 'no'
    P.time_figure(os.path.join(rd, 'acc_log.csv'), os.path.join(rd, 'drive_plot.png'),
                  [('speed [km/h]', [('speed_kmh', 'your car'), ('lead_kmh', 'car ahead')]),
                   ('gap [m]', [('true_gap_m', 'gap to the car ahead')]),
                   ('brake (0-1)', [('brake', 'brake')])],
                  'motorway - %s' % s['label'])
    P.append_result(wd, COLUMNS, {
        'config': s['label'], 'run': n, 'date': P.now(), 'computer': P.computer(), 'use_my_rule': 'yes' if mine else 'no',
        'reaction_time_s': '%.3f' % tr if mine else '', 'time_gap_s': s['time_gap'], 'car_ahead_slows_to_kmh': slow,
        'smallest_gap_m': m.group(1), 'smallest_time_gap_s': m.group(2), 'smallest_ttc_s': m.group(3),
        'speed_before_kmh': m.group(4), 'collision': crash})
    P.bar_figure(wd, 'smallest_gap_m', 'smallest gap to the car ahead [m]', 'P5 Part B - radar cruise control')
    P.finish(wd, 'RUN %d "%s": smallest gap %s m, smallest time gap %s s, smallest TTC %s s, collision: %s\nDrive plot: %s'
             % (n, s['label'], m.group(1), m.group(2), m.group(3), crash, os.path.join(rd, 'drive_plot.png')))


if __name__ == '__main__':
    main()
