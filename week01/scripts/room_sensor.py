#!/usr/bin/env python3
"""A heated room with a temperature sensor - the 'plant' and the 'sensor' of the Week 1 control loop.

Purpose  Week 1 activity. A first ROS 2 node that behaves like a real sensor: it publishes a noisy, quantised
         reading at a fixed rate, with a frame and a timestamp, and it reacts to an actuator (the fan).
Usage    python3 ~/labs/week01/scripts/room_sensor.py
         python3 ~/labs/week01/scripts/room_sensor.py --ros-args -p noise_std:=0.5
Model    first-order room: a heater would hold it at ambient + 15 C (time constant 20 s); the fan removes heat in
         proportion to its speed and to (T - ambient). The sensor adds Gaussian noise and rounds to 0.1 C.
Topics   publishes  /room/temperature  sensor_msgs/msg/Temperature   5 Hz
         subscribes /fan/speed         std_msgs/msg/Float32          fan speed in percent (from fan_driver.py)
"""
import random

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature
from std_msgs.msg import Float32

AMBIENT_C = 20.0      # outside temperature
HEATER_RISE_C = 15.0  # with no fan the room settles at AMBIENT_C + HEATER_RISE_C
TAU_S = 20.0          # thermal time constant of the room
FAN_GAIN = 0.15       # heat removed per second at 100 % fan, per degree above ambient


class RoomSensor(Node):
    def __init__(self):
        super().__init__('room_sensor')
        self.declare_parameter('rate_hz', 5.0)
        self.declare_parameter('noise_std', 0.2)               # sensor noise, degrees C (1 sigma)
        self.temp_c = AMBIENT_C + 5.0                          # start a little warm
        self.fan_pct = 0.0
        self.pub = self.create_publisher(Temperature, '/room/temperature', 10)
        self.create_subscription(Float32, '/fan/speed', self.on_fan, 10)
        self.dt = 1.0 / self.get_parameter('rate_hz').value
        self.create_timer(self.dt, self.tick)
        self.get_logger().info('room_sensor: publishing /room/temperature at %.1f Hz' % (1.0 / self.dt))

    def on_fan(self, msg):
        self.fan_pct = min(max(msg.data, 0.0), 100.0)

    def tick(self):
        # plant: integrate the room temperature one step (Euler)
        heating = (AMBIENT_C + HEATER_RISE_C - self.temp_c) / TAU_S
        cooling = FAN_GAIN * (self.fan_pct / 100.0) * (self.temp_c - AMBIENT_C)
        self.temp_c += (heating - cooling) * self.dt
        # sensor: noise and 0.1 C resolution, stamped and labelled with its frame
        msg = Temperature()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'room_sensor_link'
        noise = random.gauss(0.0, self.get_parameter('noise_std').value)
        msg.temperature = round(self.temp_c + noise, 1)
        msg.variance = self.get_parameter('noise_std').value ** 2
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = RoomSensor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
