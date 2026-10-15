#!/usr/bin/env python3
"""P1 Security - Part B: the security drone. Run:  python3 ~/labs/projects/P1_security/partB/run.py

Takes the alarm log of your Part A patrol robot (~/work/P1/partA/alarms.csv), turns every FAILED checkpoint into a
waypoint over the town, and lets the drone - controlled from ROS 2 - fly to each one, photograph it and come home.
With stop_bridge_after_waypoint the AirSim bridge is stopped in flight, to test the safety watchdog.
Writes ~/work/P1/partB/results.csv, figure.png and run_NN_<label>/ (photos, logs).
"""
import glob
import math
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.expanduser('~/labs/projects/tools'))
import projlib as P               # noqa: E402
from handover import load_points  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
COLUMNS = ['config', 'run', 'date', 'computer', 'alarms', 'waypoints_reached', 'photos', 'time_s', 'flown_m',
           'worst_miss_m', 'end_from_start_m', 'speed_mps', 'watchdog_s', 'bridge_stopped_after', 'watchdog_fired',
           'sharpness_mean', 'notes']
EXAMPLE = 'name,x,y,status,time_s\nroom 2 upper,5.00,3.00,FAILED,90.0\nroom 2 lower,4.80,-2.80,FAILED,90.0\n'


def main():
    s = P.load_settings(os.path.join(HERE, 'settings.yaml'),
                        ['label', 'speed', 'stop_bridge_after_waypoint', 'watchdog_seconds', 'scale'])
    wd = P.workdir('P1', 'partB')
    alarms = os.path.expanduser('~/work/P1/partA/alarms.csv')
    if s.get('use_course_example'):
        alarms = os.path.join(wd, 'example_alarms.csv')
        open(alarms, 'w').write(EXAMPLE)
    if not os.path.exists(alarms):
        P.stop_with('your alarm log %s is not on this computer.\nCopy it from your Part A computer into '
                    '~/work/P1/partA/ (Firefox -> your OneDrive -> download), or set use_course_example: true' % alarms)
    n, rd = P.new_run_dir(wd, s['label'])
    shutil.copy(alarms, os.path.join(rd, 'alarms_used.csv'))

    P.step(1, 5, 'hand-over: alarm log -> drone waypoints')
    try:
        pts = list(dict.fromkeys(load_points(alarms, scale=float(s['scale']), only='FAILED')))
    except ValueError as e:
        P.stop_with('%s (scale in settings.yaml)' % e)
    if not pts:
        P.stop_with('your alarm log has no FAILED checkpoint, so there is nothing for the drone to check.\n'
                    'Do a Part A run with an obstacle on a checkpoint, or set use_course_example: true')
    for i, p in enumerate(pts, 1):
        P.say('alarm %d -> fly to %.1f m east, %.1f m north of the take-off point' % (i, p[0], p[1]))
    route = pts + [(0.0, 0.0)]
    cx = sum(p[0] for p in route) / len(route)
    cy = sum(p[1] for p in route) / len(route)

    P.step(2, 5, 'start AirSim (town) and PX4 - 1 to 3 minutes')
    P.drone_sim_start('neighborhood', rd)
    P.step(3, 5, 'start the two ROS 2 bridges')
    a_bridge, b_bridge = P.drone_bridges(rd)

    P.step(4, 5, 'the flight - watch the AirSim window')
    prog = P.make_copy(os.path.join(P.LABS, 'solutions/week10/mission_node.py'), os.path.join(rd, 'security_drone.py'), [
        ('WAYPOINTS = [(10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]', 'WAYPOINTS = %r' % route),
        ('SPEED, TOL, STILL = 2.0, 0.5, 0.2', 'SPEED, TOL, STILL = %.2f, 0.5, 0.2' % float(s['speed'])),
        ('return time.monotonic() - self.t_odom < 1.0', 'return time.monotonic() - self.t_odom < %.2f' % float(s['watchdog_seconds'])),
        ('        n.face(start[0] + 5.0, start[1] + 5.0)          # the camera looks at the middle of the square\n',
         '        if math.hypot(start[0] + %.2f - n.pos[0], start[1] + %.2f - n.pos[1]) > 2.0:\n'
         '            n.face(start[0] + %.2f, start[1] + %.2f)     # the camera looks at the middle of the route\n'
         % (cx, cy, cx, cy)),
    ])
    for f in glob.glob(os.path.expanduser('~/mission/wp*.png')):
        os.remove(f)
    log = os.path.join(rd, 'mission.log')
    mission = P.start('python3 -u %s' % prog, log)
    cut = int(s['stop_bridge_after_waypoint'])
    if cut > 0:
        if P.wait_for(log, r'waypoint %d/' % cut, 300, mission, what='alarm %d' % cut):
            P.stop(a_bridge)
            P.say('AirSim bridge STOPPED in mid-air (simulated sensor failure) - the watchdog must land the drone')
    P.wait_for(log, r'RESULT .*', 600, mission, what='the flight')
    P.stop(mission)
    P.stop(a_bridge)
    P.stop(b_bridge)
    out = P.read(log)
    for line in out.splitlines():
        if re.match(r'(waypoint|WATCHDOG|RESULT)', line):
            P.say(line)
    P.drone_sim_stop(rd)
    m = re.search(r'RESULT ([\d.]+) s, ([\d.]+) m flown, worst waypoint miss ([\d.]+) m, finished ([\d.]+) m', out)
    if not m:
        P.stop_with('the flight printed no RESULT line - see %s/mission.log' % rd)

    P.step(5, 5, 'photos, results and figure')
    photos = sorted(glob.glob(os.path.expanduser('~/mission/wp*.png')))
    for f in photos:
        shutil.copy(f, rd)
    sharp = P.photo_sharpness(photos) if photos else []
    reached = len(re.findall(r'^waypoint \d+/', out, re.M))
    fired = 'yes' if 'WATCHDOG' in out else 'no'
    P.append_result(wd, COLUMNS, {
        'config': s['label'], 'run': n, 'date': P.now(), 'computer': P.computer(), 'alarms': len(pts),
        'waypoints_reached': '%d of %d' % (reached, len(route)), 'photos': len(photos), 'time_s': m.group(1),
        'flown_m': m.group(2), 'worst_miss_m': m.group(3), 'end_from_start_m': m.group(4), 'speed_mps': s['speed'],
        'watchdog_s': s['watchdog_seconds'], 'bridge_stopped_after': cut or 'no', 'watchdog_fired': fired,
        'sharpness_mean': '%.0f' % (sum(sharp) / len(sharp)) if sharp else ''})
    P.bar_figure(wd, 'worst_miss_m', 'worst waypoint miss [m]', 'P1 Part B - security drone')
    P.finish(wd, 'RUN %d "%s": %d of %d waypoints, %s s, %s m flown, worst miss %s m, photos: %d, watchdog fired: %s\n'
             'Photos: %s' % (n, s['label'], reached, len(route), m.group(1), m.group(2), m.group(3), len(photos),
                             fired, rd))


if __name__ == '__main__':
    main()
