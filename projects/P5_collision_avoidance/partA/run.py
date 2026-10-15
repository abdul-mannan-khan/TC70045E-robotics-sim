#!/usr/bin/env python3
"""P5 Collision avoidance - Part A: the robot that cannot crash.
Run:  python3 ~/labs/projects/P5_collision_avoidance/partA/run.py

Starts the robot with its LiDAR safety brick (Gazebo + RViz), drives it straight at an obstacle at each speed, and
measures how far inside the stop distance it ends up (the brick reacts only when a new laser scan arrives, 5.5 times
a second). From that it fits your safety rule:
    overshoot into the stop distance = reaction time x speed
Writes ~/work/P5/partA/results.csv, figure.png, run_NN_<label>/ (with rule_plot.png) and safety_rule.csv -
the HAND-OVER to Part B: the car's emergency brake uses your measured reaction time.
"""
import os
import re
import sys

sys.path.insert(0, os.path.expanduser('~/labs/projects/tools'))
import projlib as P   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
COLUMNS = ['config', 'run', 'date', 'computer', 'stop_distance_m', 'trials', 'overshoot_by_speed',
           'closest_to_obstacle_m', 'reaction_time_s', 'notes']


def rule_plot(points, tr, out_png, title):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return
    fig, ax = plt.subplots(figsize=(5, 3.6))
    ax.plot([p[0] for p in points], [100 * p[1] for p in points], 'o', label='measured')
    vmax = max(p[0] for p in points) * 1.1
    ax.plot([0, vmax], [0, 100 * tr * vmax], '-', label='rule: %.2f s x speed' % tr)
    ax.set_xlabel('speed [m/s]')
    ax.set_ylabel('overshoot into the stop distance [cm]')
    ax.set_title(title, fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.text(0.99, 0.02, 'simulated', transform=ax.transAxes, ha='right', va='bottom', fontsize=8, color='0.4')
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


def main():
    s = P.load_settings(os.path.join(HERE, 'settings.yaml'), ['label', 'stop_distance', 'speeds', 'repeats'])
    speeds = [float(v) for v in s['speeds']]
    if max(speeds) > 0.5 or min(speeds) <= 0:
        P.stop_with('speeds must be between 0.05 and 0.5 m/s')
    wd = P.workdir('P5', 'partA')
    n, rd = P.new_run_dir(wd, s['label'])
    P.say('run %d "%s": stop distance %s m, speeds %s, %s repeats' % (n, s['label'], s['stop_distance'], speeds, s['repeats']))

    P.step(1, 3, 'start the robot and its safety brick (about 1 minute)')
    sim, ok = P.robot_launch('ros2 launch ~/labs/week02/launch/lego.launch.py gui:=true safety:=true',
                             os.path.join(rd, 'robot.log'), r'safety_stop: /cmd_vel_in', 240, 'the safety brick')
    if not ok:
        P.clean_robot_sim()
        P.stop_with('the robot did not start - see %s/robot.log, then run again' % rd)
    P.time.sleep(15)                                   # let Gazebo and the laser settle
    P.run('ros2 param set /safety_stop stop_distance %s' % s['stop_distance'], os.path.join(rd, 'param.log'), 60)
    P.say('safety brick ready, stop distance %s m' % s['stop_distance'])

    P.step(2, 3, 'the stopping test - watch Gazebo: the robot drives at the obstacle, stops, backs off, again')
    log = os.path.join(rd, 'stop_test.log')
    t = P.start('python3 -u %s --speeds %s --repeats %d' % (os.path.join(HERE, 'stop_test.py'),
                                                              ' '.join(str(v) for v in speeds), int(s['repeats'])), log)
    P.wait_for(log, r'RESULT .*', 120 + 60 * len(speeds) * int(s['repeats']), t, what='the stopping test')
    P.stop(t)
    P.clean_robot_sim()
    out = P.read(log)
    sd = float(s['stop_distance'])
    trials = [(float(v), max(0.0, sd - float(c)), float(c)) for v, d, c in
              re.findall(r'TRIAL speed ([\d.]+) m/s run \d+: travelled ([\d.]+) m after the block, stopped ([\d.]+) m', out)]
    for v, d, c in trials:
        P.say('speed %.2f m/s: stopped %.2f m from the obstacle - %.1f cm inside the %.2f m stop distance'
              % (v, c, 100 * d, sd))
    if not trials:
        P.stop_with('no trial finished - see %s/stop_test.log' % rd)

    P.step(3, 3, 'your safety rule, results and figure')
    tr = sum(v * d for v, d, _ in trials) / sum(v * v for v, d, _ in trials)   # least squares through 0: overshoot = tr * v
    by = {}
    for v, d, _ in trials:
        by.setdefault(v, []).append(d)
    with open(os.path.join(wd, 'safety_rule.csv'), 'w') as f:
        f.write('reaction_time_s,stop_distance_m,from_run\n%.3f,%s,%s\n' % (tr, s['stop_distance'], s['label']))
    rule_plot([(v, d) for v, d, _ in trials], tr, os.path.join(rd, 'rule_plot.png'),
              'safety rule - %s' % s['label'])
    P.append_result(wd, COLUMNS, {
        'config': s['label'], 'run': n, 'date': P.now(), 'computer': P.computer(), 'stop_distance_m': s['stop_distance'],
        'trials': len(trials),
        'overshoot_by_speed': '; '.join('%.2f m/s: %.1f cm' % (v, 100 * sum(ds) / len(ds)) for v, ds in by.items()),
        'closest_to_obstacle_m': '%.3f' % min(c for _, _, c in trials), 'reaction_time_s': '%.3f' % tr})
    P.bar_figure(wd, 'reaction_time_s', 'reaction time of the safety stop [s]', 'P5 Part A - safety stop')
    P.finish(wd, 'RUN %d "%s": your rule - overshoot = %.2f s x speed (reaction time %.2f s); closest %.2f m\n'
             'Rule plot: %s\nSafety rule (hand-over to Part B): %s'
             % (n, s['label'], tr, tr, min(c for _, _, c in trials), os.path.join(rd, 'rule_plot.png'),
                os.path.join(wd, 'safety_rule.csv')))


if __name__ == '__main__':
    main()
