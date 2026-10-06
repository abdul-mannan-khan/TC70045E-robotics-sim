#!/usr/bin/env python3
"""Safety-stop brick: passes drive commands through, but blocks motion towards a nearby obstacle.

Purpose  Week 2, Activity 4 - the first brick you add to the robot yourself. It sits BETWEEN whatever produces
         drive commands (keyboard, wander.py, Nav2) and the robot, so every other brick becomes safer for free.
Usage    python3 ~/labs/week02/scripts/safety_stop.py
         ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_in
         ros2 param set /safety_stop stop_distance 0.6        # change it while it runs
Brick    in   /cmd_vel_in  geometry_msgs/msg/Twist    the wanted motion
         in   /scan        sensor_msgs/msg/LaserScan  the 2D LiDAR
         out  /cmd_vel     geometry_msgs/msg/Twist    the allowed motion (to the robot)
         out  /safety/blocked  std_msgs/msg/Bool       true while it is holding the robot back
Rule     look at the laser rays within +/- `half_angle_deg` of the direction the robot wants to move (the base is
         holonomic, so that can be sideways). If the nearest one is closer than `stop_distance`, remove the
         translation and keep only the rotation, so the robot can still turn away.
         The check runs 20 times a second on the LAST command, not only when a new one arrives: a keyboard sends
         one message per key press, and the robot keeps driving on that one message.
"""
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool


class SafetyStop(Node):
    def __init__(self):
        super().__init__('safety_stop')
        self.declare_parameter('stop_distance', 0.45)   # metres from the LiDAR (the body reaches ~0.17 m)
        self.declare_parameter('half_angle_deg', 35.0)  # width of the checked sector, each side
        self.scan = None
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.blocked_pub = self.create_publisher(Bool, '/safety/blocked', 10)
        self.create_subscription(LaserScan, '/scan', self.on_scan, qos_profile_sensor_data)
        self.create_subscription(Twist, '/cmd_vel_in', self.on_cmd, 10)
        self.create_timer(0.05, self.check)              # re-check the last command at 20 Hz
        self.cmd = None
        self.was_blocked = False
        self.get_logger().info('safety_stop: /cmd_vel_in -> /cmd_vel, guarded by /scan')

    def on_scan(self, msg):
        self.scan = msg

    def nearest_towards(self, heading):
        """Nearest valid range within the sector centred on `heading` (rad, robot frame)."""
        s = self.scan
        half = math.radians(self.get_parameter('half_angle_deg').value)
        nearest = float('inf')
        for i, r in enumerate(s.ranges):
            if not (s.range_min < r < s.range_max):
                continue
            a = s.angle_min + i * s.angle_increment
            if abs(math.atan2(math.sin(a - heading), math.cos(a - heading))) <= half:
                nearest = min(nearest, r)
        return nearest

    def on_cmd(self, cmd):
        self.cmd = cmd                                   # remember what is wanted ...
        self.check()                                     # ... and act on it at once

    def check(self):
        cmd = self.cmd
        if cmd is None:
            return
        out = Twist()
        out.angular.z = cmd.angular.z
        out.linear.x, out.linear.y = cmd.linear.x, cmd.linear.y
        speed = math.hypot(cmd.linear.x, cmd.linear.y)
        blocked = False
        if speed > 1e-3:
            if self.scan is None:
                blocked = True                                   # no LiDAR yet: do not move blind
            else:
                heading = math.atan2(cmd.linear.y, cmd.linear.x)
                blocked = self.nearest_towards(heading) < self.get_parameter('stop_distance').value
        if blocked:
            out.linear.x = out.linear.y = 0.0
        if blocked != self.was_blocked:
            self.get_logger().warn('BLOCKED - obstacle ahead' if blocked else 'clear')
            self.was_blocked = blocked
        self.pub.publish(out)
        self.blocked_pub.publish(Bool(data=blocked))


def main():
    rclpy.init()
    node = SafetyStop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.pub.publish(Twist())                                # leave the robot stopped
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
