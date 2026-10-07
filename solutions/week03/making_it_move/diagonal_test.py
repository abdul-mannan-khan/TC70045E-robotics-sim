#!/usr/bin/env python3
"""SOLUTION - Week 3, Activity 5: a new acceptance test (diagonal move and a 1 m square), reusing motion_test.py.

Run    (robot + correctly configured base_driver running, as in Activity 3)
       ros2 service call /reset_world std_srvs/srv/Empty
       python3 ~/labs/solutions/week03/making_it_move/diagonal_test.py
Tests  square    four 1 m sides, no turning   expect to end within 0.10 m of the start (run it from the start pose:
                 the route is clear of the crate and the pillar)
       diagonal  vx = vy = 0.14 m/s for 5 s   expect 0.70 m ahead and 0.70 m left
"""
import math
import os
import sys

import rclpy

sys.path.insert(0, os.path.expanduser('~/labs/week03/making_it_move/scripts'))
from motion_test import MotionTest  # noqa: E402  (the helper class from the activity file)


def main():
    rclpy.init()
    n = MotionTest()
    n.wait_ready()
    rows = []
    try:
        start = n.pose
        for vx, vy in [(0.2, 0.0), (0.0, 0.2), (-0.2, 0.0), (0.0, -0.2)]:   # 1 m each side
            n.drive(vx, vy, 0.0, 5.0)
            n.settle()
        a, l, t = n.relative(start)
        gap = math.hypot(a, l)
        rows.append(('square', 'back within 0.10 m', 'ended %.2f m from the start, turn %+.0f deg' % (gap, t), gap < 0.10))
        start = n.pose
        n.drive(0.14, 0.14, 0.0, 5.0)
        n.settle()
        a, l, t = n.relative(start)
        ok = abs(a - 0.7) < 0.07 and abs(l - 0.7) < 0.07 and abs(t) < 10
        rows.append(('diagonal', '0.70 m ahead, 0.70 m left', 'ahead %+.2f, left %+.2f, turn %+.0f deg' % (a, l, t), ok))

    finally:
        from geometry_msgs.msg import Twist
        n.direct.publish(Twist())
        n.pub.publish(Twist())
    print('\n%-9s %-28s %-42s %s' % ('TEST', 'EXPECTED', 'MEASURED (ground truth)', 'RESULT'))
    for name, exp, got, ok in rows:
        print('%-9s %-28s %-42s %s' % (name, exp, got, 'PASS' if ok else 'FAIL'))
    n.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
