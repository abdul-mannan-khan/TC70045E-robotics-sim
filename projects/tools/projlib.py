"""projlib - the shared engine of the project packages (you never need to edit this file).

Each project part has a `run.py` that reads its `settings.yaml`, starts the simulator and the course programs, waits
for them, reads their result lines, and writes everything into ~/work/<project>/<part>/:
    results.csv      one row per run - open it in Excel
    figure.png       made again after every run
    run_NN_<label>/  the logs and the files of that run
"""
import csv
import datetime
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import warnings

warnings.filterwarnings('ignore')     # matplotlib's harmless Axes3D warning in the course images
ROS_ENV = ('source /opt/ros/humble/setup.bash 2>/dev/null; '
           '[ -f /opt/tc70045e_ws/install/setup.bash ] && source /opt/tc70045e_ws/install/setup.bash; '
           'export DISPLAY=${DISPLAY:-:1}; ')
HOME = os.path.expanduser('~')
LABS = os.path.expanduser('~/labs')
T0 = time.monotonic()


# ------------------------------------------------------------------------------------------------ talking to you
def say(text):
    print('[%5.0f s] %s' % (time.monotonic() - T0, text), flush=True)


def stop_with(text):
    print('\n*** STOPPED: %s\n' % text, flush=True)
    sys.exit(1)


def step(n, total, text):
    print('\n=== Step %d of %d: %s' % (n, total, text), flush=True)


# ------------------------------------------------------------------------------------------------ settings
def load_settings(path, required):
    try:
        import yaml
    except ImportError:
        stop_with('PyYAML is missing in this container (pip3 install --user pyyaml)')
    try:
        with open(path) as f:
            s = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        stop_with('settings.yaml could not be read - check the line the message names:\n%s\n'
                  'Tip: keep the spaces at the start of each line, and a space after every colon.' % e)
    for k in required:
        if k not in s:
            stop_with('settings.yaml has no line "%s:" - copy it back from settings_original.yaml' % k)
    s['label'] = str(s.get('label') or 'run').strip()
    return s


# ------------------------------------------------------------------------------------------------ folders and results
def workdir(project, part):
    d = os.path.expanduser('~/work/%s/%s' % (project, part))
    os.makedirs(d, exist_ok=True)
    return d


def new_run_dir(wd, label):
    n = 1 + sum(1 for x in os.listdir(wd) if re.match(r'run_\d\d_', x))
    d = os.path.join(wd, 'run_%02d_%s' % (n, re.sub(r'[^A-Za-z0-9_-]+', '_', label)[:40]))
    os.makedirs(d)
    return n, d


def append_result(wd, columns, row):
    path = os.path.join(wd, 'results.csv')
    new = not os.path.exists(path)
    with open(path, 'a', newline='') as f:
        w = csv.writer(f)
        if new:
            w.writerow(columns)
        w.writerow([row.get(c, '') for c in columns])
    return path


def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')


def computer():
    """What this ran on: the GPU's name (or no GPU) and the number of CPU cores."""
    try:
        gpu = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], capture_output=True,
                             text=True, timeout=10).stdout.strip().splitlines()[0]
    except Exception:
        gpu = 'no NVIDIA GPU'
    return '%s, %d CPU cores' % (gpu, os.cpu_count() or 0)


