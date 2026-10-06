"""Single-wheel motor test bench (no Gazebo needed): a brushed DC gear motor, its PWM driver and a quadrature encoder.

  command    motor/duty      std_msgs/Float32   duty cycle in per cent, -100 ... +100
  feedback   motor/speed     std_msgs/Float32   wheel surface speed in m/s, measured by the encoder (M-method, 10 ms)
             motor/speed_true std_msgs/Float32  the true speed (for checking your identification - a real bench has no such topic)
             motor/current   std_msgs/Float32   motor current in A

Plant (what you identify in the lab):
  dead zone:  |duty| below dead_zone_pct gives no torque (static friction + driver dead time)
  transport delay: dead_time_s between the command and any response
  first order:  tau dv/dt = K * u_eff - v,   with K in (m/s) per % duty and tau in seconds
  encoder:  C_rev counts per wheel revolution, counted in a 10 ms window -> speed quantum 2 pi r / (C_rev Ts)
Default values K = 0.0084 (m/s)/%, tau = 0.12 s, dead time 40 ms, dead zone 6 %, C_rev = 2464, r = 37.5 mm.
The load parameter adds a step of load torque (as a speed loss) at load_step_s seconds to test disturbance rejection.
"""
import collections
import math
import random

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float32


class MotorBench(Node):
    def __init__(self):
        super().__init__('motor_bench')
        p = self.declare_parameter
        self.K = p('gain_mps_per_pct', 0.0084).value
        self.tau = p('time_constant_s', 0.12).value
        self.dead_time = p('dead_time_s', 0.04).value
        self.dead_zone = p('dead_zone_pct', 6.0).value
        self.c_rev = p('counts_per_rev', 2464).value
        self.r = p('wheel_radius', 0.0375).value
        self.ts = p('sample_s', 0.010).value
        self.load = p('load_mps', 0.0).value
        self.load_step = p('load_step_s', -1.0).value
        self.noise = p('speed_noise_mps', 0.002).value
        self.duty = 0.0
        self.v = 0.0
        self.angle = 0.0
        self.prev_count = 0
        self.t = 0.0
        n = max(0, int(round(self.dead_time / self.ts)))
        self.delay = collections.deque([0.0] * (n + 1), maxlen=n + 1)   # oldest entry is exactly n steps old
        self.create_subscription(Float32, 'motor/duty', self.on_duty, 10)
        self.pub = self.create_publisher(Float32, 'motor/speed', 10)
        self.pub_true = self.create_publisher(Float32, 'motor/speed_true', 10)
        self.pub_i = self.create_publisher(Float32, 'motor/current', 10)
        self.create_timer(self.ts, self.step)
        self.get_logger().info('motor bench ready: publish duty (%%) on motor/duty, read motor/speed (m/s). '
                               'Speed quantum = %.4f m/s' % (2 * math.pi * self.r / (self.c_rev * self.ts)))

    def on_duty(self, msg):
        self.duty = max(-100.0, min(100.0, msg.data))

    def step(self):
        self.t += self.ts
        self.delay.append(self.duty)
        u = self.delay[0]
        u_eff = 0.0 if abs(u) < self.dead_zone else u - math.copysign(self.dead_zone, u)
        target = self.K * u_eff
        if self.load_step >= 0.0 and self.t >= self.load_step:
            target -= math.copysign(self.load, target) if target != 0.0 else 0.0
        self.v += (target - self.v) * self.ts / self.tau
        v_meas_true = self.v + random.gauss(0.0, self.noise)
        self.angle += v_meas_true / self.r * self.ts
        count = math.floor(self.angle * self.c_rev / (2 * math.pi))
        v_enc = (count - self.prev_count) * 2 * math.pi * self.r / (self.c_rev * self.ts)
        self.prev_count = count
        self.pub.publish(Float32(data=float(v_enc)))
        self.pub_true.publish(Float32(data=float(self.v)))
        self.pub_i.publish(Float32(data=float(0.15 + 1.8 * abs(u_eff) / 100.0 + 2.0 * abs(target - self.v))))


def main():
    rclpy.init()
    node = MotorBench()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
