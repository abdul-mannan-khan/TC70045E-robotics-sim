#!/usr/bin/env python3
"""stop_test.py - how far does the robot travel after its LiDAR safety brick says "blocked"? (P5 Part A, given code)

Needs:  ros2 launch ~/labs/week02/launch/lego.launch.py gui:=true safety:=true     (the robot + the safety brick)
Run:    python3 stop_test.py --speeds 0.1 0.2 0.3 --repeats 2

For every speed: drive straight ahead (through the safety brick, on /cmd_vel_in) until /safety/blocked turns true,
keep asking for the speed until the robot has stopped, measure on the simulator's true position (/ground_truth/odom)
how far it went after the block, then back away 0.8 m and do the next one. Prints one TRIAL line per test and RESULT.
"""
import argparse
import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool


class StopTest(Node):
    def __init__(self):
        super().__init__('stop_test')
        self.pos, self.speed, self.blocked, self.scan = None, 0.0, False, None
        self.pub = self.create_publisher(Twist, '/cmd_vel_in', 10)
        self.create_subscription(Odometry, '/ground_truth/odom', self.on_odom, 10)
        self.create_subscription(Bool, '/safety/blocked', lambda m: setattr(self, 'blocked', m.data), 10)
        self.create_subscription(LaserScan, '/scan', lambda m: setattr(self, 'scan', m), 10)

    def on_odom(self, m):
        p, v = m.pose.pose.position, m.twist.twist.linear
        self.pos = (p.x, p.y)
        self.speed = math.hypot(v.x, v.y)

    def nearest_ahead(self, half_deg=35.0):
        s = self.scan
        if s is None:
            return float('nan')
        best = float('inf')
        for i, r in enumerate(s.ranges):
            a = s.angle_min + i * s.angle_increment
            if s.range_min < r < s.range_max and abs(math.atan2(math.sin(a), math.cos(a))) <= math.radians(half_deg):
                best = min(best, r)
        return best

    def drive(self, vx, seconds=0.1):
        cmd = Twist()
        cmd.linear.x = vx
        t0 = time.monotonic()
        while time.monotonic() - t0 < seconds:
            self.pub.publish(cmd)
            rclpy.spin_once(self, timeout_sec=0.02)

    def trial(self, v, timeout=40.0):
        """Drive at v until blocked and stopped. Returns (travelled after block [m], range ahead at stop [m]) or None."""
        t0 = time.monotonic()
        while not self.blocked:                       # 1 drive towards the obstacle
            self.drive(v)
            if time.monotonic() - t0 > timeout:
                return None
        at_block = self.pos
        still_since = None
        while True:                                   # 2 keep asking for the speed: the brick must hold it
            self.drive(v)
            if self.speed < 0.005:
                still_since = still_since or time.monotonic()
                if time.monotonic() - still_since > 1.0:
                    break
            else:
                still_since = None
            if time.monotonic() - t0 > timeout:
                break
        travelled = math.hypot(self.pos[0] - at_block[0], self.pos[1] - at_block[1])
        return travelled, self.nearest_ahead()

    def back_off(self, metres=0.8):
        start = self.pos
        t0 = time.monotonic()
        while math.hypot(self.pos[0] - start[0], self.pos[1] - start[1]) < metres and time.monotonic() - t0 < 15:
            self.drive(-0.15)
        self.drive(0.0, 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--speeds', type=float, nargs='+', default=[0.1, 0.2, 0.3])
    ap.add_argument('--repeats', type=int, default=2)
    a = ap.parse_args()
    rclpy.init()
    n = StopTest()
    t0 = time.monotonic()
    while (n.pos is None or n.scan is None) and time.monotonic() - t0 < 60:
        rclpy.spin_once(n, timeout_sec=0.2)
    if n.pos is None or n.scan is None:
        print('RESULT no data from the robot (/ground_truth/odom, /scan)', flush=True)
        return
    n.drive(0.0, 1.0)
    for v in a.speeds:
        for k in range(1, a.repeats + 1):
            r = n.trial(v)
            if r is None:
                print('TRIAL speed %.2f m/s run %d: never blocked within 40 s' % (v, k), flush=True)
            else:
                print('TRIAL speed %.2f m/s run %d: travelled %.3f m after the block, stopped %.3f m from the obstacle'
                      % (v, k, r[0], r[1]), flush=True)
            n.back_off()
    n.drive(0.0, 1.0)
    print('RESULT done', flush=True)
    n.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
