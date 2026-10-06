#!/usr/bin/env python3
"""The ROS 2 driver of a (pretend) motor-controller board you have just bought - Week 3 integration clinic.

What it stands for  Every real motor-controller board comes with a driver node and a configuration file: wheel
                    radius, wheel spacing, which motors are wired backwards, speed limits, a command timeout.
                    Get one value wrong and the robot drives wrongly. This node behaves like such a driver, so you
                    can practise finding and fixing configuration faults in simulation.
Usage    python3 ~/labs/week03/scripts/base_driver.py --ros-args --params-file ~/labs/week03/config/base_driver.yaml
Brick    in   /cmd_vel_in          geometry_msgs/msg/Twist     what you want the robot to do
         out  /cmd_vel             geometry_msgs/msg/Twist     what the wheels really make the robot do (to the sim)
         out  /driver/wheel_cmd    sensor_msgs/msg/JointState  wheel speed commands fl, fr, rl, rr [rad/s]
How the 'board' works
  1. inverse kinematics with the CONFIGURED geometry: body twist -> four wheel speeds
  2. wiring: a wheel listed in `reversed` turns the other way
  3. limit: no wheel faster than `max_wheel_speed`
  4. the wheels then move the REAL robot (true radius 0.0375 m, lx + ly = 0.18 m): forward kinematics -> /cmd_vel
  5. watchdog: no command for `cmd_timeout_s` seconds -> stop (0 disables it, as on many boards out of the box)
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState

TRUE_R, TRUE_L = 0.0375, 0.18          # the physical robot - you cannot change these
WHEELS = ['fl', 'fr', 'rl', 'rr']


def inverse(vx, vy, wz, r, L):
    return [(vx - vy - L * wz) / r, (vx + vy + L * wz) / r, (vx + vy - L * wz) / r, (vx - vy + L * wz) / r]


def forward(w, r, L):
    return (r / 4 * (w[0] + w[1] + w[2] + w[3]), r / 4 * (-w[0] + w[1] + w[2] - w[3]),
            r / (4 * L) * (-w[0] + w[1] - w[2] + w[3]))


class BaseDriver(Node):
    def __init__(self):
        super().__init__('base_driver')
        self.declare_parameter('wheel_radius', 0.0375)          # m
        self.declare_parameter('lx_plus_ly', 0.18)              # m, half wheelbase + half track
        self.declare_parameter('reversed', ['none'])            # wheels wired backwards, e.g. ['fr']
        self.declare_parameter('max_wheel_speed', 30.0)         # rad/s
        self.declare_parameter('cmd_timeout_s', 0.5)            # s, 0 = no watchdog
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.wheel_pub = self.create_publisher(JointState, '/driver/wheel_cmd', 10)
        self.create_subscription(Twist, '/cmd_vel_in', self.on_cmd, 10)
        self.last_cmd_time = None
        self.stopped = True
        self.create_timer(0.05, self.watchdog)
        g = lambda n: self.get_parameter(n).value
        self.get_logger().info('base_driver: r=%.4f m, lx+ly=%.3f m, reversed=%s, timeout=%.2f s'
                               % (g('wheel_radius'), g('lx_plus_ly'), g('reversed'), g('cmd_timeout_s')))

    def on_cmd(self, cmd):
        g = lambda n: self.get_parameter(n).value
        w = inverse(cmd.linear.x, cmd.linear.y, cmd.angular.z, g('wheel_radius'), g('lx_plus_ly'))
        rev = set(g('reversed'))
        w = [-wi if name in rev else wi for wi, name in zip(w, WHEELS)]
        wmax = g('max_wheel_speed')
        peak = max(abs(wi) for wi in w)
        if peak > wmax:                                          # scale all wheels together: keeps the direction
            w = [wi * wmax / peak for wi in w]
        js = JointState(name=WHEELS, velocity=w)
        js.header.stamp = self.get_clock().now().to_msg()
        self.wheel_pub.publish(js)
        vx, vy, wz = forward(w, TRUE_R, TRUE_L)
        out = Twist()
        out.linear.x, out.linear.y, out.angular.z = vx, vy, wz
        self.pub.publish(out)
        self.last_cmd_time = self.get_clock().now()
        self.stopped = False

    def watchdog(self):
        timeout = self.get_parameter('cmd_timeout_s').value
        if timeout <= 0.0 or self.stopped or self.last_cmd_time is None:
            return
        if (self.get_clock().now() - self.last_cmd_time).nanoseconds * 1e-9 > timeout:
            self.pub.publish(Twist())
            self.stopped = True
            self.get_logger().warn('no command for %.2f s - watchdog stopped the motors' % timeout)


def main():
    rclpy.init()
    node = BaseDriver()
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
