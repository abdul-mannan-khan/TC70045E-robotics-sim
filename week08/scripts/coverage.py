#!/usr/bin/env python3
"""coverage.py - how much of the building is on the map, over time (Week 8).

Every 30 s of simulated time it prints the explored area (free + occupied cells of /map) and the distance the robot
has driven (from /ground_truth/odom - a test harness, nothing else uses it). At time_limit it prints a RESULT line.
The lab is about 80 m^2 inside its walls; the map also counts the wall cells, so a complete map is about 85 m^2.

Usage:  python3 ~/labs/week08/scripts/coverage.py --ros-args -p use_sim_time:=true -p time_limit:=600.0
"""
import math

import numpy as np
import rclpy
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.node import Node


class Coverage(Node):
    def __init__(self):
        super().__init__('coverage')
        self.limit = self.declare_parameter('time_limit', 600.0).value
        self.area, self.dist, self.last, self.t0 = 0.0, 0.0, None, None
        self.create_subscription(OccupancyGrid, '/map', self.on_map, 1)
        self.create_subscription(Odometry, '/ground_truth/odom', self.on_truth, 10)
        self.create_timer(30.0, self.report)
        self.done = False

    def on_map(self, m):
        g = np.array(m.data)
        self.area = np.count_nonzero(g >= 0) * m.info.resolution ** 2

    def on_truth(self, m):
        p = m.pose.pose.position
        if self.last:
            self.dist += math.hypot(p.x - self.last[0], p.y - self.last[1])
        self.last = (p.x, p.y)

    def report(self):
        now = self.get_clock().now().nanoseconds * 1e-9
        self.t0 = self.t0 if self.t0 is not None else now - 30.0
        t = now - self.t0
        print('t = %4.0f s   explored %5.1f m^2   driven %5.1f m' % (t, self.area, self.dist), flush=True)
        if t >= self.limit and not self.done:
            self.done = True
            print('RESULT after %.0f s: explored %.1f m^2, driven %.1f m' % (t, self.area, self.dist), flush=True)


def main():
    rclpy.init()
    node = Coverage()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
