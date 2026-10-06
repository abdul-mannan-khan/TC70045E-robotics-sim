#!/usr/bin/env python3
"""drive_square.py - scripted, repeatable test manoeuvres for the simulated lab robot (TC70045E Week 6).

Timing uses SIMULATED time (/clock), so distances and angles are right even if your laptop runs the
simulator slower than real time. Every pattern starts with a stationary settle period and ends with an
explicit zero Twist (the simulator has no command timeout - it keeps executing the last command).

Patterns:
  square    --side 2.0 --laps 1 --dir cw|ccw     side legs at --v, 90 deg in-place turns at --w
            (from the lab-world spawn pose use:  square --dir cw   or   square --dir ccw --pre-turn -90
             - both trace the same clear 2 m x 2 m area; ccw without the pre-turn hits the pillar)
  straight  --distance 2.0                       forward (use a negative distance to reverse)
  lateral   --distance 1.0                       sideways, +y = left (mecanum only)
  spin      --turns 2 --dir ccw|cw               in-place rotation
  arc       --radius 0.5 --angle 360 --dir ccw   drive a circular arc (v = --v, w = v / radius)

Usage:
  python3 ~/labs/week06/scripts/drive_square.py square --side 2.0 --dir cw
  python3 ~/labs/week06/scripts/drive_square.py straight --distance 2.0
  python3 ~/labs/week06/scripts/drive_square.py spin --turns 2
Expected: one log line per segment and "done - robot stopped". A 2 m square at 0.2 m/s and 0.5 rad/s
takes about 67 s of simulated time including the 5 s settle and the 1 s pauses.
"""
import argparse
import math

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist


def build(a):
    """Return the manoeuvre as a list of (duration_s, vx, vy, wz, label)."""
    turn = -1.0 if a.dir == 'cw' else 1.0
    seg = [(a.settle, 0, 0, 0, 'settle (stationary)')]
    pause = (1.0, 0, 0, 0, 'pause')
    if a.pre_turn:
        seg += [(abs(math.radians(a.pre_turn)) / a.w, 0, 0, math.copysign(a.w, a.pre_turn),
                 'pre-turn %+.0f deg' % a.pre_turn), pause]
    if a.pattern == 'square':
        for lap in range(a.laps):
            for k in range(4):
                seg += [(a.side / a.v, a.v, 0, 0, 'lap %d leg %d: %.2f m' % (lap + 1, k + 1, a.side)), pause,
                        (math.pi / 2 / a.w, 0, 0, turn * a.w, 'turn %+d deg' % (turn * 90)), pause]
    elif a.pattern == 'straight':
        seg += [(abs(a.distance) / a.v, math.copysign(a.v, a.distance), 0, 0, 'straight %.2f m' % a.distance)]
    elif a.pattern == 'lateral':
        seg += [(abs(a.distance) / a.v, 0, math.copysign(a.v, a.distance), 0, 'lateral %.2f m' % a.distance)]
    elif a.pattern == 'spin':
        seg += [(2 * math.pi * a.turns / a.w, 0, 0, turn * a.w, 'spin %.2f turns %s' % (a.turns, a.dir))]
    elif a.pattern == 'arc':
        w = a.v / a.radius
        seg += [(math.radians(a.angle) / w, a.v, 0, turn * w, 'arc r=%.2f m, %.0f deg' % (a.radius, a.angle))]
    return seg + [(2.0, 0, 0, 0, 'stop and settle')]


class Driver(Node):
    def __init__(self, segments):
        super().__init__('drive_square', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.seg, self.i, self.t0, self.done = segments, -1, None, False
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_timer(0.01, self.tick)                 # 100 Hz in simulated time

    def tick(self):
        now = self.get_clock().now().nanoseconds * 1e-9
        if now == 0.0 or self.done:                        # no /clock yet, or finished
            return
        if self.t0 is None:
            self.t0 = self.t_end = now
        while now >= self.t_end:                           # next segment (exact boundaries, no drift)
            self.i += 1
            if self.i == len(self.seg):
                for _ in range(5):
                    self.pub.publish(Twist())
                self.done = True
                self.get_logger().info('done - robot stopped (%.1f s)' % (now - self.t0))
                return
            self.t_end += self.seg[self.i][0]
            self.get_logger().info('t=%6.2f s  %s' % (now - self.t0, self.seg[self.i][4]))
        _, vx, vy, wz, _ = self.seg[self.i]
        cmd = Twist()
        cmd.linear.x, cmd.linear.y, cmd.angular.z = float(vx), float(vy), float(wz)
        self.pub.publish(cmd)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pattern', choices=['square', 'straight', 'lateral', 'spin', 'arc'])
    ap.add_argument('--side', type=float, default=2.0)
    ap.add_argument('--laps', type=int, default=1)
    ap.add_argument('--distance', type=float, default=2.0)
    ap.add_argument('--turns', type=float, default=1.0)
    ap.add_argument('--radius', type=float, default=0.5)
    ap.add_argument('--angle', type=float, default=360.0)
    ap.add_argument('--dir', choices=['cw', 'ccw'], default='cw')
    ap.add_argument('--v', type=float, default=0.2, help='linear speed, m/s')
    ap.add_argument('--w', type=float, default=0.5, help='turn rate, rad/s')
    ap.add_argument('--settle', type=float, default=5.0, help='stationary time at the start, s')
    ap.add_argument('--pre-turn', type=float, default=0.0, help='turn in place by this many degrees first')
    a = ap.parse_args()

    rclpy.init()
    node = Driver(build(a))
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.pub.publish(Twist())                          # never leave the robot moving
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
