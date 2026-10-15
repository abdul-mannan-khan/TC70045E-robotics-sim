#!/usr/bin/env python3
"""P4 Driverless shuttle - Part A: the robot shuttle. Run:  python3 ~/labs/projects/P4_driverless_shuttle/partA/run.py

The shuttle drives its 24 m circuit through the building by itself. While it drives, three estimates of where it is
are compared with the truth: wheel counting (odometry), the EKF (wheels + gyroscope, if switched on) and SLAM.
Writes ~/work/P4/partA/results.csv, figure.png, run_NN_<label>/ and timetable.csv - the HAND-OVER to Part B: the
robot's lap time, scaled down, becomes the road shuttle's drive - stop - drive timetable.
"""
import os
import re
import sys

sys.path.insert(0, os.path.expanduser('~/labs/projects/tools'))
import projlib as P   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
COLUMNS = ['config', 'run', 'date', 'computer', 'position_from', 'gyro_calibration', 'turn_speed', 'drive_s',
           'wheels_end_m', 'wheels_heading_deg', 'ekf_end_m', 'ekf_rms_m', 'ekf_heading_deg', 'slam_end_m',
           'position_error_m', 'notes']


def yes(v):
    return str(v).strip().lower() in ('yes', 'true', '1')


def main():
    s = P.load_settings(os.path.join(HERE, 'settings.yaml'),
                        ['label', 'position_from', 'gyro_calibration', 'turn_speed', 'stop_seconds'])
    src = str(s['position_from']).strip()
    configs = {'wheels': 'odom:=raw', 'ekf_as_given': 'odom:=ekf',
               'ekf': 'odom:=ekf ekf_config:=%s' % os.path.join(P.LABS, 'solutions/week05/ekf.yaml')}
    if src not in configs:
        P.stop_with('position_from must be wheels, ekf_as_given or ekf (not "%s")' % src)
    wd = P.workdir('P4', 'partA')
    n, rd = P.new_run_dir(wd, s['label'])
    P.say('run %d "%s": position from %s, gyro calibration %s, turn speed %s'
          % (n, s['label'], src, 'yes' if yes(s['gyro_calibration']) else 'no', s['turn_speed']))

    P.step(1, 3, 'start the building and the shuttle; it drives its circuit by itself (about 5 minutes)')
    cmd = ('ros2 launch ~/labs/week05/launch/fusion.launch.py drive:=true %s gyro_cal:=%s turn_rate:=%s'
           % (configs[src], 'true' if yes(s['gyro_calibration']) else 'false', s['turn_speed']))
    log = os.path.join(rd, 'shuttle.log')
    sim, ok = P.robot_launch(cmd, log, r'SLAM\s{2,}(\(not running\)|\d)', 900, 'the shuttle to finish its circuit')
    if not ok:
        P.clean_robot_sim()
        P.stop_with('the shuttle did not finish - see %s/shuttle.log, then run again' % rd)
    P.time.sleep(3)
    P.clean_robot_sim()
    out = P.read(log)

    P.step(2, 3, 'where did it think it was, against the truth?')
    drive = re.search(r'samples: \d+ at 2 Hz over ([\d.]+) s', out)

    def row(name):
        m = re.search(r'%s\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([-+\d.]+)' % name, out)
        return m.groups() if m else None
    wheels, ekf, slam = row('wheel odometry'), row('EKF'), row('SLAM')
    for name, r in (('wheels', wheels), ('EKF', ekf), ('SLAM', slam)):
        P.say('%-7s %s' % (name, 'end error %s m, RMS %s m, heading %s deg' % (r[0], r[1], r[3]) if r else 'not running'))
    if not wheels:
        P.stop_with('no result table - see %s/shuttle.log' % rd)

    P.step(3, 3, 'results, timetable and figure')
    drive_s = float(drive.group(1)) if drive else 210.0
    road_s = round(drive_s / 10.0)
    stop_s = float(s['stop_seconds'])
    with open(os.path.join(wd, 'timetable.csv'), 'w') as f:
        f.write('from_s,speed_kmh,what\n0,50,drive (robot lap %.0f s / 10)\n%d,0,stop\n%d,50,drive on\n'
                % (drive_s, road_s, road_s + stop_s))
    err = ekf[0] if (src != 'wheels' and ekf) else wheels[0]
    P.append_result(wd, COLUMNS, {
        'config': s['label'], 'run': n, 'date': P.now(), 'computer': P.computer(), 'position_from': src,
        'gyro_calibration': 'yes' if yes(s['gyro_calibration']) else 'no', 'turn_speed': s['turn_speed'],
        'drive_s': '%.0f' % drive_s, 'wheels_end_m': wheels[0], 'wheels_heading_deg': wheels[3],
        'ekf_end_m': ekf[0] if ekf else '', 'ekf_rms_m': ekf[1] if ekf else '', 'ekf_heading_deg': ekf[3] if ekf else '',
        'slam_end_m': slam[0] if slam else '', 'position_error_m': err})
    P.bar_figure(wd, 'position_error_m', 'position error at the end [m]', 'P4 Part A - robot shuttle')
    P.finish(wd, 'RUN %d "%s": position error at the end %s m (%s); lap %.0f s\n'
             'Timetable (hand-over to Part B): drive %d s, stop %d s, drive on -> %s'
             % (n, s['label'], err, src, drive_s, road_s, stop_s, os.path.join(wd, 'timetable.csv')))


if __name__ == '__main__':
    main()
