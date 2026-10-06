#!/usr/bin/env python3
"""Command-to-measurement latency of the lab robot: time a velocity step through the whole chain.

Purpose  Week 1, Laboratory C. `ros2 topic delay` tells you how old each message is; this script measures the
         end-to-end chain a controller actually sees:  /cmd_vel step  ->  body moves (/ground_truth/odom)
         ->  encoders report it (/vel_raw, the 25 Hz 'firmware' report of the wheel_odometry node).
Usage    (simulator running, robot free to move ~1 m forward)
           python3 ~/labs/week01/scripts/step_latency.py --trials 10
Method   each trial: 1.50-1.54 s of zero command (random, so the step lands at a random phase of the 40 ms
         encoder report cycle), then a 0.20 m/s step for 0.5 s, then zero again.
         A stage 'responds' when its measured vx first exceeds 50 % of the step. All times are simulated time.
Output   per-trial delays and the mean, standard deviation and maximum for each stage [ms]. The robot ends
         where it started (+/- drift): forward steps alternate with backward steps.
"""
import argparse
import random
import signal
import time

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.signals import SignalHandlerOptions
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

STEP, T_ZERO, T_STEP = 0.20, 1.5, 0.5


class StepLatency(Node):
    def __init__(self, trials):
        super().__init__('step_latency', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Odometry, '/ground_truth/odom', self.on_truth, 50)
        self.create_subscription(Twist, '/vel_raw', self.on_vel_raw, 50)
        self.trials, self.k, self.t_start, self.t_step = trials, 0, None, None
        self.sign, self.hit, self.res = 1.0, {}, []
        self.t_zero = T_ZERO + random.uniform(0.0, 0.04)
        self.create_timer(0.005, self.tick)                   # 200 Hz command loop (simulated time)

    def now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def mark(self, stage, vx, t):
        if self.t_step is not None and stage not in self.hit and self.sign * vx > 0.5 * STEP:
            self.hit[stage] = (t - self.t_step) * 1e3

    def on_truth(self, m):          # stamp = when the simulator produced the state
        self.mark('truth', m.twist.twist.linear.x, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)

    def on_vel_raw(self, m):        # Twist has no header: use the arrival time
        self.mark('vel_raw', m.linear.x, self.now())

    def tick(self):
        t = self.now()
        if t == 0.0:
            return
        if self.t_start is None:
            self.t_start = t
        cmd = Twist()
        phase = t - self.t_start
        if phase >= self.t_zero:
            if self.t_step is None:
                self.t_step = t                                # the step is published NOW
            cmd.linear.x = self.sign * STEP
        if phase >= self.t_zero + T_STEP:                           # end of trial
            cmd.linear.x = 0.0
            self.res.append((self.hit.get('truth', np.nan), self.hit.get('vel_raw', np.nan)))
            print('trial %2d   cmd->truth %6.1f ms   cmd->vel_raw %6.1f ms' % (len(self.res), *self.res[-1]))
            self.sign, self.hit, self.t_step, self.t_start = -self.sign, {}, None, t
            self.t_zero = T_ZERO + random.uniform(0.0, 0.04)
            if len(self.res) >= self.trials:
                self.pub.publish(Twist())
                raise SystemExit
        self.pub.publish(cmd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--trials', type=int, default=10)
    a = ap.parse_args()
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)   # Ctrl-C must not kill the context:
    signal.signal(signal.SIGINT, signal.default_int_handler)     # we still need it to stop the robot
    node = StepLatency(a.trials)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    r = np.array(node.res) if node.res else np.zeros((0, 2))
    for j, name in enumerate(['cmd_vel -> ground truth', 'cmd_vel -> /vel_raw (encoders)']):
        col = r[:, j][~np.isnan(r[:, j])] if len(r) else []
        if len(col):
            print('%-32s mean %6.1f ms   sd %5.1f ms   max %6.1f ms   (n=%d)'
                  % (name, np.mean(col), np.std(col), np.max(col), len(col)))
    for _ in range(5):                                   # stop the robot; let DDS deliver before exiting
        node.pub.publish(Twist())
        time.sleep(0.05)
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
