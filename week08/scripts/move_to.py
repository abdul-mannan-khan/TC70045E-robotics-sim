"""Drive the simulated lab robot to a pose (x, y) in the world frame, using /ground_truth/odom, then stop.

Purpose: place the robot at a known distance from a target, the way you would roll a real robot to a tape mark.
It uses the simulator's exact pose, which only exists in simulation (on a real robot you would use a tape measure).
The mecanum base is holonomic, so the robot moves in x and y without turning; yaw is held at 0.

Usage (range world, robot spawned with x:=0 y:=0):
    python3 ~/labs/week08/scripts/move_to.py 4.81 0.0      # camera 2.0 m from the target wall
    python3 ~/labs/week08/scripts/move_to.py 0.0 3.3       # in front of the 30 degree target
Expected output:
    reached x=4.806 y=0.000 (target 4.810 0.000) in 16.4 s  -- robot stopped

Remember: the simulated base has NO command timeout. This script always publishes a zero Twist before it exits.
"""
import math
import sys
import time

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

V_MAX = 0.30      # m/s
GAIN = 1.0        # 1/s, proportional gain on position error
TOL = 0.004       # m, stop when closer than this


class Mover(Node):
    def __init__(self):
        super().__init__('move_to', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.pose = None
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Odometry, '/ground_truth/odom', self.on_odom, 10)
        self.ex = SingleThreadedExecutor()     # one persistent executor: the global rclpy.spin_once(node) re-adds
        self.ex.add_node(self)                 # the node on every call, too slow for the 200 Hz /clock of a simulation

    def on_odom(self, m):
        q = m.pose.pose.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        self.pose = (m.pose.pose.position.x, m.pose.pose.position.y, yaw)

    def stop(self):
        for _ in range(3):
            self.pub.publish(Twist())
            time.sleep(0.05)

    def go(self, gx, gy, timeout=120.0):
        t0 = time.time()
        while rclpy.ok() and time.time() - t0 < timeout:
            self.ex.spin_once(timeout_sec=0.05)
            if self.pose is None:
                continue
            x, y, yaw = self.pose
            ex, ey = gx - x, gy - y
            dist = math.hypot(ex, ey)
            if dist < TOL:
                break
            s = min(V_MAX, GAIN * dist) / dist            # world-frame velocity along the error
            vx_w, vy_w = s * ex, s * ey
            cmd = Twist()                                  # rotate into the body frame
            cmd.linear.x = math.cos(yaw) * vx_w + math.sin(yaw) * vy_w
            cmd.linear.y = -math.sin(yaw) * vx_w + math.cos(yaw) * vy_w
            cmd.angular.z = -1.0 * yaw                     # hold yaw = 0
            self.pub.publish(cmd)
        self.stop()
        return dist, time.time() - t0


def main():
    gx, gy = float(sys.argv[1]), float(sys.argv[2])
    rclpy.init()
    node = Mover()
    try:
        err, dt = node.go(gx, gy)
        node.ex.spin_once(timeout_sec=0.1)
        x, y, _ = node.pose
        print('reached x=%.3f y=%.3f (target %.3f %.3f) in %.1f s  -- robot stopped' % (x, y, gx, gy, dt))
    except KeyboardInterrupt:
        node.stop()
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
