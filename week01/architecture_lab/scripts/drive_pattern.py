#!/usr/bin/env python3
"""Drive the simulated lab robot round a fixed, repeatable pattern (the 'duty cycle' of the energy test).

Purpose  Week 1, Laboratory B. An endurance figure means nothing without the duty cycle that produced it, so the
         pattern is written down here, in code, and is the same for everyone.
Usage    python3 ~/labs/week01/scripts/drive_pattern.py                # loop until Ctrl-C
         python3 ~/labs/week01/scripts/drive_pattern.py --cycles 2     # two laps, then stop
Pattern  one lap (19.3 s of simulated time): a 0.9 m square driven with the mecanum base's sideways motion
         (+x, +y, -x, -y at 0.30 m/s, 3 s each), a full turn on the spot at 1.0 rad/s, and a 1 s pause.
         Mean |v| over a lap = 0.19 m/s, mean |wz| = 0.33 rad/s. Edit PHASES to define your own duty cycle.
Safety   the lab robot has NO command timeout - it keeps the last command for ever. This script therefore
         publishes a zero Twist when it ends, including on Ctrl-C.
"""
import argparse
import signal
import time

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.signals import SignalHandlerOptions
from geometry_msgs.msg import Twist

#          seconds  vx [m/s]  vy [m/s]  wz [rad/s]
PHASES = [(3.0,     0.30,     0.0,      0.0),
          (3.0,     0.0,      0.30,     0.0),
          (3.0,    -0.30,     0.0,      0.0),
          (3.0,     0.0,     -0.30,     0.0),
          (6.283,   0.0,      0.0,      1.0),
          (1.0,     0.0,      0.0,      0.0)]


class Pattern(Node):
    def __init__(self, cycles):
        super().__init__('drive_pattern', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.cycles, self.lap, self.phase, self.t0 = cycles, 0, 0, None
        self.create_timer(0.05, self.tick)                    # 20 Hz command stream (simulated time)

    def tick(self):
        now = self.get_clock().now().nanoseconds * 1e-9
        if now == 0.0:
            return                                             # /clock not received yet
        if self.t0 is None:
            self.t0 = now
            self.get_logger().info('lap 1 started')
        while now - self.t0 >= PHASES[self.phase][0]:          # advance to the next phase on schedule
            self.t0 += PHASES[self.phase][0]
            self.phase = (self.phase + 1) % len(PHASES)
            if self.phase == 0:
                self.lap += 1
                if self.cycles and self.lap >= self.cycles:
                    raise SystemExit
                self.get_logger().info('lap %d started' % (self.lap + 1))
        _, vx, vy, wz = PHASES[self.phase]
        cmd = Twist()
        cmd.linear.x, cmd.linear.y, cmd.angular.z = vx, vy, wz
        self.pub.publish(cmd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cycles', type=int, default=0, help='number of laps (0 = until Ctrl-C)')
    a = ap.parse_args()
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)   # keep the context alive on Ctrl-C ...
    signal.signal(signal.SIGINT, signal.default_int_handler)     # Ctrl-C -> KeyboardInterrupt, even in background
    signal.signal(signal.SIGTERM, signal.default_int_handler)    # 'kill' also stops the robot first
    node = Pattern(a.cycles)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    for _ in range(5):                                             # ... so that we can still stop the robot
        node.pub.publish(Twist())
        time.sleep(0.05)                                           # give DDS time to deliver before we exit
    node.get_logger().info('stopped after %d complete laps (zero Twist sent)' % node.lap)
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
