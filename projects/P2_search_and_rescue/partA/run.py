#!/usr/bin/env python3
"""P2 Search and rescue - Part A: the mapping robot. Run:  python3 ~/labs/projects/P2_search_and_rescue/partA/run.py

The robot drives a 24 m loop through the damaged building by itself and maps it - with the laser only, or with the
laser and the D455 depth camera. Then the map is saved and checked: were the hazards (an 8 cm step and a table top,
both below or above the laser) found, how many false obstacles, how big is the building?
Writes ~/work/P2/partA/results.csv, figure.png, run_NN_<label>/ (the map) and building.csv - the HAND-OVER to Part B.
"""
import os
import re
import sys

sys.path.insert(0, os.path.expanduser('~/labs/projects/tools'))
import projlib as P   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
COLUMNS = ['config', 'run', 'date', 'computer', 'sensors', 'camera_draws_map', 'floor_height_m', 'low_step',
           'table_top', 'hazards_found', 'phantom_cells', 'width_m', 'depth_m', 'loop', 'notes']


def main():
    s = P.load_settings(os.path.join(HERE, 'settings.yaml'), ['label', 'sensors'])
    sensors = str(s['sensors']).strip()
    if sensors not in ('lidar', 'lidar_and_camera'):
        P.stop_with('sensors must be lidar or lidar_and_camera (not "%s")' % sensors)
    wd = P.workdir('P2', 'partA')
    n, rd = P.new_run_dir(wd, s['label'])
    P.say('run %d "%s": %s' % (n, s['label'], sensors))

    P.step(1, 4, 'start the building, the robot, SLAM and RViz; the robot drives its loop (about 4 minutes)')
    if sensors == 'lidar':
        cmd = 'ros2 launch ~/labs/week04/launch/slam.launch.py slam:=toolbox drive:=true'
        draws, floor = '', ''
    else:
        draws, floor = str(s.get('camera_draws_map', 1)), float(s.get('floor_height', 0.04))
        if draws not in ('1', '2'):
            P.stop_with('camera_draws_map must be 1 or 2')
        cfg = P.make_copy(os.path.join(P.LABS, 'solutions/week04/rtabmap.yaml'), os.path.join(rd, 'rtabmap.yaml'), [
            ('Grid/Sensor: "1"', 'Grid/Sensor: "%s"' % draws),
            ('Grid/MaxGroundHeight: "0.04"', 'Grid/MaxGroundHeight: "%.3f"' % floor)])
        cmd = 'ros2 launch ~/labs/week04/launch/slam.launch.py slam:=rtabmap drive:=true config:=%s' % cfg
    slam, m = P.robot_launch(cmd, os.path.join(rd, 'slam.log'), r'loop finished: ([\d.]+) m in ([\d.]+) s', 900,
                             'the robot to finish its loop')
    if not m:
        P.clean_robot_sim()
        P.stop_with('the robot did not finish its loop - see %s/slam.log, then run again' % rd)
    P.say('loop finished: %s m in %s s' % m.groups())

    P.step(2, 4, 'save the map')
    mp = os.path.join(rd, 'map')
    P.run('ros2 run nav2_map_server map_saver_cli -f %s --ros-args -p use_sim_time:=true' % mp,
          os.path.join(rd, 'map_saver.log'), timeout=120)
    P.clean_robot_sim()
    if not os.path.exists(mp + '.yaml'):
        P.stop_with('the map was not saved - see %s/map_saver.log' % rd)

    P.step(3, 4, 'check the map: hazards, false obstacles, size')
    chk = P.run('python3 ~/labs/week04/scripts/map_check.py %s.yaml' % mp, os.path.join(rd, 'map_check.txt'), 120)
    met = P.run('python3 ~/labs/week04/scripts/map_metrics.py %s.yaml' % mp, os.path.join(rd, 'map_metrics.txt'), 120)
    found = {}
    for name in ('low_step', 'table_top'):
        h = re.search(r'^%s\s.*?(SEEN|MISSED)' % name, chk, re.M)
        found[name] = h.group(1) if h else '?'
    ph = re.search(r'phantom obstacle cells\s+(\d+)', chk)
    w = re.search(r'room width\s+([\d.]+) m', met)
    d = re.search(r'room depth\s+([\d.]+) m', met)
    if not (w and d):
        P.stop_with('the map size could not be measured - see %s/map_metrics.txt' % rd)
    for k, v in found.items():
        P.say('%-10s %s' % (k, v))
    P.say('false obstacles (phantom cells): %s; building %s x %s m' % (ph.group(1) if ph else '?', w.group(1), d.group(1)))

    P.step(4, 4, 'results, hand-over and figure')
    with open(os.path.join(wd, 'building.csv'), 'w') as f:
        f.write('width_m,depth_m,from_run\n%s,%s,%s\n' % (w.group(1), d.group(1), s['label']))
    hz = sum(v == 'SEEN' for v in found.values())
    P.append_result(wd, COLUMNS, {
        'config': s['label'], 'run': n, 'date': P.now(), 'computer': P.computer(), 'sensors': sensors,
        'camera_draws_map': draws, 'floor_height_m': floor, 'low_step': found['low_step'],
        'table_top': found['table_top'], 'hazards_found': hz, 'phantom_cells': ph.group(1) if ph else '',
        'width_m': w.group(1), 'depth_m': d.group(1), 'loop': '%s m in %s s' % m.groups()})
    P.bar_figure(wd, 'hazards_found', 'hazards found (of 2)', 'P2 Part A - mapping robot')
    P.finish(wd, 'RUN %d "%s": hazards found %d of 2 (step %s, table top %s), building %s x %s m\n'
             'Map: %s.pgm   Hand-over to Part B: %s'
             % (n, s['label'], hz, found['low_step'], found['table_top'], w.group(1), d.group(1), mp,
                os.path.join(wd, 'building.csv')))


if __name__ == '__main__':
    main()
