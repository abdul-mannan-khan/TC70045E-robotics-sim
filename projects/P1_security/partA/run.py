#!/usr/bin/env python3
"""P1 Security - Part A: the patrol robot. Run:  python3 ~/labs/projects/P1_security/partA/run.py

Reads settings.yaml (next to this file), starts the building, the robot and Nav2 (Gazebo + RViz), lets the robot patrol
its checkpoints (with locked_door: yes, also a store room it cannot get into), and writes:
  ~/work/P1/partA/results.csv   one row per run          ~/work/P1/partA/figure.png   time per checkpoint
  ~/work/P1/partA/alarms.csv    the HAND-OVER for Part B: every checkpoint of the last run, REACHED or FAILED
"""
import os
import re
import sys

sys.path.insert(0, os.path.expanduser('~/labs/projects/tools'))
import projlib as P   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
COLUMNS = ['config', 'run', 'date', 'computer', 'laps', 'checkpoints', 'reached', 'failed', 'total_s',
           'mean_s_per_checkpoint', 'time_limit_s', 'safety_margin_m', 'locked_door', 'notes']
ATTEMPTS = 3
LOST_LIMIT = 200    # 'Transform data too old' lines in nav.log: more means AMCL stopped - the run is invalid
LOCKED = ('store room (locked)', 8.6, 0.0, 0.0)    # beyond the east wall, off the map: no path leads there


RELOCALISE = """
_TF = []


def relocalise(nav):
    \"\"\"(added by the project package) After a FAILED checkpoint the robot can stand still for a long time, and AMCL
    then stops refreshing its map -> odom transform, so every later goal fails too. Giving AMCL the robot's last pose
    again makes it publish at once.\"\"\"
    tr = None
    t0 = time.time()
    while time.time() - t0 < 3.0:
        rclpy.spin_once(nav, timeout_sec=0.1)
        try:
            tr = _TF[0].lookup_transform('map', 'base_footprint', rclpy.time.Time())
            break
        except Exception:
            pass
    if tr is None:
        return
    p = PoseStamped()
    p.header.frame_id, p.header.stamp = 'map', nav.get_clock().now().to_msg()
    p.pose.position.x, p.pose.position.y = tr.transform.translation.x, tr.transform.translation.y
    p.pose.orientation = tr.transform.rotation
    nav.setInitialPose(p)
    t0 = time.time()
    while time.time() - t0 < 2.0:
        rclpy.spin_once(nav, timeout_sec=0.1)


def visit("""


def add_relocalise(text):
    """Add relocalise() to the course patrol and call it after a failed checkpoint (and keep a TF listener)."""
    for old, new in (
            ('import sys\n', 'import sys\nimport time\n'),
            ('\ndef visit(', RELOCALISE),
            ('    seconds = (nav.get_clock().now() - t0).nanoseconds * 1e-9\n'
             '    return nav.getResult() == TaskResult.SUCCEEDED, seconds\n',
             '    seconds = (nav.get_clock().now() - t0).nanoseconds * 1e-9\n'
             '    ok = nav.getResult() == TaskResult.SUCCEEDED\n'
             '    if not ok:\n'
             '        relocalise(nav)\n'
             '    return ok, seconds\n'),
            ("    nav.waitUntilNav2Active(localizer='controller_server')",
             "    nav.waitUntilNav2Active(localizer='controller_server')\n"
             "    from tf2_ros import Buffer, TransformListener\n"
             "    _TF.extend([Buffer()])\n"
             "    _TF.append(TransformListener(_TF[0], nav))")):
        if old not in text:
            P.stop_with('the course patrol has changed (%s) - run update-labs, or ask the module leader' % old.strip()[:40])
        text = text.replace(old, new, 1)
    return text


