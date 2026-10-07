#!/usr/bin/env python3
"""Week 4, Lab B - spin the simulated robot on the spot and record the magnetometer for calibration.

Terminal 1:  ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false
Terminal 2:  python3 ~/labs/week04/inertial_sensing/scripts/mag_spin_capture.py --turns 2 --wz 0.3 --out mag_cal.csv

Publishes /cmd_vel (wz only) until the robot has turned --turns full turns, then publishes a zero Twist
(the base has no command timeout). Every /imu/mag message is written with the latest true yaw.
Columns: t [s], mx my mz [uT], yaw_true [deg] (from /ground_truth/odom - evaluation only), x y [m]
Expected: about 50 rows per second, 2 turns at 0.3 rad/s take about 42 s of simulated time.
"""
import argparse
import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import MagneticField


class MagSpin(Node):
    def __init__(self, out):
        super().__init__('mag_spin_capture', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.f = open(out, 'w')
        self.f.write('t,mx,my,mz,yaw_true,x,y\n')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(MagneticField, '/imu/mag', self.on_mag, qos_profile_sensor_data)
        self.create_subscription(Odometry, '/ground_truth/odom', self.on_truth, 20)
        self.yaw = self.yaw_prev = None
        self.turned, self.xy, self.n = 0.0, (0.0, 0.0), 0

    def on_truth(self, m):
        q = m.pose.pose.orientation
        self.yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        if self.yaw_prev is not None:
            self.turned += abs(math.atan2(math.sin(self.yaw - self.yaw_prev), math.cos(self.yaw - self.yaw_prev)))
        self.yaw_prev, self.xy = self.yaw, (m.pose.pose.position.x, m.pose.pose.position.y)

    def on_mag(self, m):
        if self.yaw is None:
            return
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        b = m.magnetic_field
        self.f.write('%.3f,%.3f,%.3f,%.3f,%.3f,%.4f,%.4f\n' % (t, b.x * 1e6, b.y * 1e6, b.z * 1e6,
                                                           math.degrees(self.yaw), *self.xy))
        self.n += 1

    def drive(self, wz):
        m = Twist()
        m.angular.z = wz
        self.pub.publish(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--turns', type=float, default=2.0)
    ap.add_argument('--wz', type=float, default=0.3, help='rad/s')
    ap.add_argument('--out', default='mag_cal.csv')
    a = ap.parse_args()
    rclpy.init()
    node = MagSpin(a.out)
    t_pub = 0.0
    try:
        while rclpy.ok() and node.turned < 2 * math.pi * a.turns:
            if time.monotonic() - t_pub > 0.05:        # command at 20 Hz
                node.drive(a.wz)
                t_pub = time.monotonic()
            rclpy.spin_once(node, timeout_sec=0.05)
    finally:
        for _ in range(5):
            node.drive(0.0)                            # ALWAYS leave the robot stopped
        node.f.close()
        print('turned %.1f deg, wrote %d magnetometer samples to %s' % (math.degrees(node.turned), node.n, a.out))
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
