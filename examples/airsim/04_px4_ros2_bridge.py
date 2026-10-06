#!/usr/bin/env python3
"""AirSim WITH ROS 2 - the control bridge: drive the PX4 autopilot with ordinary ROS 2 messages.

Start the simulator first:   drone-sim start --world blocks
Then run:                    python3 ~/labs/examples/airsim/04_px4_ros2_bridge.py
Try it:                      ros2 service call /drone/takeoff std_srvs/srv/Trigger
                             ros2 topic pub -r 10 /drone/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.0}}"
                             ros2 service call /drone/land std_srvs/srv/Trigger

Interface (ROS conventions, body frame FLU: x forward, y left, z up, yaw rate positive = turn left):
  /drone/takeoff  std_srvs/Trigger   arm, climb to 'altitude' (parameter, default 5 m), hold position (offboard)
  /drone/land     std_srvs/Trigger   leave offboard and land
  /drone/cmd_vel  geometry_msgs/Twist velocity command; if nothing arrives for 0.5 s the drone holds still
  /drone/px4/odom nav_msgs/Odometry  the AUTOPILOT's own estimate (EKF2), map frame ENU - compare with /drone/odom
  /drone/px4/status std_msgs/String  armed / flight mode / altitude

Pipeline:   your node --(ROS 2)--> this bridge --(MAVSDK, MAVLink UDP 14540)--> PX4 --> AirSim
            The same bridge works in HIL mode with the real Pixhawk 6C (point 'url' at the Jetson's MAVLink link).
"""
import asyncio
import math
import threading
import time

import rclpy
from geometry_msgs.msg import Twist
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityBodyYawspeed
from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger


class Px4Bridge(Node):
    def __init__(self):
        super().__init__('px4_bridge')
        self.declare_parameter('url', 'udpin://0.0.0.0:14540')
        self.declare_parameter('altitude', 5.0)
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        self.drone = System()
        self.cmd = (0.0, 0.0, 0.0, 0.0)
        self.last_cmd = 0.0
        self.offboard = False
        self.status = {'armed': False, 'mode': '?', 'alt': 0.0}
        self.pub_odom = self.create_publisher(Odometry, '/drone/px4/odom', 10)
        self.pub_status = self.create_publisher(String, '/drone/px4/status', 10)
        self.create_subscription(Twist, '/drone/cmd_vel', self.on_cmd, 10)
        self.create_service(Trigger, '/drone/takeoff', self.on_takeoff)
        self.create_service(Trigger, '/drone/land', self.on_land)
        self.create_timer(0.05, self.send_setpoint)
        self.create_timer(0.5, self.publish_status)
        self.call(self.connect(), timeout=120)

    def call(self, coro, timeout=60):
        """Run a MAVSDK coroutine on the MAVSDK thread and wait for its result."""
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)

    async def connect(self):
        url = self.get_parameter('url').value
        self.get_logger().info('connecting to PX4 on %s ...' % url)
        await self.drone.connect(system_address=url)
        async for s in self.drone.core.connection_state():
            if s.is_connected:
                break
        for coro in (self.watch_odom(), self.watch_armed(), self.watch_mode(), self.watch_alt()):
            asyncio.ensure_future(coro)
        self.get_logger().info('PX4 connected - services /drone/takeoff and /drone/land are ready')

    async def watch_odom(self):
        async for pv in self.drone.telemetry.position_velocity_ned():
            o = Odometry()
            o.header.stamp = self.get_clock().now().to_msg()
            o.header.frame_id, o.child_frame_id = 'map', 'base_link'
            o.pose.pose.position.x, o.pose.pose.position.y = pv.position.east_m, pv.position.north_m
            o.pose.pose.position.z = -pv.position.down_m
            o.twist.twist.linear.x, o.twist.twist.linear.y = pv.velocity.east_m_s, pv.velocity.north_m_s
            o.twist.twist.linear.z = -pv.velocity.down_m_s
            self.pub_odom.publish(o)

    async def watch_armed(self):
        async for a in self.drone.telemetry.armed():
            self.status['armed'] = a

    async def watch_mode(self):
        async for m in self.drone.telemetry.flight_mode():
            self.status['mode'] = str(m)

    async def watch_alt(self):
        async for p in self.drone.telemetry.position():
            self.status['alt'] = p.relative_altitude_m

    async def takeoff(self):
        alt = float(self.get_parameter('altitude').value)
        async for h in self.drone.telemetry.health():
            if h.is_global_position_ok and h.is_home_position_ok:
                break
        await self.drone.action.set_takeoff_altitude(alt)
        await self.drone.action.arm()
        await self.drone.action.takeoff()
        t0 = time.time()
        while self.status['alt'] < alt - 0.5 and time.time() - t0 < 30:
            await asyncio.sleep(0.2)
        await self.drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
        await self.drone.offboard.start()
        self.offboard = True
        return 'airborne at %.1f m, offboard - send /drone/cmd_vel' % self.status['alt']

    async def land(self):
        self.offboard = False
        try:
            await self.drone.offboard.stop()
        except OffboardError:
            pass
        await self.drone.action.land()
        return 'landing'

    def on_takeoff(self, req, res):
        try:
            res.message, res.success = self.call(self.takeoff()), True
        except Exception as e:                       # report the autopilot's reason instead of crashing
            res.message, res.success = 'take-off failed: %s' % e, False
        return res

    def on_land(self, req, res):
        try:
            res.message, res.success = self.call(self.land()), True
        except Exception as e:
            res.message, res.success = 'land failed: %s' % e, False
        return res

    def on_cmd(self, msg):
        # ROS body frame FLU -> PX4 body frame FRD; ROS yaw rate (rad/s, left positive) -> PX4 (deg/s, right positive)
        self.cmd = (msg.linear.x, -msg.linear.y, -msg.linear.z, -math.degrees(msg.angular.z))
        self.last_cmd = time.time()

    def send_setpoint(self):
        if not self.offboard:
            return
        f, r, d, y = self.cmd if time.time() - self.last_cmd < 0.5 else (0.0, 0.0, 0.0, 0.0)
        asyncio.run_coroutine_threadsafe(self.drone.offboard.set_velocity_body(VelocityBodyYawspeed(f, r, d, y)),
                                         self.loop)

    def publish_status(self):
        s = self.status
        self.pub_status.publish(String(data='armed=%s mode=%s alt=%.1f m offboard=%s' %
                                       (s['armed'], s['mode'], s['alt'], self.offboard)))


def main():
    rclpy.init()
    node = Px4Bridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
