#!/usr/bin/env python3
"""Proportional temperature controller - the 'controller' of the Week 1 control loop.

Purpose  Week 1 activity. Subscribes to a sensor, filters it, decides, and commands an actuator: the pattern of
         almost every node you will write in this module.
Usage    python3 ~/labs/week01/scripts/fan_controller.py
         ros2 param set /fan_controller setpoint 24.0        # change it while it runs
Control  duty = kp * (filtered T - setpoint), limited to 0..100 %. The filter is a moving average of the last
         `window` readings. A P controller alone leaves a steady-state error - you will see it, and fix it in Week 3.
Topics   subscribes /room/temperature  sensor_msgs/msg/Temperature
         publishes  /fan/duty          std_msgs/msg/Float32   commanded fan duty, percent
"""
from collections import deque

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature
from std_msgs.msg import Float32


class FanController(Node):
    def __init__(self):
        super().__init__('fan_controller')
        self.declare_parameter('setpoint', 26.0)   # degrees C
        self.declare_parameter('kp', 20.0)         # percent duty per degree C of error
        self.declare_parameter('window', 5)        # moving-average length, samples
        self.history = deque()
        self.pub = self.create_publisher(Float32, '/fan/duty', 10)
        self.create_subscription(Temperature, '/room/temperature', self.on_temperature, 10)
        self.count = 0

    def on_temperature(self, msg):
        # parameters are read on every message, so `ros2 param set` takes effect at once
        setpoint = self.get_parameter('setpoint').value
        kp = self.get_parameter('kp').value
        window = max(1, self.get_parameter('window').value)
        self.history.append(msg.temperature)
        while len(self.history) > window:
            self.history.popleft()
        filtered = sum(self.history) / len(self.history)
        duty = min(max(kp * (filtered - setpoint), 0.0), 100.0)
        self.pub.publish(Float32(data=duty))
        self.count += 1
        if self.count % 10 == 0:                   # log every 2 s at 5 Hz
            self.get_logger().info('T = %.2f C (setpoint %.1f)  duty = %5.1f %%' % (filtered, setpoint, duty))


def main():
    rclpy.init()
    node = FanController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
