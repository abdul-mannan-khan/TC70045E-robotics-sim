"""Simulated wheel encoders and wheel odometry for the TC70045E lab robot.

Chain modelled (the same chain as a real mecanum robot with a microcontroller motor board):
  true body twist (ground_truth/odom)
    -> inverse kinematics with the TRUE wheel radii and geometry, plus a little random slip
    -> quadrature encoders (C_rev counts per wheel revolution), counted in a 10 ms window
    -> every 40 ms (25 Hz) the 'firmware' reports wheel speeds and computes the body twist with the NOMINAL
       geometry  -> vel_raw (geometry_msgs/Twist) and wheel_speeds (sensor_msgs/JointState)
    -> first-order Euler dead reckoning -> odom_raw (nav_msgs/Odometry) and TF odom -> base_footprint

The difference between the true and the nominal geometry (radius_error_pct, track_error_pct) is a
SYSTEMATIC error: odometry drifts in a repeatable way, which is what Week 6 measures, calibrates and fuses.
Calibrate by setting the NOMINAL parameters wheel_radius and lx_plus_ly to your measured values; the true
geometry (true_wheel_radius, true_lx_plus_ly and the per-wheel errors) is the simulated hardware and stays fixed.

Wheel order: fl, fr, rl, rr.  Kinematics (rollers at 45 deg, L = lx + ly):
  w_fl = (vx - vy - L wz)/r   w_fr = (vx + vy + L wz)/r   w_rl = (vx + vy - L wz)/r   w_rr = (vx - vy + L wz)/r
  vx = r/4 (w_fl + w_fr + w_rl + w_rr), vy = r/4 (-w_fl + w_fr + w_rl - w_rr), wz = r/(4L) (-w_fl + w_fr - w_rl + w_rr)
"""
import math
import random

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster

WHEELS = ['fl', 'fr', 'rl', 'rr']


def inverse(vx, vy, wz, r, L):
    return [(vx - vy - L * wz) / r[0], (vx + vy + L * wz) / r[1],
            (vx + vy - L * wz) / r[2], (vx - vy + L * wz) / r[3]]


def forward(w, r, L):
    vx = r / 4.0 * (w[0] + w[1] + w[2] + w[3])
    vy = r / 4.0 * (-w[0] + w[1] + w[2] - w[3])
    wz = r / (4.0 * L) * (-w[0] + w[1] - w[2] + w[3])
    return vx, vy, wz


