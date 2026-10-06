#!/usr/bin/env python3
"""Wander brick: a very simple 'brain' that drives forward and turns away from walls.

Purpose  Week 2, Activity 5 - a behaviour brick. On its own it is not very clever; snapped together with the
         safety brick and the mapping brick it becomes an exploring robot that draws a map by itself.
Usage    python3 ~/labs/week02/scripts/wander.py                          # publishes /cmd_vel directly
         python3 ~/labs/week02/scripts/wander.py --ros-args -r cmd_vel:=cmd_vel_in   # through safety_stop.py
Brick    in   /scan     sensor_msgs/msg/LaserScan
         out  cmd_vel   geometry_msgs/msg/Twist   (relative name, so it can be remapped)
Rule     two states. FORWARD: drive at `speed` while the front sector (+/-30 deg) is clearer than `turn_distance`.
         TURN: rotate on the spot towards the side with more space until the front is clearer than
         `clear_distance`, then go FORWARD again.
"""
import math
import random

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan


def sector_min(scan, centre_deg, half_deg):
    lo, hi = math.radians(centre_deg - half_deg), math.radians(centre_deg + half_deg)
    best = float('inf')
    for i, r in enumerate(scan.ranges):
        a = scan.angle_min + i * scan.angle_increment
        if lo <= a <= hi and scan.range_min < r < scan.range_max:
            best = min(best, r)
    return best


class Wander(Node):
    def __init__(self):
        super().__init__('wander')
        self.declare_parameter('speed', 0.25)           # m/s forward
        self.declare_parameter('turn_rate', 0.8)        # rad/s when turning
        self.declare_parameter('turn_distance', 0.7)    # start turning when the front is closer than this
        self.declare_parameter('clear_distance', 1.2)   # stop turning when the front is clearer than this
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_subscription(LaserScan, '/scan', self.on_scan, qos_profile_sensor_data)
        self.state, self.turn_dir = 'FORWARD', 1.0

    def on_scan(self, scan):
        front = sector_min(scan, 0.0, 30.0)
        cmd = Twist()
        if self.state == 'FORWARD':
            if front < self.get_parameter('turn_distance').value:
                left, right = sector_min(scan, 60.0, 30.0), sector_min(scan, -60.0, 30.0)
                self.turn_dir = 1.0 if left > right else -1.0
                if random.random() < 0.2:                       # sometimes the other way: explores more
                    self.turn_dir = -self.turn_dir
                self.state = 'TURN'
            else:
                cmd.linear.x = self.get_parameter('speed').value
        if self.state == 'TURN':
            if front > self.get_parameter('clear_distance').value:
                self.state = 'FORWARD'
            else:
                cmd.angular.z = self.turn_dir * self.get_parameter('turn_rate').value
        self.pub.publish(cmd)


def main():
    rclpy.init()
    node = Wander()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.pub.publish(Twist())                                # stop: the robot keeps its last command
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
