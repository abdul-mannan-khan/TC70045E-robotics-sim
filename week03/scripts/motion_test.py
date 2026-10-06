#!/usr/bin/env python3
"""Motion acceptance test: does the robot do what it is told? Run it after every change to the drive system.

Purpose  Week 3 integration clinic. Four short tests through /cmd_vel_in (so they pass through base_driver.py),
         measured with the simulator's exact pose /ground_truth/odom (on a real robot: a tape measure).
Usage    python3 ~/labs/week03/scripts/motion_test.py            # about 25 s; needs ~1.5 m free ahead and to the left
         python3 ~/labs/week03/scripts/motion_test.py --only forward
Tests    forward   0.2 m/s for 5 s        expect 1.00 m ahead, no sideways drift, no turn
         left      0.2 m/s for 5 s        expect 1.00 m to the left (mecanum: sideways)
         rotate    0.5 rad/s for pi s     expect +90 deg on the spot
         watchdog  0.2 m/s for 1 s, then SILENCE for 2 s    expect the robot to stop by itself
PASS     distance within 10 %, drift under 0.10 m, angle within 10 deg; watchdog: < 0.05 m travelled in the silence
At the end it always sends a zero command straight to /cmd_vel, so the robot is left stopped.
"""
import argparse
import math

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


class MotionTest(Node):
    def __init__(self):
        super().__init__('motion_test', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.pub = self.create_publisher(Twist, '/cmd_vel_in', 10)
        self.direct = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pose = None
        self.create_subscription(Odometry, '/ground_truth/odom', self.on_odom, 20)

    def on_odom(self, m):
        p = m.pose.pose
        self.pose = (p.position.x, p.position.y, yaw_of(p.orientation))

    def now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def wait_ready(self):
        while rclpy.ok() and (self.pose is None or self.now() == 0.0):
            rclpy.spin_once(self, timeout_sec=0.1)

    def drive(self, vx, vy, wz, seconds, publish=True):
        """Publish (or stay silent) for `seconds` of simulated time at 20 Hz."""
        t_end = self.now() + seconds
        cmd = Twist()
        cmd.linear.x, cmd.linear.y, cmd.angular.z = vx, vy, wz
        next_pub = 0.0
        while rclpy.ok() and self.now() < t_end:
            if publish and self.now() >= next_pub:
                self.pub.publish(cmd)
                next_pub = self.now() + 0.05
            rclpy.spin_once(self, timeout_sec=0.01)

    def relative(self, start):
        """Displacement since `start`, in the robot's starting frame: ahead, left, turned (deg)."""
        dx, dy = self.pose[0] - start[0], self.pose[1] - start[1]
        c, s = math.cos(start[2]), math.sin(start[2])
        dth = math.atan2(math.sin(self.pose[2] - start[2]), math.cos(self.pose[2] - start[2]))
        return c * dx + s * dy, -s * dx + c * dy, math.degrees(dth)

    def settle(self):
        self.drive(0.0, 0.0, 0.0, 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', choices=['forward', 'left', 'rotate', 'watchdog'])
    args, _ = ap.parse_known_args()
    rclpy.init()
    n = MotionTest()
    n.wait_ready()
    rows = []
    tests = [('forward', (0.2, 0.0, 0.0), 5.0, (1.0, 0.0, 0.0)),
             ('left', (0.0, 0.2, 0.0), 5.0, (0.0, 1.0, 0.0)),
             ('rotate', (0.0, 0.0, 0.5), math.pi, (0.0, 0.0, 90.0))]
    try:
        for name, (vx, vy, wz), secs, (ea, el, et) in tests:
            if args.only and args.only != name:
                continue
            start = n.pose
            n.drive(vx, vy, wz, secs)
            n.settle()
            a, l, t = n.relative(start)
            if name == 'rotate':
                ok = abs(t - et) < 10 and math.hypot(a, l) < 0.10
                rows.append((name, 'turn %+.0f deg' % et, 'turn %+.1f deg, moved %.2f m' % (t, math.hypot(a, l)), ok))
            else:
                want, side = (a, l) if name == 'forward' else (l, a)
                ok = abs(want - 1.0) < 0.10 and abs(side) < 0.10 and abs(t) < 10
                rows.append((name, '1.00 m, no drift, no turn',
                             'ahead %+.2f m, left %+.2f m, turn %+.0f deg' % (a, l, t), ok))
        if not args.only or args.only == 'watchdog':
            n.drive(0.2, 0.0, 0.0, 1.0)
            n.drive(0.0, 0.0, 0.0, 0.5, publish=False)      # grace period for the watchdog
            start = n.pose
            n.drive(0.0, 0.0, 0.0, 1.5, publish=False)
            moved = math.hypot(*n.relative(start)[:2])
            rows.append(('watchdog', 'stops when commands stop', 'moved %.2f m in 1.5 s of silence' % moved, moved < 0.05))
    finally:
        n.direct.publish(Twist())                            # leave the robot stopped, whatever happened
        n.pub.publish(Twist())
    print('\n%-9s %-28s %-40s %s' % ('TEST', 'EXPECTED', 'MEASURED (ground truth)', 'RESULT'))
    for name, exp, got, ok in rows:
        print('%-9s %-28s %-40s %s' % (name, exp, got, 'PASS' if ok else 'FAIL'))
    print('%d of %d passed' % (sum(r[3] for r in rows), len(rows)))
    n.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
