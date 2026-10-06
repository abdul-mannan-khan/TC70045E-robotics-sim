#!/usr/bin/env python3
"""llm_command.py - natural language -> local LLM (Ollama) -> strict JSON -> validator -> robot (Week 11, Lab C).

The model only PROPOSES a command. llm_validator.validate() decides; this node executes with fixed,
slow speeds and four interlocks:
  deadman   motion only while /deadman (std_msgs/Bool true) arrives at >= 2 Hz
  veto      forward motion blocked if the LiDAR sees anything closer than 0.40 m within +/-30 deg
  watchdog  every motion has a time budget (1.5 x nominal + 2 s); exceeded -> zero Twist
  timeout   no LLM reply within --timeout s -> rejected, robot not moved
goto uses Nav2 (NavigateToPose, map frame = the frame slam_toolbox starts in at the spawn pose).

Usage:
  python3 llm_command.py --test ~/labs/week11/params/llm_test_instructions.txt   # 20 prompts, no robot
  python3 llm_command.py --text "turn left ninety degrees"                        # one command, executed
  ros2 topic pub -r 5 /deadman std_msgs/msg/Bool "{data: true}"                    # hold the deadman
Options: --model qwen2.5:0.5b  --format schema|json  --threads 4  --host http://127.0.0.1:11434  --no-deadman
"""
import argparse
import csv
import json
import math
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_validator import PLACES, validate  # noqa: E402

SYSTEM = ('You translate ONE robot instruction into ONE JSON object and nothing else. Verbs: '
          '"stop" {}; "move" {"distance_m": metres, negative = backwards}; '
          '"turn" {"angle_deg": degrees, positive = left/anticlockwise}; '
          '"goto" {"place": one of ' + ', '.join(PLACES) + '}. '
          'Example: "go back half a metre" -> {"verb": "move", "distance_m": -0.5}. '
          'If the instruction is unclear, unsafe or not one of these, return {"verb": "stop"}.')
SCHEMA = {'type': 'object', 'required': ['verb'], 'properties': {
    'verb': {'type': 'string', 'enum': ['stop', 'move', 'turn', 'goto']},
    'distance_m': {'type': 'number'}, 'angle_deg': {'type': 'number'},
    'place': {'type': 'string', 'enum': list(PLACES)}}}


def ask_llm(text, a):
    """Return (raw reply, latency in ms); raw is None on timeout or HTTP error."""
    body = {'model': a.model, 'system': SYSTEM, 'prompt': text, 'stream': False,
            'format': SCHEMA if a.format == 'schema' else 'json',
            'options': {'temperature': 0, 'num_predict': 64, **({'num_thread': a.threads} if a.threads else {})}}
    req = urllib.request.Request(a.host + '/api/generate', json.dumps(body).encode(),
                                 {'Content-Type': 'application/json'})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=a.timeout) as r:
            raw = json.load(r)['response']
    except Exception as e:  # timeout, connection refused, bad HTTP: fail closed
        raw = None
        print('LLM error:', e)
    return raw, (time.monotonic() - t0) * 1e3


def matches(expected, ok, cmd):
    """Is the outcome what a careful human operator meant? expected: 'move 1.0', 'goto red_box', 'reject'."""
    want = expected.split()
    if want[0] == 'reject':
        return not ok or cmd['verb'] == 'stop'
    if not ok or cmd['verb'].replace('goto_xy', 'goto') != want[0]:
        return False
    if want[0] == 'goto':
        return cmd.get('place') == want[1]
    if len(want) > 1:
        got = cmd['distance_m'] if want[0] == 'move' else cmd['angle_deg']
        return abs(got - float(want[1])) <= 0.1 * abs(float(want[1]))
    return True


