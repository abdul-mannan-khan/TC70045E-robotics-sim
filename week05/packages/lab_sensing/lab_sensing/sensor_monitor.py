#!/usr/bin/env python3
"""sensor_monitor - a software instrument for the lab robot's IMU stream (TC70045E Week 5).

Over a sliding window it measures the IMU rate and jitter twice - from the arrival time at this node
(host clock) and from the header stamps (the sensor's clock, simulated time in the simulator) - plus the
RMS acceleration and angular rate, and publishes the result as lab_interfaces/msg/SensorHealth.

Usage (after colcon build and source ~/ws/install/setup.bash):
  ros2 run lab_sensing sensor_monitor --ros-args --params-file ~/labs/week05/params/sensor_monitor_params.yaml
  ros2 topic echo /sensor_health
Expected with the simulator standing still: imu_rate_hz ~98-100, stamp_rate_hz ~100.0, accel_rms ~9.8,
gyro_rms ~0.003, healthy: true.
"""
import math
import time
from collections import deque

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from rcl_interfaces.msg import SetParametersResult

from sensor_msgs.msg import Imu
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32
from lab_interfaces.msg import SensorHealth


def mean_std(xs):
    m = sum(xs) / len(xs)
    return m, math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


class SensorMonitor(Node):
    TUNABLE = {'expected_hz': 'expected_hz', 'rate_tolerance': 'tol', 'battery_min_v': 'vmin', 'window_s': 'window_s'}

    def __init__(self):
        super().__init__('sensor_monitor')
        # ---- parameters: everything tunable is declared, nothing is hard-coded
        p = self.declare_parameter
        imu_topic = p('imu_topic', '/imu/data_raw').value
        self.window_s = float(p('window_s', 2.0).value)
        self.expected_hz = float(p('expected_hz', 100.0).value)
        self.tol = float(p('rate_tolerance', 0.10).value)       # +/- 10 per cent
        self.vmin = float(p('battery_min_v', 10.5).value)
        report_hz = float(p('report_hz', 2.0).value)

        # ---- QoS: high-rate stream, newest data wins, short queue
        sensor_qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                                history=HistoryPolicy.KEEP_LAST, depth=5,
                                durability=DurabilityPolicy.VOLATILE)
        # ---- QoS: low-rate state, must arrive, only the latest value matters
        state_qos = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                               history=HistoryPolicy.KEEP_LAST, depth=1,
                               durability=DurabilityPolicy.VOLATILE)
        # ---- QoS: the health report - a late-joining supervisor gets the last one at once
        health_qos = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                                history=HistoryPolicy.KEEP_LAST, depth=1,
                                durability=DurabilityPolicy.TRANSIENT_LOCAL)

        self.win = deque()        # (arrival [s, host clock], stamp [s], |a|, |w|)
        self.battery = float('nan')
        self.speed = 0.0
        self.create_subscription(Imu, imu_topic, self.imu_cb, sensor_qos)
        self.create_subscription(Twist, '/vel_raw', self.vel_cb, sensor_qos)
        self.create_subscription(Float32, '/voltage', self.volt_cb, state_qos)
        self.pub = self.create_publisher(SensorHealth, '/sensor_health', health_qos)
        self.create_timer(1.0 / report_hz, self.report)
        self.add_on_set_parameters_callback(self.on_set)     # without this, 'ros2 param set' changes nothing
        self.get_logger().info('monitoring %s, expecting %.1f Hz, window %.1f s'
                               % (imu_topic, self.expected_hz, self.window_s))

    def on_set(self, params):
        for prm in params:
            if prm.name == 'expected_hz' and prm.value <= 0.0:
                return SetParametersResult(successful=False, reason='expected_hz must be > 0')
            if prm.name in self.TUNABLE:
                setattr(self, self.TUNABLE[prm.name], float(prm.value))
        return SetParametersResult(successful=True)

    # ---------------------------------------------------------------- callbacks: timestamp, append, return
    def imu_cb(self, msg):
        now = time.monotonic()                     # host clock: what a consumer actually experiences
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        la, av = msg.linear_acceleration, msg.angular_velocity
        self.win.append((now, stamp, math.sqrt(la.x**2 + la.y**2 + la.z**2),
                         math.sqrt(av.x**2 + av.y**2 + av.z**2)))
        while now - self.win[0][0] > self.window_s:
            self.win.popleft()

    def vel_cb(self, msg):
        self.speed = math.hypot(msg.linear.x, msg.linear.y)

    def volt_cb(self, msg):
        self.battery = msg.data

    # ---------------------------------------------------------------- the measurement, on the timer
    def report(self):
        n = len(self.win)
        if n < 3:
            self.get_logger().warn('fewer than 3 IMU samples in the window')
            return
        arr, stp, acc, gyr = zip(*self.win)
        d_arr = [b - a for a, b in zip(arr, arr[1:])]
        d_stp = [b - a for a, b in zip(stp, stp[1:])]
        m_arr, s_arr = mean_std(d_arr)
        m_stp, s_stp = mean_std(d_stp)

        m = SensorHealth()
        m.header.stamp = self.get_clock().now().to_msg()
        m.header.frame_id = 'imu_link'
        m.imu_rate_hz = float(1.0 / m_arr) if m_arr > 0.0 else 0.0
        m.imu_jitter_ms = float(s_arr * 1e3)
        m.stamp_rate_hz = float(1.0 / m_stp) if m_stp > 0.0 else 0.0
        m.stamp_jitter_ms = float(s_stp * 1e3)
        m.accel_rms = float(math.sqrt(sum(v * v for v in acc) / n))
        m.gyro_rms = float(math.sqrt(sum(v * v for v in gyr) / n))
        m.body_speed = float(self.speed)
        m.battery_v = float(self.battery)
        m.samples = n
        m.missed = max(0, round((stp[-1] - stp[0]) * self.expected_hz) + 1 - n)
        rate_ok = abs(m.stamp_rate_hz - self.expected_hz) <= self.tol * self.expected_hz
        batt_ok = not math.isnan(m.battery_v) and m.battery_v >= self.vmin
        m.healthy = bool(rate_ok and batt_ok)
        self.pub.publish(m)
        if not m.healthy:
            self.get_logger().warn('UNHEALTHY: %.1f Hz (expected %.1f), battery %.2f V'
                                   % (m.stamp_rate_hz, self.expected_hz, m.battery_v))


def main(args=None):
    rclpy.init(args=args)
    node = SensorMonitor()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass                              # Ctrl+C or launch shutdown: exit quietly
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
