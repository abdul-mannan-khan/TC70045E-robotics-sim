#!/usr/bin/env python3
"""tour.py - drive the robot on a fixed tour past the two coloured boxes, stopping to look at each (Week 6).

Steers on /ground_truth/odom (a test harness: box_finder.py and SLAM never see that topic). Route in the WORLD frame
(lab world, the robot starts at (-3.0, -0.4) facing +x):
  start -> (-0.8, -1.4), turn until the red box is 25 deg right of the image centre, look 10 s -> (2.0, -1.2)
  -> (2.4, -0.6), the same for the green box, look 10 s -> stop on the spot (the camera sweeps the room: a test for TF timing) -> stop.

Usage (normally started by perception.launch.py with tour:=true):
  python3 ~/labs/week06/scripts/tour.py --ros-args -p use_sim_time:=true
  ... -p turn_rate:=0.6     turn faster (TODO 3 shows its effect)
Expected: one log line per leg, then "tour finished" after about 130 s of simulated time.
"""
import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions

RED, GREEN = (-1.5, -2.8), (4.2, -0.8)          # world frame
# (kind, target): 'go' to a point, 'face' a point, 'look' (stand still, seconds), 'spin' (degrees)
TOUR = [('go', (-0.8, -1.4)), ('face', RED), ('look', 10.0),
        ('go', (-0.2, -1.5)), ('go', (2.0, -1.2)), ('go', (2.4, -0.6)), ('face', GREEN), ('look', 10.0)]
# (a ('spin', 360.0) leg can be added: a turn on the spot is the test case for TF timing - lecture slide 5)


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


class Tour(Node):
    def __init__(self):
        super().__init__('tour')
        self.speed = self.declare_parameter('speed', 0.15).value
        self.turn = self.declare_parameter('turn_rate', 0.3).value
        self.offset = math.radians(self.declare_parameter('look_offset_deg', 25.0).value)   # box off-centre
        self.truth, self.i, self.t_leg, self.spun, self.last_th, self.done = None, 0, None, 0.0, None, False
        self.cmd = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Odometry, '/ground_truth/odom', self.on_truth, 10)
        self.create_timer(0.05, self.step)

    def on_truth(self, m):
        p = m.pose.pose
        self.truth = (p.position.x, p.position.y, yaw_of(p.orientation))

    def next_leg(self):
        self.get_logger().info('leg %d done: %s %s' % (self.i + 1, TOUR[self.i][0], TOUR[self.i][1]))
        self.i, self.t_leg, self.spun, self.last_th = self.i + 1, None, 0.0, None
        self.cmd.publish(Twist())
        if self.i == len(TOUR):
            self.done = True
            self.get_logger().info('tour finished')

    def step(self):
        if self.truth is None or self.done:
            return
        x, y, th = self.truth
        kind, arg = TOUR[self.i]
        cmd = Twist()
        now = self.get_clock().now().nanoseconds * 1e-9
        if kind == 'go':
            d = math.hypot(arg[0] - x, arg[1] - y)
            err = wrap(math.atan2(arg[1] - y, arg[0] - x) - th)
            if d < 0.06:
                return self.next_leg()
            cmd.angular.z = max(-self.turn, min(self.turn, 1.5 * err))
            if abs(err) < 0.15:
                cmd.linear.x = self.speed * min(1.0, d / 0.4 + 0.2)
        elif kind == 'face':                          # the box ends up `look_offset_deg` right of the image centre
            err = wrap(math.atan2(arg[1] - y, arg[0] - x) + self.offset - th)
            if abs(err) < 0.03:
                return self.next_leg()
            cmd.angular.z = max(-self.turn, min(self.turn, 1.5 * err))
            if abs(cmd.angular.z) < 0.08:
                cmd.angular.z = math.copysign(0.08, err)
        elif kind == 'look':
            self.t_leg = self.t_leg or now
            if now - self.t_leg > arg:
                return self.next_leg()
        elif kind == 'spin':
            if self.last_th is not None:
                self.spun += abs(wrap(th - self.last_th))
            self.last_th = th
            if math.degrees(self.spun) >= arg:
                return self.next_leg()
            cmd.angular.z = self.turn
        self.cmd.publish(cmd)


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = Tour()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        for _ in range(5):                         # the simulated robot has no command timeout
            node.cmd.publish(Twist())
            time.sleep(0.02)
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
