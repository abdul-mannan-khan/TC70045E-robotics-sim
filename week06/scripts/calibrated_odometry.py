#!/usr/bin/env python3
"""calibrated_odometry.py - wheel odometry from /wheel_speeds with YOUR calibrated geometry (TC70045E Week 6).

Optional extension. The primary calibration re-runs the simulator's own wheel_odometry node with new
wheel_radius and lx_plus_ly. This script shows the same kinematics in plain Python and adds what the firmware
has no parameter for: a straight-line curvature correction (yaw_per_metre).

Subscribes to the four measured wheel speeds (sensor_msgs/JointState, rad/s, order fl fr rl rr), applies
mecanum forward kinematics with the parameters wheel_radius and lx_plus_ly, dead-reckons the pose with
Euler or midpoint integration, and publishes nav_msgs/Odometry on odom_cal (frame odom -> base_footprint,
no TF, so it never fights the simulator or the EKF for the transform). Same covariances as /odom_raw.
Parameters: wheel_radius [m], lx_plus_ly [m], yaw_per_metre [rad/m] (removes the heading drift of a
straight run caused by unequal wheel radii), integration (euler | midpoint).

Usage:
  python3 ~/labs/week06/scripts/calibrated_odometry.py --ros-args -p use_sim_time:=true \
      -p wheel_radius:=0.03789 -p lx_plus_ly:=0.18727 -p yaw_per_metre:=-0.0130
  python3 ~/labs/week06/scripts/calibrated_odometry.py --ros-args -p use_sim_time:=true \
      -p integration:=midpoint -r odom_cal:=odom_mid -r __node:=odom_mid
Expected: "calibrated odometry: r = 0.03789 m, lx+ly = 0.1873 m, yaw_per_metre = -0.0130 rad/m, euler -> /odom_cal"
and /odom_cal at 25 Hz. On a 2 m square it cut e/L from ~4.5 % (/odom_raw) to ~0.6 %.
"""
import math

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState


class CalibratedOdometry(Node):
    def __init__(self):
        super().__init__('calibrated_odometry')
        self.r = self.declare_parameter('wheel_radius', 0.0375).value
        self.L = self.declare_parameter('lx_plus_ly', 0.18).value
        self.mode = self.declare_parameter('integration', 'euler').value
        self.c = self.declare_parameter('yaw_per_metre', 0.0).value     # straight-line heading drift, rad/m
        self.x = self.y = self.th = 0.0
        self.t_last = None
        self.pub = self.create_publisher(Odometry, 'odom_cal', 10)
        self.create_subscription(JointState, 'wheel_speeds', self.on_wheels, 10)
        self.get_logger().info('calibrated odometry: r = %.5f m, lx+ly = %.4f m, yaw_per_metre = %.4f rad/m, %s -> %s'
                               % (self.r, self.L, self.c, self.mode, self.pub.topic_name))

    def on_wheels(self, js):
        t = js.header.stamp.sec + js.header.stamp.nanosec * 1e-9
        if self.t_last is None:
            self.t_last = t
            return
        dt, self.t_last = t - self.t_last, t
        w1, w2, w3, w4 = js.velocity                        # fl, fr, rl, rr  [rad/s]
        vx = self.r / 4.0 * (w1 + w2 + w3 + w4)
        vy = self.r / 4.0 * (-w1 + w2 + w3 - w4)
        wz = self.r / (4.0 * self.L) * (-w1 + w2 - w3 + w4) - self.c * vx   # unequal-radius correction
        th = self.th + 0.5 * wz * dt if self.mode == 'midpoint' else self.th
        self.x += (vx * math.cos(th) - vy * math.sin(th)) * dt
        self.y += (vx * math.sin(th) + vy * math.cos(th)) * dt
        self.th = math.atan2(math.sin(self.th + wz * dt), math.cos(self.th + wz * dt))
        self.publish(js.header.stamp, vx, vy, wz)

    def publish(self, stamp, vx, vy, wz):
        od = Odometry()
        od.header.stamp = stamp
        od.header.frame_id, od.child_frame_id = 'odom', 'base_footprint'
        od.pose.pose.position.x, od.pose.pose.position.y = self.x, self.y
        od.pose.pose.orientation.z, od.pose.pose.orientation.w = math.sin(self.th / 2), math.cos(self.th / 2)
        od.twist.twist.linear.x, od.twist.twist.linear.y, od.twist.twist.angular.z = vx, vy, wz
        pc, tc = [0.0] * 36, [0.0] * 36
        pc[0] = pc[7] = 0.01
        pc[14] = pc[21] = pc[28] = 1e6                      # z, roll, pitch: not measured
        pc[35] = 0.03
        tc[0] = tc[7] = 0.0004                              # (0.02 m/s)^2
        tc[14] = tc[21] = tc[28] = 1e6
        tc[35] = 0.0025                                     # (0.05 rad/s)^2
        od.pose.covariance, od.twist.covariance = pc, tc
        self.pub.publish(od)


def main():
    rclpy.init()
    node = CalibratedOdometry()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
