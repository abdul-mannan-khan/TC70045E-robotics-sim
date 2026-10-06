"""Reactive behaviours for the lab robot: /scan in, /cmd_vel out. One scan -> one decision, no memory of the map.

  avoid   drive forward at --v; if anything valid in the front sector (+/-30 deg) is closer than --d,
          stop and turn towards the side (left or right sector) with more free space until the front is clear.
  follow  hold the nearest object in the front +/-60 deg sector at distance --d (P control on range and bearing).
  guard   stay in place, turn to face the nearest object anywhere (360 deg); raise an alarm (/buzzer = True)
          while it is closer than --d.

Every range passes the validity test (finite, > 0, inside [range_min, range_max]) and every angle is wrapped
into [-180, 180) before it is compared, so sectors that straddle +/-180 deg work.
--delay adds an artificial sensor-chain latency (each scan is used --delay seconds after it arrives), so you can
reproduce the latency of a real LiDAR driver in simulation.

Usage:
    python3 ~/labs/week08/scripts/reactive.py --mode avoid --v 0.2 --d 0.5
    python3 ~/labs/week08/scripts/reactive.py --mode follow --d 0.8
    python3 ~/labs/week08/scripts/reactive.py --mode guard --d 1.0
Stop with Ctrl-C: the node then publishes a zero Twist (the simulated base has no command timeout).
Expected output (once a second):
    [avoid ] nearest front 1.84 m @  -12 deg | cmd v 0.20 w  0.00 | closest so far 0.47 m
"""
import argparse
import collections
import math
import signal

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool

ap = argparse.ArgumentParser()
ap.add_argument('--mode', choices=['avoid', 'follow', 'guard'], default='avoid')
ap.add_argument('--v', type=float, default=0.2, help='forward speed / speed limit, m/s')
ap.add_argument('--w', type=float, default=0.8, help='turn-rate limit, rad/s')
ap.add_argument('--d', type=float, default=0.5, help='response distance, m (from the LiDAR)')
ap.add_argument('--delay', type=float, default=0.0, help='extra latency added to every scan, s')
a = ap.parse_args()


def wrap_deg(x):
    return (np.asarray(x) + 180.0) % 360.0 - 180.0


def nearest(s, centre_deg, half_deg):
    """(range, angle_deg) of the closest VALID beam within +/-half_deg of centre_deg, or (inf, 0)."""
    r = np.asarray(s.ranges, dtype=np.float64)
    ang = np.degrees(s.angle_min + np.arange(r.size) * s.angle_increment)
    ok = np.isfinite(r) & (r > 0.0) & (r >= s.range_min) & (r <= s.range_max)
    ok &= np.abs(wrap_deg(ang - centre_deg)) <= half_deg
    if not ok.any():
        return math.inf, 0.0
    i = np.flatnonzero(ok)[np.argmin(r[ok])]
    return r[i], float(wrap_deg(ang[i]))


class Reactive(Node):
    def __init__(self):
        super().__init__('reactive', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.queue = collections.deque()           # (arrival time, scan): the emulated latency line
        self.turn = 0.0                            # avoid: committed turn direction (hysteresis)
        self.closest = math.inf
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.buzzer = self.create_publisher(Bool, '/buzzer', 10)
        self.create_subscription(LaserScan, '/scan', self.on_scan, qos_profile_sensor_data)
        self.create_timer(0.05, self.step)         # 20 Hz decision loop
        self.create_timer(1.0, self.report)
        self.info = 'waiting for /scan'

    def now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def on_scan(self, s):
        self.queue.append((self.now(), s))

    def latest_scan(self):
        s = None
        while self.queue and self.now() - self.queue[0][0] >= a.delay:
            s = self.queue.popleft()[1]
        return s

    def step(self):
        s = self.latest_scan()
        if s is None:
            return
        cmd = Twist()
        r_all, _ = nearest(s, 0.0, 180.0)
        self.closest = min(self.closest, r_all)
        if a.mode == 'avoid':
            r, th = nearest(s, 0.0, 30.0)
            if r < a.d or (self.turn and r < 1.2 * a.d):       # obstacle: turn on the spot
                if not self.turn:
                    left, _ = nearest(s, 60.0, 30.0)
                    right, _ = nearest(s, -60.0, 30.0)
                    self.turn = 1.0 if left > right else -1.0
                cmd.angular.z = self.turn * a.w
            else:
                self.turn = 0.0
                cmd.linear.x = a.v
        elif a.mode == 'follow':
            r, th = nearest(s, 0.0, 60.0)
            if r < 3.0:                                         # something to follow within 3 m
                cmd.linear.x = float(np.clip(0.8 * (r - a.d), -a.v, a.v))
                cmd.angular.z = float(np.clip(1.5 * math.radians(th), -a.w, a.w))
        else:                                                   # guard
            r, th = r_all, nearest(s, 0.0, 180.0)[1]
            cmd.angular.z = float(np.clip(1.5 * math.radians(th), -a.w, a.w))
            self.buzzer.publish(Bool(data=bool(r < a.d)))
            if r < a.d:
                self.get_logger().warn('ALARM: object at %.2f m (< %.2f m)' % (r, a.d), throttle_duration_sec=1.0)
        self.pub.publish(cmd)
        self.info = 'nearest %s %.2f m @ %4.0f deg | cmd v %.2f w %5.2f | closest so far %.2f m' % (
            'front' if a.mode != 'guard' else 'any', r, th, cmd.linear.x, cmd.angular.z, self.closest)

    def report(self):
        print('[%-6s] %s' % (a.mode, self.info), flush=True)


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)     # keep the context alive to send the stop
    signal.signal(signal.SIGTERM, signal.default_int_handler)      # treat `kill`/`timeout` like Ctrl-C
    node = Reactive()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    for _ in range(3):
        node.pub.publish(Twist())                                  # stop the robot
    print('stopped; closest valid range seen by the LiDAR: %.3f m' % node.closest)
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
