#!/usr/bin/env python3
"""YOUR brick - a template to copy and change in the Week 2 build challenge.

As given it works: it reads the LiDAR and publishes the distance to the nearest obstacle, and an alarm flag.
Usage    cp ~/labs/week02/scripts/my_brick.py ~/labs/week02/scripts/alarm_brick.py     # work on a copy
         python3 ~/labs/week02/scripts/alarm_brick.py
         ros2 topic echo /nearest_obstacle
Brick    in   /scan              sensor_msgs/msg/LaserScan
         out  /nearest_obstacle  std_msgs/msg/Float32   metres
         out  /alarm             std_msgs/msg/Bool      true when something is closer than `alarm_distance`

Ideas for turning it into something new (each one is a few lines in on_scan):
  * Guard dog   - publish a Twist on cmd_vel that turns the robot to FACE the nearest obstacle
  * Wall follower - keep the right-hand wall at 0.5 m: wz = k * (0.5 - right_distance), vx = 0.2
  * Doorway counter - count how many times /alarm goes from false to true
"""
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, Float32


class MyBrick(Node):
    def __init__(self):
        super().__init__('my_brick')
        self.declare_parameter('alarm_distance', 0.8)
        # 1. INPUT studs: what the brick listens to
        self.create_subscription(LaserScan, '/scan', self.on_scan, qos_profile_sensor_data)
        # 2. OUTPUT studs: what the brick offers to other bricks
        self.nearest_pub = self.create_publisher(Float32, '/nearest_obstacle', 10)
        self.alarm_pub = self.create_publisher(Bool, '/alarm', 10)

    def on_scan(self, scan):
        # 3. The brick's job: turn the input into the output
        best_r, best_a = float('inf'), 0.0
        for i, r in enumerate(scan.ranges):
            if scan.range_min < r < scan.range_max and r < best_r:
                best_r, best_a = r, scan.angle_min + i * scan.angle_increment
        self.nearest_pub.publish(Float32(data=best_r))
        alarm = best_r < self.get_parameter('alarm_distance').value
        self.alarm_pub.publish(Bool(data=alarm))
        if alarm:
            self.get_logger().info('obstacle %.2f m at %+.0f deg' % (best_r, math.degrees(best_a)),
                                   throttle_duration_sec=1.0)


def main():
    rclpy.init()
    node = MyBrick()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