class WheelOdometry(Node):
    def __init__(self):
        super().__init__('wheel_odometry')
        p = self.declare_parameter
        # NOMINAL geometry = what the 'firmware' believes (change these to calibrate the odometry)
        self.r_nom = p('wheel_radius', 0.0375).value
        self.L_nom = p('lx_plus_ly', 0.18).value
        # TRUE geometry of the simulated robot (the errors below are applied to these, not to the nominal values)
        r_true_base = p('true_wheel_radius', 0.0375).value
        L_true_base = p('true_lx_plus_ly', 0.18).value
        self.c_rev = p('counts_per_rev', 2464).value
        self.window = p('encoder_window_s', 0.010).value
        self.report = p('report_period_s', 0.040).value
        rad_err = p('radius_error_pct', [0.8, 1.2, 0.9, 1.1]).value      # true radius = nominal x (1 + e/100)
        trk_err = p('track_error_pct', 4.0).value                          # effective L in turns (roller slip)
        self.slip_sd = p('slip_noise', 0.01).value                         # relative random wheel-speed noise
        self.integration = p('integration', 'euler').value                 # 'euler' or 'midpoint'
        self.publish_tf = p('publish_tf', True).value
        self.prefix = p('frame_prefix', '').value
        self.r_true = [r_true_base * (1.0 + e / 100.0) for e in rad_err]
        self.L_true = L_true_base * (1.0 + trk_err / 100.0)

        self.twist = (0.0, 0.0, 0.0)
        self.angle = [0.0] * 4          # true wheel angles [rad]
        self.counts = [0] * 4           # encoder counters
        self.prev_counts = [0] * 4
        self.speed_window = [0.0] * 4
        self.x = self.y = self.th = 0.0
        self.last_report = None

        self.create_subscription(Odometry, 'ground_truth/odom', self.on_truth, 20)
        self.pub_vel = self.create_publisher(Twist, 'vel_raw', 10)
        self.pub_odom = self.create_publisher(Odometry, 'odom_raw', 10)
        self.pub_js = self.create_publisher(JointState, 'wheel_speeds', 10)
        self.tf = TransformBroadcaster(self) if self.publish_tf else None
        self.create_timer(self.window, self.on_encoder_tick)
        self.get_logger().info('wheel odometry: C_rev=%d, window %.0f ms, report %.0f ms, radius error %s %%, '
                               'track error %.1f %%' % (self.c_rev, self.window * 1e3, self.report * 1e3,
                                                        rad_err, trk_err))

    def on_truth(self, msg):
        t = msg.twist.twist
        self.twist = (t.linear.x, t.linear.y, t.angular.z)

    def on_encoder_tick(self):
        # 1) the wheels turn according to the true geometry (+ random slip)
        w_true = inverse(*self.twist, self.r_true, self.L_true)
        for i in range(4):
            w = w_true[i] * (1.0 + random.gauss(0.0, self.slip_sd))
            self.angle[i] += w * self.window
            self.counts[i] = math.floor(self.angle[i] * self.c_rev / (2.0 * math.pi))
        # 2) M-method speed over the 10 ms window (quantised to 2*pi/(C_rev*Ts))
        self.speed_window = [(self.counts[i] - self.prev_counts[i]) * 2.0 * math.pi / (self.c_rev * self.window)
                             for i in range(4)]
        self.prev_counts = list(self.counts)
        now = self.get_clock().now()
        if self.last_report is None:
            self.last_report = now
            return
        dt = (now - self.last_report).nanoseconds * 1e-9
        if dt + 1e-4 < self.report:
            return
        self.last_report = now
        self.publish(now, dt)

    def publish(self, now, dt):
        w = self.speed_window
        vx, vy, wz = forward(w, self.r_nom, self.L_nom)
        th = self.th + 0.5 * wz * dt if self.integration == 'midpoint' else self.th
        self.x += (vx * math.cos(th) - vy * math.sin(th)) * dt
        self.y += (vx * math.sin(th) + vy * math.cos(th)) * dt
        self.th = math.atan2(math.sin(self.th + wz * dt), math.cos(self.th + wz * dt))

        stamp = now.to_msg()
        js = JointState()
        js.header.stamp = stamp
        js.name = [self.prefix + 'wheel_' + n + '_joint' for n in WHEELS]
        js.position = [c * 2.0 * math.pi / self.c_rev for c in self.counts]
        js.velocity = list(w)
        self.pub_js.publish(js)

        tw = Twist()
        tw.linear.x, tw.linear.y, tw.angular.z = vx, vy, wz
        self.pub_vel.publish(tw)

        od = Odometry()
        od.header.stamp = stamp
        od.header.frame_id = self.prefix + 'odom'
        od.child_frame_id = self.prefix + 'base_footprint'
        od.pose.pose.position.x, od.pose.pose.position.y = self.x, self.y
        od.pose.pose.orientation.z = math.sin(self.th / 2.0)
        od.pose.pose.orientation.w = math.cos(self.th / 2.0)
        od.twist.twist = tw
        pc = [0.0] * 36
        pc[0] = pc[7] = 0.01
        pc[14] = pc[21] = pc[28] = 1e6          # z, roll, pitch: not measured
        pc[35] = 0.03
        od.pose.covariance = pc
        tc = [0.0] * 36
        tc[0] = tc[7] = 0.0004                  # (0.02 m/s)^2
        tc[14] = tc[21] = tc[28] = 1e6
        tc[35] = 0.0025                         # (0.05 rad/s)^2
        od.twist.covariance = tc
        self.pub_odom.publish(od)

        if self.tf:
            t = TransformStamped()
            t.header = od.header
            t.child_frame_id = od.child_frame_id
            t.transform.translation.x, t.transform.translation.y = self.x, self.y
            t.transform.rotation = od.pose.pose.orientation
            self.tf.sendTransform(t)


def main():
    rclpy.init()
    node = WheelOdometry()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
