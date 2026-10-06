#!/usr/bin/env python3
"""SOLUTION - Week 2, Activity 5 option C: my_brick.py turned into a right-hand wall follower.

Run    ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true safety:=true
       python3 ~/labs/solutions/week02/wall_follower.py
Brick  in   /scan      sensor_msgs/msg/LaserScan
       out  cmd_vel    geometry_msgs/msg/Twist   (published to /cmd_vel_in, so the safety brick still guards it)
Idea   keep the wall on the right at `wall_distance`: turn towards it when too far, away when too close,
       and turn left on the spot when something is straight ahead (an inside corner).
       The wall distance also uses the front-right diagonal, so a corner is seen BEFORE the robot reaches it
       (the LiDAR only updates 5.5 times a second), and a lost wall (outside corner) gives a gentle right arc.
"""
import math

import rclpy
from rclpy.signals import SignalHandlerOptions
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
        self.declare_parameter('kp', 1.5)              # rad/s per metre of error
        self.pub = self.create_publisher(Twist, '/cmd_vel_in', 10)
        self.create_subscription(LaserScan, '/scan', self.on_scan, qos_profile_sensor_data)

    def on_scan(self, scan):
        right = sector_min(scan, -90.0, 15.0)
        diagonal = sector_min(scan, -45.0, 15.0) * math.cos(math.radians(45.0))   # same wall, seen ahead
        front = sector_min(scan, 0.0, 30.0)
        wall = min(right, diagonal)
        cmd = Twist()
        target = self.get_parameter('wall_distance').value
        if front < target + 0.25:                      # corner or obstacle ahead: turn left on the spot
            cmd.angular.z = 0.6
        elif wall > 1.5:                               # no wall on the right (outside corner): arc to the right
            cmd.linear.x = self.get_parameter('speed').value
            cmd.angular.z = -0.4
        else:
            error = wall - target                      # > 0: too far from the wall
            cmd.linear.x = self.get_parameter('speed').value
            cmd.angular.z = max(-0.8, min(0.8, -self.get_parameter('kp').value * error))
        self.pub.publish(cmd)


def main():
    # Handle Ctrl+C ourselves, so ROS 2 is still running when the final stop command is sent.
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
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
