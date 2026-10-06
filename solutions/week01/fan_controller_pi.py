#!/usr/bin/env python3
"""SOLUTION - Week 1 activity: add integral action to fan_controller.py so the room reaches the setpoint.

Run    python3 ~/labs/week01/scripts/room_sensor.py      # T1
       python3 ~/labs/week01/scripts/fan_driver.py       # T2
       python3 ~/labs/solutions/week01/fan_controller_pi.py   # T3 (instead of fan_controller.py)
What changed  duty = kp * error  +  ki * (sum of error * dt). The integral keeps growing while there is an error,
              so the fan ends up exactly as fast as it must be - the steady-state error disappears.
              The integral is frozen while the duty is limited at 0 or 100 % (anti-windup).
"""
from collections import deque

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature
from std_msgs.msg import Float32


class FanControllerPI(Node):
    def __init__(self):
        super().__init__('fan_controller')
        self.declare_parameter('setpoint', 26.0)
        self.declare_parameter('kp', 20.0)
        self.declare_parameter('ki', 2.0)          # NEW: % duty per (degree C x second)
        self.declare_parameter('window', 5)
        self.history = deque()
        self.integral = 0.0                        # NEW
        self.last_t = None
        self.pub = self.create_publisher(Float32, '/fan/duty', 10)
        self.create_subscription(Temperature, '/room/temperature', self.on_temperature, 10)
        self.count = 0

    def on_temperature(self, msg):
        setpoint = self.get_parameter('setpoint').value
        kp, ki = self.get_parameter('kp').value, self.get_parameter('ki').value
        window = max(1, self.get_parameter('window').value)
        self.history.append(msg.temperature)
        while len(self.history) > window:
            self.history.popleft()
        filtered = sum(self.history) / len(self.history)
        now = self.get_clock().now().nanoseconds * 1e-9
        dt = 0.0 if self.last_t is None else now - self.last_t
        self.last_t = now
        error = filtered - setpoint
        unclamped = kp * error + ki * (self.integral + error * dt)
        if 0.0 < unclamped < 100.0:                # anti-windup: integrate only when not saturated
            self.integral += error * dt
        duty = min(max(kp * error + ki * self.integral, 0.0), 100.0)
        self.pub.publish(Float32(data=duty))
        self.count += 1
        if self.count % 10 == 0:
            self.get_logger().info('T = %.2f C (setpoint %.1f)  duty = %5.1f %%' % (filtered, setpoint, duty))


def main():
    rclpy.init()
    node = FanControllerPI()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
