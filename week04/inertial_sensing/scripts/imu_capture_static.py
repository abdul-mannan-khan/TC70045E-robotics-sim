#!/usr/bin/env python3
"""Week 4, Lab A - record a static IMU log from /imu/data_raw to CSV (the robot must NOT move).

Terminal 1:  ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false
Terminal 2:  python3 ~/labs/week04/inertial_sensing/scripts/imu_capture_static.py --duration 60 --out imu_60s.csv
Long run in the background (keeps going while you do Lab B; progress goes to the log file):
             nohup python3 ~/labs/week04/inertial_sensing/scripts/imu_capture_static.py --duration 600 --out imu_static.csv > cap.log 2>&1 &

Time is the message header stamp (simulated time), so a slow laptop gives the same data, only later.
Columns: t [s], gx gy gz [deg/s], ax ay az [m/s^2] - the same layout as the imu_noise_model output,
so allan_deviation.py reads both. Expected: about 100 samples per simulated second.
"""
import argparse
import math

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu


class Capture(Node):
    def __init__(self, out, duration):
        super().__init__('imu_capture_static', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.f = open(out, 'w')
        self.f.write('t,gx,gy,gz,ax,ay,az\n')
        self.duration, self.t0, self.n, self.next_report = duration, None, 0, 60.0
        self.create_subscription(Imu, '/imu/data_raw', self.on_imu, qos_profile_sensor_data)

    def on_imu(self, m):
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        self.t0 = t if self.t0 is None else self.t0
        w, a, k = m.angular_velocity, m.linear_acceleration, 180.0 / math.pi
        self.f.write('%.4f,%.6f,%.6f,%.6f,%.5f,%.5f,%.5f\n'
                     % (t - self.t0, w.x * k, w.y * k, w.z * k, a.x, a.y, a.z))
        self.n += 1
        if t - self.t0 >= self.next_report:
            print('%4.0f s recorded, %d samples' % (t - self.t0, self.n), flush=True)
            self.next_report += 60.0

    def done(self):
        return self.t0 is not None and self.get_clock().now().nanoseconds * 1e-9 - self.t0 >= self.duration


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--duration', type=float, default=60.0, help='simulated seconds to record')
    ap.add_argument('--out', default='imu_static.csv')
    a = ap.parse_args()
    rclpy.init()
    node = Capture(a.out, a.duration)
    try:
        while rclpy.ok() and not node.done():
            rclpy.spin_once(node, timeout_sec=0.5)
    except KeyboardInterrupt:
        pass
    node.f.close()
    print('wrote %d samples to %s' % (node.n, a.out))
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
