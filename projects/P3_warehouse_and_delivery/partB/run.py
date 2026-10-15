#!/usr/bin/env python3
"""P3 Warehouse and delivery - Part B: the delivery drone.
Run:  python3 ~/labs/projects/P3_warehouse_and_delivery/partB/run.py

Takes your robot's stock list (~/work/P3/partA/stock.csv), turns every parcel into a delivery point over the town,
asks the pre-flight check for GO or NO-GO, and - on GO - flies the deliveries from ROS 2 with a proof-of-delivery photo
at each point, then comes home. With gps_fault: yes the GPS is switched off first, so the check must say NO-GO.
Writes ~/work/P3/partB/results.csv, figure.png and run_NN_<label>/ (photos, logs).
"""
import glob
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.expanduser('~/labs/projects/tools'))
import projlib as P               # noqa: E402
from handover import load_points  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
COLUMNS = ['config', 'run', 'date', 'computer', 'parcels', 'gps_fault', 'verdict', 'deliveries', 'photos', 'time_s',
           'flown_m', 'worst_miss_m', 'end_from_start_m', 'speed_mps', 'sharpness_mean', 'result', 'notes']
EXAMPLE = 'name,x,y,detections\nred parcel,1.41,-2.40,198\ngreen parcel,7.14,-0.40,104\n'


