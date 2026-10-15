#!/usr/bin/env python3
"""P4 Driverless shuttle - Part B: the road shuttle. Run:  python3 ~/labs/projects/P4_driverless_shuttle/partB/run.py

A self-driving car on CARLA's motorway keeps its lane by itself and drives your robot shuttle's timetable
(~/work/P4/partA/timetable.csv): 50 km/h, stop, wait, 50 km/h again - with a PI speed controller (throttle and brake).
Writes ~/work/P4/partB/results.csv, figure.png and run_NN_<label>/ (speed log and its plot).
"""
import csv
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.expanduser('~/labs/projects/tools'))
import projlib as P   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
COLUMNS = ['config', 'run', 'date', 'computer', 'kp', 'ki', 'timetable', 'speed_error_before_stop_kmh',
           'slowest_at_stop_kmh', 'back_to_45_s', 'mean_last10_kmh', 'max_error_last10_kmh', 'notes']
EXAMPLE = 'from_s,speed_kmh,what\n0,50,drive\n21,0,stop\n31,50,drive on\n'


def main():
    s = P.load_settings(os.path.join(HERE, 'settings.yaml'), ['label', 'kp', 'ki'])
    wd = P.workdir('P4', 'partB')
    tt = os.path.expanduser('~/work/P4/partA/timetable.csv')
    if s.get('use_course_example'):
        tt = os.path.join(wd, 'example_timetable.csv')
        open(tt, 'w').write(EXAMPLE)
    if not os.path.exists(tt):
        P.stop_with('your timetable %s is not on this computer.\nCopy it from your Part A computer into '
                    '~/work/P4/partA/ (Firefox -> your OneDrive -> download), or set use_course_example: true' % tt)
    table = [(float(r['from_s']), float(r['speed_kmh'])) for r in csv.DictReader(open(tt))]
    n, rd = P.new_run_dir(wd, s['label'])
    shutil.copy(tt, os.path.join(rd, 'timetable_used.csv'))
    stop_at = [t for t, v in table if v == 0][0] if any(v == 0 for _, v in table) else None
    restart = [t for t, v in table if stop_at is not None and t > stop_at and v > 0]
    seconds = (restart[0] if restart else table[-1][0]) + 30

    P.step(1, 3, 'hand-over: timetable ' + ', '.join('from %.0f s %.0f km/h' % r for r in table))
    P.step(2, 3, 'start CARLA, then the road shuttle drives its timetable (about 2 minutes) - watch the window')
    P.carla_start(rd)
    prog = P.make_copy(os.path.join(P.LABS, 'week11/scripts/02_cruise_control_api.py'), os.path.join(rd, 'road_shuttle.py'), [
        ('def main():\n', 'TIMETABLE = %r    # (from this time [s], target speed [km/h])\n\n\n'
                          'def target_at(t):\n    target = TIMETABLE[0][1]\n    for start, kmh in TIMETABLE:\n'
                          '        if t >= start:\n            target = kmh\n    return target\n\n\ndef main():\n' % table),
        ('            err = a.target - kmh\n', '            err = target_at(i * s.fixed_delta_seconds) - kmh\n'),
        ("pygame.display.set_caption('CARLA cruise control (no ROS)')", "pygame.display.set_caption('Road shuttle - your timetable')"),
    ])
    log = os.path.join(rd, 'shuttle.log')
    car = P.start('python3 -u %s --show --seconds %.0f --kp %s --ki %s' % (prog, seconds, s['kp'], s['ki']), log, ros=False)
    P.wait_for(log, r'RESULT .*', seconds * 4 + 120, car, what='the drive')
    P.stop(car)
    P.carla_stop(rd)
    out = P.read(log)
    r = re.search(r'RESULT last 10 s: mean ([\d.]+) km/h, max error ([\d.]+) km/h', out)
    src = os.path.expanduser('~/cruise_api.csv')
    if not r or not os.path.exists(src):
        P.stop_with('the drive printed no RESULT line - see %s/shuttle.log' % rd)
    shutil.copy(src, os.path.join(rd, 'speed_log.csv'))

    P.step(3, 3, 'how well did it keep the timetable?')
    rows = [(float(x['t']), float(x['speed_kmh'])) for x in csv.DictReader(open(os.path.join(rd, 'speed_log.csv')))]
    before = [abs(50 - v) for t, v in rows if stop_at and stop_at - 5 <= t < stop_at] or [0]
    at_stop = [v for t, v in rows if stop_at and restart and stop_at <= t < restart[0]] or [0]
    back = [t for t, v in rows if restart and t >= restart[0] and v >= 45]
    with open(os.path.join(rd, 'speed_log_with_target.csv'), 'w') as f:
        f.write('t,speed_kmh,target_kmh\n')
        for t, v in rows:
            tgt = [k for st, k in table if t >= st][-1]
            f.write('%.2f,%.2f,%.1f\n' % (t, v, tgt))
    P.time_figure(os.path.join(rd, 'speed_log_with_target.csv'), os.path.join(rd, 'speed_plot.png'),
                  [('speed [km/h]', [('speed_kmh', 'shuttle'), ('target_kmh', 'timetable')])],
                  'road shuttle - %s (kp %s, ki %s)' % (s['label'], s['kp'], s['ki']))
    res = {'config': s['label'], 'run': n, 'date': P.now(), 'computer': P.computer(), 'kp': s['kp'], 'ki': s['ki'],
           'timetable': ' / '.join('%.0f s %.0f km/h' % x for x in table),
           'speed_error_before_stop_kmh': '%.1f' % max(before), 'slowest_at_stop_kmh': '%.1f' % min(at_stop),
           'back_to_45_s': '%.1f' % (back[0] - restart[0]) if back else 'never',
           'mean_last10_kmh': r.group(1), 'max_error_last10_kmh': r.group(2)}
    P.append_result(wd, COLUMNS, res)
    P.bar_figure(wd, 'slowest_at_stop_kmh', 'slowest speed at the stop [km/h] (0 = stopped)', 'P4 Part B - road shuttle')
    P.finish(wd, 'RUN %d "%s": speed error before the stop %s km/h, slowest at the stop %s km/h, back to 45 km/h after '
             '%s s, last 10 s %s km/h\nSpeed plot: %s'
             % (n, s['label'], res['speed_error_before_stop_kmh'], res['slowest_at_stop_kmh'], res['back_to_45_s'],
                r.group(1), os.path.join(rd, 'speed_plot.png')))


if __name__ == '__main__':
    main()