def bar_figure(wd, metric, ylabel, title):
    """figure.png: one bar per run label (the average if a label was run more than once)."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return
    path = os.path.join(wd, 'results.csv')
    with open(path, newline='') as f:
        rows = list(csv.DictReader(f))
    vals = {}
    for r in rows:
        try:
            v = float(r[metric])
        except (KeyError, ValueError, TypeError):
            continue                       # a run without this number (e.g. a NO-GO, not flown) has no bar
        vals.setdefault(r['config'], []).append(v)
    if not vals:
        return
    names = list(vals)
    means = [sum(v) / len(v) for v in vals.values()]
    fig, ax = plt.subplots(figsize=(max(4.0, 1.4 * len(names) + 1.5), 3.6))
    ax.bar(range(len(names)), means, color='#4c78a8', width=0.6)
    for i, (m, v) in enumerate(zip(means, vals.values())):
        ax.text(i, m, ' %.2f\n (n=%d)' % (m, len(v)), ha='center', va='bottom', fontsize=8)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15, ha='right', fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=10)
    ax.set_ylim(0, max(means) * 1.3 if max(means) > 0 else 1)
    ax.grid(axis='y', alpha=0.3)
    ax.text(0.99, 0.98, 'simulated', transform=ax.transAxes, ha='right', va='top', fontsize=8, color='0.4')
    fig.tight_layout()
    fig.savefig(os.path.join(wd, 'figure.png'), dpi=200)
    plt.close(fig)


# ------------------------------------------------------------------------------------------------ programs
def start(cmd, log, ros=True):
    """Start a program in the background; its output goes to the log file."""
    f = open(log, 'w')
    return subprocess.Popen(['bash', '-c', (ROS_ENV if ros else '') + cmd], stdout=f, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, start_new_session=True, cwd=HOME)   # Gazebo needs a readable cwd


def run(cmd, log=None, timeout=600, ros=True):
    """Run a program to the end and return its output (also written to the log)."""
    try:
        out = subprocess.run(['bash', '-c', (ROS_ENV if ros else '') + cmd], capture_output=True, text=True,
                             timeout=timeout, cwd=HOME).stdout
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b'').decode() if isinstance(e.stdout, bytes) else (e.stdout or '')
        out += '\n(stopped after %d s)' % timeout
    if log:
        with open(log, 'w') as f:
            f.write(out)
    return out


def stop(proc, sig=signal.SIGINT, wait=15):
    """Stop a program started with start(): first politely (Ctrl+C), then firmly."""
    if proc is None or proc.poll() is not None:
        return
    for s, w in ((sig, wait), (signal.SIGTERM, 5), (signal.SIGKILL, 2)):
        try:
            os.killpg(proc.pid, s)
        except ProcessLookupError:
            return
        try:
            proc.wait(w)
            return
        except subprocess.TimeoutExpired:
            pass


def read(log):
    try:
        with open(log, errors='replace') as f:
            return f.read()
    except FileNotFoundError:
        return ''


def wait_for(log, pattern, timeout, proc=None, every=30, what=''):
    """Wait until the regular expression appears in the log. Returns the match, or None after the timeout."""
    t0, said = time.monotonic(), time.monotonic()
    while time.monotonic() - t0 < timeout:
        m = re.search(pattern, read(log))
        if m:
            return m
        if proc is not None and proc.poll() is not None:
            return re.search(pattern, read(log))
        if time.monotonic() - said > every:
            say('still waiting%s ... (%.0f s)' % (' for ' + what if what else '', time.monotonic() - t0))
            said = time.monotonic()
        time.sleep(1)
    return None


GZ_DIED = r'process has died \[pid \d+, exit code [^,]+, cmd .gzserver'   # the simulator itself (not only its window)


def robot_launch(cmd, log, ready, timeout, what, tries=3, companion=None):
    """Start a mobile-robot launch file and wait for `ready` (a regular expression) in its log.
    Gazebo sometimes crashes while it starts (the course sheets say: stop it, start again) - this does that for you,
    up to `tries` times. `companion`: a function that starts a second program with each attempt (it is stopped and
    started again if Gazebo crashes); its process is returned as robot_launch.companion.
    Returns (process, match), or (None, None) if it never got there."""
    robot_launch.companion = None
    for k in range(1, tries + 1):
        clean_robot_sim()
        proc = start(cmd, log)
        robot_launch.companion = companion() if companion else None
        t0, said = time.monotonic(), time.monotonic()
        while time.monotonic() - t0 < timeout:
            text = read(log)
            m = re.search(ready, text)
            if m:
                return proc, m
            if re.search(GZ_DIED, text) or proc.poll() is not None:
                break
            if time.monotonic() - said > 30:
                say('still waiting for %s ... (%.0f s)' % (what, time.monotonic() - t0))
                said = time.monotonic()
            time.sleep(1)
        else:
            return None, None              # timed out without a crash: something else is wrong
        stop(robot_launch.companion)
        if k < tries:
            say('Gazebo crashed while starting (it happens) - starting again, attempt %d of %d' % (k + 1, tries))
            time.sleep(5)
    return None, None


def clean_robot_sim():
    """Stop everything the mobile-robot packages start (Gazebo, RViz, ROS 2 nodes)."""
    for pat in ('/opt/ros/humble/bin/ros2 launch', 'gzserver', 'gzclient', 'rviz2', '/opt/ros/humble/lib/',
                '/opt/tc70045e_ws/', 'labs/week0', 'labs/solutions/week0', '/work/P'):
        subprocess.run(['pkill', '-f', pat], capture_output=True)
    time.sleep(3)
    for pat in ('gzserver', 'gzclient', '/opt/ros/humble/lib/'):
        subprocess.run(['pkill', '-9', '-f', pat], capture_output=True)
    time.sleep(1)


# ------------------------------------------------------------------------------------------------ drone (AirSim + PX4)
def drone_sim_start(world, rd):
    """drone-sim stop, then start in the given world. Waits until PX4 is ready (1-3 minutes)."""
    clean_drone()
    P_out = run('drone-sim stop; drone-sim start --world %s' % world, os.path.join(rd, 'drone-sim.log'), timeout=600,
                ros=False)
    if 'ready for take-off' not in P_out:
        stop_with('the drone simulator did not start - see %s/drone-sim.log. Run again; if it fails twice, destroy '
                  'this Vast.ai machine and rent another' % rd)
    say('AirSim (%s) and PX4 are ready' % world)


def drone_bridges(rd):
    """Start the two Week 10 ROS 2 bridges; returns (airsim_bridge, px4_bridge)."""
    a = start('python3 -u ~/labs/week10/scripts/03_airsim_ros2_bridge.py', os.path.join(rd, 'airsim_bridge.log'))
    b = start('python3 -u ~/labs/week10/scripts/04_px4_ros2_bridge.py', os.path.join(rd, 'px4_bridge.log'))
    if not wait_for(os.path.join(rd, 'airsim_bridge.log'), r'AirSim bridge running', 120, a, what='the AirSim bridge'):
        stop_with('the AirSim bridge did not start - see %s/airsim_bridge.log' % rd)
    if not wait_for(os.path.join(rd, 'px4_bridge.log'), r'PX4 connected', 180, b, what='the PX4 bridge'):
        stop_with('the PX4 bridge did not connect - see %s/px4_bridge.log' % rd)
    say('ROS 2 bridges running')
    return a, b


def clean_drone():
    for pat in ('week10/scripts/0', '/work/P', 'labs/solutions/week', 'labs/week12/scripts/'):
        subprocess.run(['pkill', '-f', pat], capture_output=True)
    time.sleep(2)
    subprocess.run(['pkill', '-f', 'mavsdk/bin/mavsdk_server'], capture_output=True)   # left behind by MAVSDK programs
    time.sleep(1)


def drone_sim_stop(rd):
    clean_drone()
    run('drone-sim stop', os.path.join(rd, 'drone-sim-stop.log'), timeout=120, ros=False)


# ------------------------------------------------------------------------------------------------ CARLA
def carla_start(rd, town='Town04'):
    subprocess.run(['pkill', '-f', '/work/P'], capture_output=True)
    out = run('carla-sim stop; carla-sim start --town %s' % town, os.path.join(rd, 'carla-sim.log'), timeout=600, ros=False)
    if 'CARLA is up' not in out:
        stop_with('CARLA did not start - see %s/carla-sim.log. Run again; if it fails twice, destroy this Vast.ai '
                  'machine and rent another' % rd)
    say('CARLA (%s) is up' % town)


def carla_stop(rd):
    subprocess.run(['pkill', '-f', '/work/P'], capture_output=True)
    run('carla-sim stop', os.path.join(rd, 'carla-stop.log'), timeout=60, ros=False)


def time_figure(csv_path, out_png, panels, title):
    """One panel per entry of `panels`: (ylabel, [(column, legend), ...]) against the column t."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return
    rows = list(csv.DictReader(open(csv_path)))
    t = [float(r['t']) for r in rows]
    fig, axes = plt.subplots(len(panels), 1, sharex=True, figsize=(7, 2.2 * len(panels) + 0.6), squeeze=False)
    for ax, (ylabel, cols) in zip(axes[:, 0], panels):
        for col, legend in cols:
            ax.plot(t, [float(r[col]) for r in rows], linewidth=1.4, label=legend)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc='best')
    axes[-1, 0].set_xlabel('time [s]')
    axes[0, 0].set_title(title, fontsize=10)
    axes[0, 0].text(0.99, 0.95, 'simulated', transform=axes[0, 0].transAxes, ha='right', va='top', fontsize=8, color='0.4')
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


def photo_sharpness(paths):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from sharpness import laplacian_variance
    return [laplacian_variance(p) for p in paths]


def copy_if(src, dst_dir):
    if os.path.exists(src):
        shutil.copy(src, dst_dir)
        return True
    return False


def make_copy(src, dst, replace):
    """Copy a course program, changing the given lines (old text -> new text). Stops if a line is not found."""
    s = open(src).read()
    for old, new in replace:
        if old not in s:
            stop_with('could not find "%s" in %s - run update-labs, or ask the module leader' % (old[:50], src))
        s = s.replace(old, new, 1)
    with open(dst, 'w') as f:
        f.write(s)
    return dst


def finish(wd, rows_text):
    print('\n' + '-' * 78)
    print(rows_text)
    print('Results table : %s' % os.path.join(wd, 'results.csv'))
    print('Figure        : %s' % os.path.join(wd, 'figure.png'))
    print('-' * 78, flush=True)