def main():
    s = P.load_settings(os.path.join(HERE, 'settings.yaml'), ['label', 'gps_fault', 'speed', 'scale'])
    fault = str(s['gps_fault']).strip().lower() in ('yes', 'true', '1')
    wd = P.workdir('P3', 'partB')
    stock = os.path.expanduser('~/work/P3/partA/stock.csv')
    if s.get('use_course_example'):
        stock = os.path.join(wd, 'example_stock.csv')
        open(stock, 'w').write(EXAMPLE)
    if not os.path.exists(stock):
        P.stop_with('your stock list %s is not on this computer.\nCopy it from your Part A computer into '
                    '~/work/P3/partA/ (Firefox -> your OneDrive -> download), or set use_course_example: true' % stock)
    n, rd = P.new_run_dir(wd, s['label'])
    shutil.copy(stock, os.path.join(rd, 'stock_used.csv'))

    P.step(1, 5, 'hand-over: stock list -> delivery points')
    try:
        pts = load_points(stock, scale=float(s['scale']))
    except ValueError as e:
        P.stop_with('%s (scale in settings.yaml)' % e)
    if not pts:
        P.stop_with('your stock list has no parcel in it - run Part A again, or set use_course_example: true')
    for i, p in enumerate(pts, 1):
        P.say('parcel %d -> deliver %.1f m east, %.1f m north of the take-off point' % (i, p[0], p[1]))
    route = pts + [(0.0, 0.0)]
    cx = sum(p[0] for p in route) / len(route)
    cy = sum(p[1] for p in route) / len(route)

    P.step(2, 5, 'start AirSim (town) and PX4 - 1 to 3 minutes')
    P.drone_sim_start('neighborhood', rd)
    if fault:
        P.run('python3 -u ~/labs/week12/scripts/inject_fault.py --sensor gps --type off', os.path.join(rd, 'fault.log'), 120,
              ros=False)
        P.say('GPS switched OFF (simulated fault) - waiting 20 s for the autopilot to notice')
        time.sleep(20)

    P.step(3, 5, 'pre-flight check: GO or NO-GO?')
    pre = P.run('python3 -u ~/labs/solutions/week12/preflight.py --alt 15 --length 30 --width 30',
                os.path.join(rd, 'preflight.log'), 180, ros=False)
    P.time.sleep(5)                       # let the check's MAVLink connection close before the bridges open theirs
    for line in pre.splitlines():
        if re.search(r'PASS|FAIL|VERDICT', line):
            P.say(line.strip())
    v = re.search(r'VERDICT (NO-GO|GO)', pre)
    verdict = v.group(1) if v else 'no answer'
    res = {'config': s['label'], 'run': n, 'date': P.now(), 'computer': P.computer(), 'parcels': len(pts),
           'gps_fault': 'yes' if fault else 'no', 'verdict': verdict, 'speed_mps': s['speed']}

    if verdict != 'GO':
        P.say('NO-GO: the drone stays on the ground - the pre-flight check did its job')
        res['result'] = 'not flown (%s)' % verdict
        if fault:
            P.run('python3 -u ~/labs/week12/scripts/inject_fault.py --sensor gps --type ok', os.path.join(rd, 'fault_ok.log'),
                  120, ros=False)
        P.drone_sim_stop(rd)
        P.append_result(wd, COLUMNS, res)
        P.finish(wd, 'RUN %d "%s": %s - not flown' % (n, s['label'], verdict))
        return

    P.step(4, 5, 'start the ROS 2 bridges; the delivery flight - watch the AirSim window')
    a_bridge, b_bridge = P.drone_bridges(rd)
    prog = P.make_copy(os.path.join(P.LABS, 'solutions/week10/mission_node.py'), os.path.join(rd, 'delivery_drone.py'), [
        ('WAYPOINTS = [(10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]', 'WAYPOINTS = %r' % route),
        ('SPEED, TOL, STILL = 2.0, 0.5, 0.2', 'SPEED, TOL, STILL = %.2f, 0.5, 0.2' % float(s['speed'])),
        ('        n.face(start[0] + 5.0, start[1] + 5.0)          # the camera looks at the middle of the square\n',
         '        if math.hypot(start[0] + %.2f - n.pos[0], start[1] + %.2f - n.pos[1]) > 2.0:\n'
         '            n.face(start[0] + %.2f, start[1] + %.2f)     # the camera looks at the middle of the route\n'
         % (cx, cy, cx, cy)),
    ])
    for f in glob.glob(os.path.expanduser('~/mission/wp*.png')):
        os.remove(f)
    log = os.path.join(rd, 'delivery.log')
    mission = P.start('python3 -u %s' % prog, log)
    P.wait_for(log, r'RESULT .*', 600, mission, what='the delivery flight')
    for p in (mission, a_bridge, b_bridge):
        P.stop(p)
    out = P.read(log)
    for line in out.splitlines():
        if re.match(r'(waypoint|WATCHDOG|RESULT)', line):
            P.say(line)
    P.drone_sim_stop(rd)
    m = re.search(r'RESULT ([\d.]+) s, ([\d.]+) m flown, worst waypoint miss ([\d.]+) m, finished ([\d.]+) m', out)
    if not m:
        P.stop_with('the flight printed no RESULT line - see %s/delivery.log' % rd)

    P.step(5, 5, 'proof-of-delivery photos, results and figure')
    photos = sorted(glob.glob(os.path.expanduser('~/mission/wp*.png')))
    for f in photos:
        shutil.copy(f, rd)
    sharp = P.photo_sharpness(photos) if photos else []
    done = len(re.findall(r'^waypoint \d+/', out, re.M))
    res.update({'deliveries': '%d of %d' % (min(done, len(pts)), len(pts)), 'photos': len(photos), 'time_s': m.group(1),
                'flown_m': m.group(2), 'worst_miss_m': m.group(3), 'end_from_start_m': m.group(4),
                'sharpness_mean': '%.0f' % (sum(sharp) / len(sharp)) if sharp else '',
                'result': 'WATCHDOG landing' if 'WATCHDOG' in out else 'delivered'})
    P.append_result(wd, COLUMNS, res)
    P.bar_figure(wd, 'worst_miss_m', 'worst delivery-point miss [m]', 'P3 Part B - delivery drone')
    P.finish(wd, 'RUN %d "%s": GO - %s deliveries, %s s, %s m flown, worst miss %s m, photos: %d\nPhotos: %s'
             % (n, s['label'], res['deliveries'], m.group(1), m.group(2), m.group(3), len(photos), rd))


if __name__ == '__main__':
    main()