def batch_test(a):
    rows = []
    for line in open(os.path.expanduser(a.test)):
        if '|' not in line or line.startswith('#'):
            continue
        expected, text = (s.strip() for s in line.split('|', 1))
        for _ in range(a.repeat):
            raw, ms = ask_llm(text, a)
            parsed = raw is not None and _is_json(raw)
            ok, cmd, why = validate(raw) if raw is not None else (False, None, 'timeout')
            good = matches(expected, ok, cmd)
            rows.append([text, expected, raw, parsed, ok, why, good, round(ms)])
            print(f'{ms:6.0f} ms  {"ACCEPT" if ok else "REJECT"}  {"right" if good else "WRONG"}  '
                  f'{text!r} -> {raw}  [{why}]', flush=True)
    out = os.path.expanduser(a.csv)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['instruction', 'expected', 'raw', 'valid_json', 'accepted', 'reason', 'correct', 'ms'])
        w.writerows(rows)
    n = len(rows)
    lat = sorted(r[7] for r in rows)
    pct = lambda p: lat[min(n - 1, int(round(p / 100 * (n - 1))))]  # noqa: E731
    print(f'\n{a.model} format={a.format}: n={n}  valid JSON {sum(r[3] for r in rows)}/{n}  '
          f'accepted {sum(r[4] for r in rows)}/{n}  correct {sum(r[6] for r in rows)}/{n}  '
          f'latency p50 {pct(50)} ms p95 {pct(95)} ms max {lat[-1]} ms   -> {out}')


def _is_json(raw):
    try:
        json.loads(raw)
        return True
    except ValueError:
        return False