def main():
    s = P.load_settings(os.path.join(HERE, 'settings.yaml'),
                        ['label', 'locked_door', 'time_limit', 'safety_margin', 'laps', 'checkpoints'])
    cps = [(str(c[0]), float(c[1]), float(c[2]), float(c[3])) for c in s['checkpoints']]
    locked = str(s['locked_door']).strip().lower() in ('yes', 'true', '1')
    if locked:
        cps.insert(max(0, len(cps) - 1), LOCKED)    # visit it before going back to the last checkpoint
    wd = P.workdir('P1', 'partA')
    n, rd = P.new_run_dir(wd, s['label'])
    P.say('run %d "%s": %d checkpoints, %s lap(s), locked door: %s' % (n, s['label'], len(cps), s['laps'],
                                                                       'yes' if locked else 'no'))

    wp = 'WAYPOINTS = [\n' + ''.join('    (%r, %.2f, %.2f, %.0f),\n' % c for c in cps) + ']\n'
    src = os.path.join(P.LABS, 'solutions/week03/patrol.py')
    text = open(src).read()
    text = re.sub(r'WAYPOINTS = \[\n.*?\n\]\n', lambda m: wp, text, count=1, flags=re.S)
    text = text.replace('TIME_LIMIT = 90.0', 'TIME_LIMIT = %.1f' % float(s['time_limit']), 1)
    text = add_relocalise(text)
    prog = os.path.join(rd, 'patrol.py')
    open(prog, 'w').write(text)
    log = os.path.join(rd, 'patrol.log')
    budget = 120 + int(s['laps']) * len(cps) * (float(s['time_limit']) + 30)

    for attempt in range(1, ATTEMPTS + 1):
        P.step(1, 4, 'start the building, the robot, Nav2 and RViz (about 1 minute)')
        nav, ok = P.robot_launch('ros2 launch ~/labs/week03/launch/nav.launch.py gui:=true', os.path.join(rd, 'nav.log'),
                                 r'AMCL confirmed the start pose', 240, 'the robot to localise')
        if not ok:
            P.clean_robot_sim()
            P.stop_with('the robot did not localise in 4 minutes - see %s/nav.log, then run again' % rd)
        P.say('robot localised')

        P.step(2, 4, 'safety margin')
        for cm in ('global_costmap/global_costmap', 'local_costmap/local_costmap'):
            P.run('ros2 param set /%s inflation_layer.inflation_radius %s' % (cm, s['safety_margin']),
                  os.path.join(rd, 'param.log'), timeout=60)
        P.say('safety margin %s m' % s['safety_margin'])

        P.step(3, 4, 'the patrol - watch Gazebo and RViz')
        patrol = P.start('python3 -u %s %d' % (prog, int(s['laps'])), log)
        P.wait_for(log, r'RESULT .*', budget, patrol, what='the patrol')
        P.stop(patrol)
        out = P.read(log)
        visits = re.findall(r'lap (\d+)\s+(.+?)\s+(REACHED|FAILED)\s+([\d.]+) s', out)
        for v in visits:
            P.say('lap %s  %-16s %-8s %s s' % v)
        lost = P.read(os.path.join(rd, 'nav.log')).count('Transform data too old')
        P.clean_robot_sim()
        if not visits:
            P.stop_with('the patrol printed no result - see %s/patrol.log' % rd)
        if lost < LOST_LIMIT:
            break
        # The robot lost track of where it is (AMCL stopped updating - happens on a slow or busy computer). Then every
        # later checkpoint fails for that reason, not because it is blocked: this run cannot be used.
        if attempt < ATTEMPTS:
            P.say('the robot LOST its position during this run (the computer was too busy) - the results cannot be used. '
                  'Starting the run again, attempt %d of %d' % (attempt + 1, ATTEMPTS))
        else:
            P.stop_with('the robot lost its position in %d attempts - the computer is too busy. Close other programs '
                        '(or use a Vast.ai machine) and run again' % ATTEMPTS)

    P.step(4, 4, 'results, alarm log and figure')
    where = {c[0]: (c[1], c[2]) for c in cps}
    with open(os.path.join(wd, 'alarms.csv'), 'w') as f:
        f.write('name,x,y,status,time_s\n')
        for lap, name, status, sec in visits:
            f.write('%s,%.2f,%.2f,%s,%s\n' % (name, where[name][0], where[name][1], status, sec))
    P.copy_if(os.path.join(wd, 'alarms.csv'), rd)
    times = [float(v[3]) for v in visits]
    reached = sum(v[2] == 'REACHED' for v in visits)
    P.append_result(wd, COLUMNS, {
        'config': s['label'], 'run': n, 'date': P.now(), 'computer': P.computer(), 'laps': s['laps'],
        'checkpoints': len(visits), 'reached': reached, 'failed': len(visits) - reached,
        'total_s': '%.0f' % sum(times), 'mean_s_per_checkpoint': '%.1f' % (sum(times) / len(times)),
        'time_limit_s': s['time_limit'], 'safety_margin_m': s['safety_margin'], 'locked_door': 'yes' if locked else 'no'})
    P.bar_figure(wd, 'mean_s_per_checkpoint', 'time per checkpoint [s]', 'P1 Part A - patrol robot')
    P.finish(wd, 'RUN %d "%s": %d of %d checkpoints reached, %.0f s in total, %.1f s per checkpoint\n'
             'Alarm log (hand-over to Part B): %s'
             % (n, s['label'], reached, len(visits), sum(times), sum(times) / len(times), os.path.join(wd, 'alarms.csv')))


if __name__ == '__main__':
    main()
