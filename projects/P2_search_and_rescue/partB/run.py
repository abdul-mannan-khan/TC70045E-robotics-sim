#!/usr/bin/env python3
"""P2 Search and rescue - Part B: the search drone. Run:  python3 ~/labs/projects/P2_search_and_rescue/partB/run.py

Takes your building's size from Part A (~/work/P2/partA/building.csv), scales it up to the search area around it,
asks the pre-flight check (GPS, radio link, battery) for GO or NO-GO, and - on GO - flies a lawn-mower search over the
mountain valley with a photo at every waypoint.
Writes ~/work/P2/partB/results.csv, figure.png and run_NN_<label>/ (photos, logs).
"""
import csv
import glob
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.expanduser('~/labs/projects/tools'))
import projlib as P   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
COLUMNS = ['config', 'run', 'date', 'computer', 'length_m', 'width_m', 'height_m', 'overlap', 'verdict',
           'battery_needed', 'predicted_min', 'waypoints', 'photos', 'time_s', 'flown_m', 'worst_miss_m',
           'footprint_m', 'cm_per_pixel', 'result', 'notes']


def main():
    s = P.load_settings(os.path.join(HERE, 'settings.yaml'), ['label', 'scale', 'height', 'overlap'])
    if float(s['height']) < 40:
        P.stop_with('height must be 40 m or more in this valley (the ridges are higher than that)')
    wd = P.workdir('P2', 'partB')
    b = os.path.expanduser('~/work/P2/partA/building.csv')
    if s.get('use_course_example'):
        b = os.path.join(wd, 'example_building.csv')
        open(b, 'w').write('width_m,depth_m,from_run\n10.05,8.05,course example\n')
    if not os.path.exists(b):
        P.stop_with('your building file %s is not on this computer.\nCopy it from your Part A computer into '
                    '~/work/P2/partA/ (Firefox -> your OneDrive -> download), or set use_course_example: true' % b)
    row = list(csv.DictReader(open(b)))[0]
    width = float(row['width_m']) * float(s['scale'])
    length = float(row['depth_m']) * float(s['scale'])
    n, rd = P.new_run_dir(wd, s['label'])
    shutil.copy(b, os.path.join(rd, 'building_used.csv'))
    args = '--alt %.0f --length %.0f --width %.0f --overlap %.2f' % (float(s['height']), length, width, float(s['overlap']))

    P.step(1, 4, 'hand-over: building %s x %s m -> search area %.0f x %.0f m' % (row['width_m'], row['depth_m'], width, length))
    P.step(2, 4, 'start AirSim (mountain valley) and PX4 - 1 to 3 minutes')
    P.drone_sim_start('mountains', rd)

    P.step(3, 4, 'pre-flight check: GO or NO-GO?')
    pre = P.run('python3 -u ~/labs/solutions/week12/preflight.py %s' % args, os.path.join(rd, 'preflight.log'), 180,
                ros=False)
    P.time.sleep(5)                       # let the check's MAVLink connection close before the flight opens its own
    for line in pre.splitlines():
        if re.search(r'PASS|FAIL|VERDICT', line):
            P.say(line.strip())
    v = re.search(r'VERDICT (NO-GO|GO)', pre)
    verdict = v.group(1) if v else 'no answer'
    bat = re.search(r'need (\d+) %', pre)
    pm = re.search(r': ([\d.]+) min survey', pre)
    res = {'config': s['label'], 'date': P.now(), 'computer': P.computer(), 'length_m': '%.0f' % length,
           'width_m': '%.0f' % width, 'height_m': s['height'], 'overlap': s['overlap'], 'verdict': verdict,
           'battery_needed': (bat.group(1) + ' %') if bat else '', 'predicted_min': pm.group(1) if pm else ''}

    if verdict != 'GO':
        P.say('NO-GO: the drone stays on the ground - this is the pre-flight check doing its job')
        res.update({'run': n, 'result': 'not flown (%s)' % verdict})
        out = ''
    else:
        P.step(4, 4, 'the search flight - watch the AirSim window')
        for f in glob.glob(os.path.expanduser('~/survey/*.png')):
            os.remove(f)
        log = os.path.join(rd, 'search.log')
        fl = P.start('python3 -u ~/labs/solutions/week09/mission.py %s' % args, log, ros=False)
        P.wait_for(log, r'RESULT .*', 900, fl, what='the search flight')
        P.stop(fl)
        out = P.read(log)
        for line in out.splitlines():
            if re.match(r'(plan|waypoint|time limit|RESULT)', line.strip()):
                P.say(line.strip())
        for f in sorted(glob.glob(os.path.expanduser('~/survey/*.png'))):
            shutil.copy(f, rd)
        plan = re.search(r'footprint ([\d.]+) m, row spacing ([\d.]+) m, (\d+) waypoints', out)
        r = re.search(r'RESULT (.*?): ([\d.]+) s, ([\d.]+) m flown, (\d+) photos, worst waypoint miss ([\d.]+) m', out)
        if not r:
            P.drone_sim_stop(rd)
            P.stop_with('the flight printed no RESULT line - see %s/search.log' % rd)
        fp = float(plan.group(1)) if plan else 0
        res.update({'run': n, 'waypoints': plan.group(3) if plan else '', 'photos': r.group(4), 'time_s': r.group(2),
                    'flown_m': r.group(3), 'worst_miss_m': r.group(5), 'footprint_m': '%.1f' % fp,
                    'cm_per_pixel': '%.1f' % (100 * fp / 640), 'result': r.group(1)})
    P.drone_sim_stop(rd)
    P.append_result(wd, COLUMNS, res)
    P.bar_figure(wd, 'time_s', 'search flight time [s]', 'P2 Part B - search drone')
    if verdict == 'GO':
        P.finish(wd, 'RUN %d "%s": GO - %s waypoints, %s photos, %s s, %s m flown, worst miss %s m, %s cm per pixel\n'
                 'Photos: %s' % (n, s['label'], res['waypoints'], res['photos'], res['time_s'], res['flown_m'],
                                 res['worst_miss_m'], res['cm_per_pixel'], rd))
    else:
        P.finish(wd, 'RUN %d "%s": %s - battery needed %s; not flown' % (n, s['label'], verdict, res['battery_needed']))


if __name__ == '__main__':
    main()
