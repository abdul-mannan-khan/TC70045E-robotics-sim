"""Simulated 3-axis magnetometer (the third sensor of a 9-axis MEMS IMU) with hard- and soft-iron distortion.

Earth field for the UK (approximate): 19.5 uT horizontal pointing to magnetic north, 45 uT vertical (down).
In the simulated world magnetic north is the +y axis (ENU: x east, y north, z up).

Measured field in the sensor frame:   m = S (R^T b_world) + h + noise
  h = hard-iron offset (a constant vector from magnetised parts on the robot)
  S = soft-iron matrix (distorts the sphere into an ellipsoid)
Publishes imu/mag (sensor_msgs/MagneticField, tesla) at 50 Hz. Heading needs calibration: that is the Week 4 lab.
"""
import math
import random

import numpy as np
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import MagneticField


def quat_to_rot(q):
    x, y, z, w = q.x, q.y, q.z, q.w
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


class Magnetometer(Node):
    def __init__(self):
        super().__init__('magnetometer')
        p = self.declare_parameter
        self.b_world = np.array([0.0, p('horizontal_uT', 19.5).value, -p('vertical_uT', 45.0).value])
        self.hard = np.array(p('hard_iron_uT', [6.0, -4.0, 3.0]).value)
        self.soft = np.array(p('soft_iron', [1.08, 0.05, 0.0, 0.05, 0.94, 0.0, 0.0, 0.0, 1.0]).value).reshape(3, 3)
        self.noise = p('noise_uT', 0.3).value
        self.frame = p('frame_id', 'imu_link').value
        self.R = np.eye(3)
        self.create_subscription(Odometry, 'ground_truth/odom', self.on_truth, 20)
        self.pub = self.create_publisher(MagneticField, 'imu/mag', 10)
        self.create_timer(1.0 / p('rate_hz', 50.0).value, self.tick)

    def on_truth(self, msg):
        self.R = quat_to_rot(msg.pose.pose.orientation)

    def tick(self):
        m = self.soft @ (self.R.T @ self.b_world) + self.hard
        m = m + np.array([random.gauss(0.0, self.noise) for _ in range(3)])
        msg = MagneticField()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame
        msg.magnetic_field.x, msg.magnetic_field.y, msg.magnetic_field.z = (float(v) * 1e-6 for v in m)
        var = (self.noise * 1e-6) ** 2
        msg.magnetic_field_covariance = [var, 0.0, 0.0, 0.0, var, 0.0, 0.0, 0.0, var]
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = Magnetometer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
