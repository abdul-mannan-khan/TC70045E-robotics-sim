#!/usr/bin/env python3
"""SOLUTION - Week 2, Activity 5 option C: my_brick.py turned into a right-hand wall follower.

Run    ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true safety:=true
       python3 ~/labs/solutions/week02/wall_follower.py
Brick  in   /scan      sensor_msgs/msg/LaserScan
       out  cmd_vel    geometry_msgs/msg/Twist   (published to /cmd_vel_in, so the safety brick still guards it)
Idea   keep the wall on the right at `wall_distance`: turn towards it when too far, away when too close,
       and turn left on the spot when something is straight ahead (an inside corner).
"""
import math

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


class WallFollower(Node):
    def __init__(self):
        super().__init__('wall_follower')
        self.declare_parameter('wall_distance', 0.5)   # m, wall on the right
        self.declare_parameter('speed', 0.2)           # m/s
        self.declare_parameter('kp', 2.0)              # rad/s per metre of error
        self.pub = self.create_publisher(Twist, '/cmd_vel_in', 10)
        self.create_subscription(LaserScan, '/scan', self.on_scan, qos_profile_sensor_data)

    def on_scan(self, scan):
        right = sector_min(scan, -90.0, 20.0)
        front = sector_min(scan, 0.0, 25.0)
        cmd = Twist()
        target = self.get_parameter('wall_distance').value
        if front < target + 0.2:                       # corner ahead: turn left on the spot
            cmd.angular.z = 0.8
        else:
            error = min(right, 2.0) - target           # > 0: too far from the wall
            cmd.linear.x = self.get_parameter('speed').value
            cmd.angular.z = max(-1.0, min(1.0, -self.get_parameter('kp').value * error))
        self.pub.publish(cmd)


def main():
    rclpy.init()
    node = WallFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.pub.publish(Twist())
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
