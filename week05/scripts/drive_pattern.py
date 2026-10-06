#!/usr/bin/env python3
"""drive_pattern.py - drive the simulated lab robot through the Week 5 scripted manoeuvre (about 55 s).

TC70045E Week 5, Laboratory C. Timing uses SIMULATED time, so the distances are right even when your
laptop runs the simulator slower than real time. The path is closed: the robot ends where it started.

  0-10 s  stationary (gyro bias and noise window)
  then 4 x [forward 1.0 m at 0.2 m/s, rotate +90 deg at 0.5 rad/s]   - a 1 m square, anticlockwise
  then lateral 0.5 m left and 0.5 m right at 0.15 m/s (mecanum only)
  then 5 s stationary, then a zero Twist (the simulator keeps executing the last command!)

Usage:   python3 ~/labs/week05/scripts/drive_pattern.py
Expected output: one line per segment, e.g. "t=  10.0 s  forward 1.0 m", and "done - robot stopped".
"""
import math

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist

V, W, VY = 0.2, 0.5, 0.15
SEGMENTS = [(10.0, 0, 0, 0, 'stationary')]
for _ in range(4):
    SEGMENTS += [(1.0 / V, V, 0, 0, 'forward 1.0 m'), (1.0, 0, 0, 0, 'pause'),
                 (math.pi / 2 / W, 0, 0, W, 'rotate +90 deg'), (1.0, 0, 0, 0, 'pause')]
SEGMENTS += [(0.5 / VY, 0, VY, 0, 'lateral left 0.5 m'), (1.0, 0, 0, 0, 'pause'),
             (0.5 / VY, 0, -VY, 0, 'lateral right 0.5 m'), (5.0, 0, 0, 0, 'stationary')]


class Driver(Node):
    def __init__(self):
        super().__init__('drive_pattern', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.i, self.t0, self.done = -1, None, False
        self.create_timer(0.02, self.tick)                 # 50 Hz, simulated time

    def tick(self):
        now = self.get_clock().now().nanoseconds * 1e-9
        if now == 0.0:                                     # /clock not received yet
            return
        if self.t0 is None:
            self.t0, self.t_seg = now, now
            self.next_segment(now)
        if now - self.t_seg >= SEGMENTS[self.i][0]:
            self.t_seg += SEGMENTS[self.i][0]
            self.next_segment(now)
        if self.done:
            return
        _, vx, vy, wz, _ = SEGMENTS[self.i]
        cmd = Twist()
        cmd.linear.x, cmd.linear.y, cmd.angular.z = float(vx), float(vy), float(wz)
        self.pub.publish(cmd)

    def next_segment(self, now):
        self.i += 1
        if self.i >= len(SEGMENTS):
            for _ in range(5):
                self.pub.publish(Twist())                  # explicit stop
            self.done = True
            self.get_logger().info('done - robot stopped')
            return
        self.get_logger().info('t=%6.1f s  %s' % (now - self.t0, SEGMENTS[self.i][4]))


def main():
    rclpy.init()
    node = Driver()
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
