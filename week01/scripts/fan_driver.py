#!/usr/bin/env python3
"""A fan and its motor driver - the 'actuator' of the Week 1 control loop.

Purpose  Week 1 activity. Real actuators are not ideal: this one cannot start below a minimum duty (the motor
         stalls) and it takes time to spin up. Both effects show up in the closed loop.
Usage    python3 ~/labs/week01/scripts/fan_driver.py
         python3 ~/labs/week01/scripts/fan_driver.py --ros-args -p stall_duty:=0.0    # an 'ideal' fan
Model    speed follows the commanded duty with a first-order lag (time constant 0.8 s); a duty below
         `stall_duty` gives zero speed. The driver also offers an emergency-stop service.
Topics   subscribes /fan/duty   std_msgs/msg/Float32   commanded duty, percent (from fan_controller.py)
         publishes  /fan/speed  std_msgs/msg/Float32   actual fan speed, percent of maximum, 10 Hz
Service  /fan/stop  std_srvs/srv/SetBool   data: true latches the fan off, data: false releases it
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from std_srvs.srv import SetBool

TAU_S = 0.8     # spin-up time constant
RATE_HZ = 10.0


class FanDriver(Node):
    def __init__(self):
        super().__init__('fan_driver')
        self.declare_parameter('stall_duty', 20.0)     # percent; below this the motor does not turn
        self.duty, self.speed, self.stopped = 0.0, 0.0, False
        self.pub = self.create_publisher(Float32, '/fan/speed', 10)
        self.create_subscription(Float32, '/fan/duty', self.on_duty, 10)
        self.create_service(SetBool, '/fan/stop', self.on_stop)
        self.create_timer(1.0 / RATE_HZ, self.tick)

    def on_duty(self, msg):
        self.duty = min(max(msg.data, 0.0), 100.0)

    def on_stop(self, request, response):
        self.stopped = request.data
        response.success = True
        response.message = 'fan latched OFF' if self.stopped else 'fan released'
        self.get_logger().warn(response.message)
        return response

    def tick(self):
        target = self.duty
        if self.stopped or target < self.get_parameter('stall_duty').value:
            target = 0.0
        self.speed += (target - self.speed) * (1.0 / RATE_HZ) / TAU_S
        self.pub.publish(Float32(data=self.speed))


def main():
    rclpy.init()
    node = FanDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