def run_robot(a):
    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import Odometry
    from sensor_msgs.msg import LaserScan
    from std_msgs.msg import Bool
    from rclpy.signals import SignalHandlerOptions

    V, W, SPAWN = 0.15, 0.5, (-3.0, -0.4)       # fixed speeds; world pose of the map/odom origin

    class Executor(Node):
        def __init__(self):
            super().__init__('llm_command', parameter_overrides=[
                rclpy.parameter.Parameter('use_sim_time', value=True)])
            self.cmd = self.create_publisher(Twist, '/cmd_vel', 1)
            self.create_subscription(Odometry, '/odom_raw', self.on_odom, 10)
            self.create_subscription(LaserScan, '/scan', self.on_scan, 5)
            self.create_subscription(Bool, '/deadman', self.on_deadman, 5)
            self.pose = self.job = None
            self.deadman_t, self.front = -1e9, float('inf')
            self.create_timer(0.05, self.tick)

        def on_odom(self, m):
            q = m.pose.pose.orientation
            self.pose = (m.pose.pose.position.x, m.pose.pose.position.y,
                         math.atan2(2 * q.w * q.z, 1 - 2 * q.z * q.z))

        def on_scan(self, m):                        # index 0 = -180 deg, forward = 0 deg
            r = [x for i, x in enumerate(m.ranges)
                 if abs(m.angle_min + i * m.angle_increment) <= math.radians(30) and m.range_min < x < m.range_max]
            self.front = min(r, default=float('inf'))

        def on_deadman(self, m):
            self.deadman_t = time.monotonic() if m.data else -1e9

        def start(self, c):
            t_wait = time.monotonic() + 3.0
            while self.pose is None and time.monotonic() < t_wait:   # first odometry after start-up
                time.sleep(0.05)
            if self.pose is None:
                print('REJECT: no /odom_raw - is the simulator running?', flush=True)
            if c['verb'] == 'stop' or self.pose is None:
                self.job = None
                return self.cmd.publish(Twist())
            if c['verb'] == 'goto_xy':
                return self.goto(c)
            size = c.get('distance_m') or math.radians(c['angle_deg'])
            nominal = abs(size) / (V if c['verb'] == 'move' else W)
            self.job = dict(c, x0=self.pose[0], y0=self.pose[1], yaw0=self.pose[2], done_at=abs(size),
                            deadline=time.monotonic() + 1.5 * nominal + 2.0, sign=math.copysign(1, size))

        def finish(self, why):
            self.cmd.publish(Twist())
            print('STOP:', why, flush=True)
            self.job = None

        def goto(self, c):
            from rclpy.action import ActionClient
            from nav2_msgs.action import NavigateToPose
            self.nav = getattr(self, 'nav', None) or ActionClient(self, NavigateToPose, 'navigate_to_pose')
            if not self.nav.wait_for_server(timeout_sec=2.0):
                return print('REJECT: goto needs Nav2 (navigate_to_pose server not found)', flush=True)
            g = NavigateToPose.Goal()
            g.pose.header.frame_id = 'map'
            g.pose.pose.position.x, g.pose.pose.position.y = c['x'] - SPAWN[0], c['y'] - SPAWN[1]
            g.pose.pose.orientation.w = 1.0
            self.job = dict(c, deadline=time.monotonic() + 120.0,
                            handle=self.nav.send_goal_async(g))
            print(f'Nav2 goal sent: map ({g.pose.pose.position.x:.2f}, {g.pose.pose.position.y:.2f})', flush=True)

        def tick(self):
            j = self.job
            if j is None:
                return
            if not a.no_deadman and time.monotonic() - self.deadman_t > 0.5:
                return self.abort('deadman released')
            if time.monotonic() > j['deadline']:
                return self.abort('watchdog: time budget exceeded')
            if j['verb'] == 'goto_xy':
                res = j['handle'].result()
                if res and res.get_result_async().done():
                    self.finish('Nav2 finished with status %d' % res.get_result_async().result().status)
                return
            t = Twist()
            if j['verb'] == 'move':
                if j['sign'] > 0 and self.front < 0.40:
                    return self.finish('LiDAR veto: obstacle at %.2f m' % self.front)
                done = math.hypot(self.pose[0] - j['x0'], self.pose[1] - j['y0'])
                t.linear.x = j['sign'] * V
            else:
                done = abs(math.atan2(math.sin(self.pose[2] - j['yaw0']), math.cos(self.pose[2] - j['yaw0'])))
                if j['done_at'] > math.radians(170):   # long turns: accumulate instead of wrapping
                    j['acc'] = j.get('acc', 0.0) + abs(math.atan2(math.sin(self.pose[2] - j.get('prev', j['yaw0'])),
                                                                 math.cos(self.pose[2] - j.get('prev', j['yaw0']))))
                    j['prev'], done = self.pose[2], j['acc']
                t.angular.z = j['sign'] * W
            if done >= j['done_at']:
                return self.finish(f'{j["verb"]} complete ({done:.3f} of {j["done_at"]:.3f})')
            self.cmd.publish(t)

        def abort(self, why):
            if self.job and self.job['verb'] == 'goto_xy' and self.job['handle'].result():
                self.job['handle'].result().cancel_goal_async()
            self.finish(why)

    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = Executor()
    import threading
    from rclpy.executors import SingleThreadedExecutor
    ex = SingleThreadedExecutor()
    ex.add_node(node)
    spinner = threading.Thread(target=ex.spin)
    spinner.start()
    texts = [a.text] if a.text else iter(lambda: input('instruction> '), '')
    try:
        for text in texts:
            raw, ms = ask_llm(text, a)
            ok, c, why = validate(raw) if raw is not None else (False, None, 'LLM timeout')
            print(f'{ms:.0f} ms  raw={raw}  ->  {"ACCEPT " + str(c) if ok else "REJECT: " + why}', flush=True)
            if ok:
                node.start(c)
                while node.job is not None:
                    time.sleep(0.05)
    except (KeyboardInterrupt, EOFError):
        pass
    node.finish('operator exit')
    time.sleep(0.2)
    ex.shutdown()
    spinner.join()
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='qwen2.5:0.5b')
    ap.add_argument('--format', choices=['schema', 'json'], default='schema')
    ap.add_argument('--host', default=os.environ.get('OLLAMA_HOST_URL', 'http://127.0.0.1:11434'))
    ap.add_argument('--timeout', type=float, default=15.0)
    ap.add_argument('--threads', type=int, default=0, help='CPU threads for the model (0 = Ollama default)')
    ap.add_argument('--test', help='file of "expected | instruction" lines: evaluate without the robot')
    ap.add_argument('--repeat', type=int, default=1)
    ap.add_argument('--csv', default='~/labs/week11/data/llm_test.csv')
    ap.add_argument('--text', help='one instruction to execute (otherwise interactive)')
    ap.add_argument('--no-deadman', action='store_true', help='simulation only: skip the deadman interlock')
    a = ap.parse_args()
    batch_test(a) if a.test else run_robot(a)
