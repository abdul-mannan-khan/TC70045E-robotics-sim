#!/usr/bin/env python3
"""gyro_bias.py - the gyro calibration brick (Week 5): measure the gyro's turn-on bias while the robot stands still,
then subtract it from every sample.

Why: a MEMS gyro reads a small non-zero rate even when it is not turning (turn-on bias: a new value every time it is
powered up - in this simulation about 0.1 deg/s). Integrated over a 210 s drive that is up to ~20 deg of heading error,
so every robot and drone measures it at standstill before moving ("keep still - calibrating IMU").

  /imu/data_raw  (sensor_msgs/Imu, 100 Hz)  ->  [wait `settle_s`, then average `still_s` seconds at standstill]  ->  /imu/data_cal
  (the first seconds are skipped: the simulated robot is still settling on its wheels after it was spawned)
  until the bias is known, /imu/data_cal is not published (so nothing downstream uses an uncalibrated gyro)

Usage (normally started by fusion.launch.py with gyro_cal:=true):
  python3 ~/labs/week05/scripts/gyro_bias.py --ros-args -p use_sim_time:=true -p still_s:=8.0
Expected log:  gyro bias measured over 8.0 s (800 samples): x +0.0012  y -0.0008  z +0.0019 rad/s  (z = +0.11 deg/s)
"""
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


class GyroBias(Node):
    def __init__(self):
        super().__init__('gyro_bias')
        self.still_s = self.declare_parameter('still_s', 8.0).value
        self.settle_s = self.declare_parameter('settle_s', 3.0).value
        self.sum, self.n, self.t0, self.bias = [0.0, 0.0, 0.0], 0, None, None
        self.pub = self.create_publisher(Imu, '/imu/data_cal', 50)
        self.create_subscription(Imu, '/imu/data_raw', self.on_imu, 50)
        self.get_logger().info('keep the robot still: measuring the gyro bias for %.0f s' % (self.settle_s + self.still_s))

    def on_imu(self, m):
        w = m.angular_velocity
        if self.bias is None:
            t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            if self.t0 is None:
                self.t0 = t + self.settle_s                # start averaging after the settling time
            if t < self.t0:
                return
            self.sum = [self.sum[0] + w.x, self.sum[1] + w.y, self.sum[2] + w.z]
            self.n += 1
            if t - self.t0 >= self.still_s:
                self.bias = [s / self.n for s in self.sum]
                self.get_logger().info('gyro bias measured over %.1f s (%d samples): x %+.4f  y %+.4f  z %+.4f rad/s'
                                       '  (z = %+.2f deg/s)' % (t - self.t0, self.n, *self.bias,
                                                                math.degrees(self.bias[2])))
            return
        w.x, w.y, w.z = w.x - self.bias[0], w.y - self.bias[1], w.z - self.bias[2]
        self.pub.publish(m)


def main():
    rclpy.init()
    node = GyroBias()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
