#!/usr/bin/env python3
"""CARLA WITH ROS 2 - the same cruise control as an ordinary ROS 2 node, through the official CARLA ROS 2 bridge.

Start, in three terminals:
   carla-sim start --town Town04
   ros2 launch carla_ros_bridge carla_ros_bridge_with_example_ego_vehicle.launch.py town:=Town04 synchronous_mode:=true
   python3 ~/labs/examples/carla/03_cruise_control_ros2.py --ros-args -p target_kmh:=50.0
Look at it:  rviz2  (the bridge publishes /carla/ego_vehicle/rgb_front/image, lidar, odometry, TF)

Listens:    /carla/ego_vehicle/speedometer           std_msgs/Float32 (m/s)
            /carla/ego_vehicle/odometry              nav_msgs/Odometry
Publishes:  /carla/ego_vehicle/vehicle_control_cmd   carla_msgs/CarlaEgoVehicleControl (throttle, brake, steer)

Pipeline:   CARLA <--(CARLA API)--> carla_ros_bridge <--(ROS 2 topics)--> this node
Steering: this node only does SPEED. Hold the lane with the bridge's manual control window, or leave steer at 0
on Town04's long straight (spawn point chosen by the bridge).
"""
import rclpy
from carla_msgs.msg import CarlaEgoVehicleControl
from rclpy.node import Node
from std_msgs.msg import Float32


class Cruise(Node):
    def __init__(self):
        super().__init__('cruise_control')
        self.declare_parameter('target_kmh', 50.0)
        self.declare_parameter('kp', 0.15)
        self.declare_parameter('ki', 0.02)
        self.integral, self.last = 0.0, None
        self.create_subscription(Float32, '/carla/ego_vehicle/speedometer', self.on_speed, 10)
        self.pub = self.create_publisher(CarlaEgoVehicleControl, '/carla/ego_vehicle/vehicle_control_cmd', 10)
        self.create_timer(1.0, self.report)
        self.kmh = 0.0

    def on_speed(self, msg):
        now = self.get_clock().now().nanoseconds * 1e-9
        dt = 0.05 if self.last is None else max(1e-3, now - self.last)
        self.last = now
        self.kmh = 3.6 * msg.data
        err = self.get_parameter('target_kmh').value - self.kmh
        self.integral = max(-50.0, min(50.0, self.integral + err * dt))
        u = self.get_parameter('kp').value * err + self.get_parameter('ki').value * self.integral
        cmd = CarlaEgoVehicleControl()
        cmd.throttle, cmd.brake = (min(u, 1.0), 0.0) if u >= 0 else (0.0, min(-u, 1.0))
        self.pub.publish(cmd)

    def report(self):
        self.get_logger().info('speed %.1f km/h (target %.0f)' % (self.kmh, self.get_parameter('target_kmh').value))


def main():
    rclpy.init()
    n = Cruise()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    n.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
