#!/usr/bin/env python3
"""Week 3, Lab C - check the mecanum inverse and forward kinematics on the simulated lab robot.

Terminal 1:  ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false
Terminal 2:  python3 ~/labs/week03/making_it_move/scripts/kinematics_check.py          (about 35 s of simulated time)
Options:     --speed 0.2 --dist 1.0 --wz 0.5     (the robot needs 1.2 m of free floor ahead and to its left)

Drives three segments from rest, then STOPS the robot with a zero Twist (the base has no command timeout):
  X   vx = speed until dist metres     Y   vy = speed until dist metres     Z   wz until one full turn
For every segment it prints
  - predicted wheel speeds (inverse Jacobian, NOMINAL r = 0.0375 m, L = lx + ly = 0.18 m) against the mean of
    /wheel_speeds, and their ratio: a ratio of 0.99 means that wheel is really 1 % larger than nominal
  - the null-space (slip) residual eps = (w_fl + w_fr - w_rl - w_rr)/4: mean and sd in rad/s
  - distance (or angle) from the forward map integrated over /wheel_speeds against /ground_truth/odom,
    as a percentage error and as the scale correction truth/wheels
"""
import argparse
import math

import numpy as np
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import JointState

R, L = 0.0375, 0.18                                    # nominal geometry (what the robot "believes")
J = np.array([[1, -1, -L], [1, 1, L], [1, 1, -L], [1, -1, L]]) / R     # inverse Jacobian, fl fr rl rr
J_PINV = np.linalg.pinv(J)                             # forward map: wheel speeds -> (vx, vy, wz)


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


class KinematicsCheck(Node):
    def __init__(self):
        super().__init__('kinematics_check', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(JointState, '/wheel_speeds', self.on_wheels, 50)
        self.create_subscription(Odometry, '/ground_truth/odom', self.on_truth, 50)
        self.w = []                                    # (t, w_fl, w_fr, w_rl, w_rr) while logging
        self.logging = False
        self.pose = None                               # (x, y, unwrapped yaw) from the simulator
        self.yaw_prev = None
        self.yaw_unwrapped = 0.0

    def t(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def on_wheels(self, msg):
        if self.logging:
            self.w.append([msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9] + list(msg.velocity))

    def on_truth(self, msg):
        yaw = yaw_of(msg.pose.pose.orientation)
        if self.yaw_prev is not None:
            self.yaw_unwrapped += math.atan2(math.sin(yaw - self.yaw_prev), math.cos(yaw - self.yaw_prev))
        self.yaw_prev = yaw
        p = msg.pose.pose.position
        self.pose = (p.x, p.y, self.yaw_unwrapped)

    def send(self, vx=0.0, vy=0.0, wz=0.0):
        m = Twist()
        m.linear.x, m.linear.y, m.angular.z = vx, vy, wz
        self.pub.publish(m)

    def wait(self, seconds, cmd=(0.0, 0.0, 0.0)):
        """Publish cmd at 20 Hz for `seconds` of simulated time."""
        t_end, t_pub = self.t() + seconds, 0.0
        while rclpy.ok() and self.t() < t_end:
            if self.t() - t_pub >= 0.05:
                self.send(*cmd)
                t_pub = self.t()
            rclpy.spin_once(self, timeout_sec=0.05)

    def segment(self, name, cmd, target, key):
        """Drive cmd until the TRUE distance/angle reaches target, then stop and analyse."""
        self.wait(1.0)                                 # at rest
        p0 = self.pose
        self.w, self.logging = [], True
        dist = lambda p: math.hypot(p[0] - p0[0], p[1] - p0[1]) if key != 'wz' else abs(p[2] - p0[2])  # noqa
        while rclpy.ok() and dist(self.pose) < target:
            self.wait(0.05, cmd)
        self.wait(1.0)                                 # stop, let the last reports arrive
        self.logging = False
        p1 = self.pose
        w = np.array(self.w)
        t, w = w[:, 0], w[:, 1:5]
        moving = np.abs(w).sum(axis=1) > 0.5
        pred = J @ np.array(cmd)
        meas = w[moving][3:-3].mean(axis=0)            # skip the start and stop transients
        eps = (w[moving] @ np.array([1, 1, -1, -1])) / 4
        xi = w @ J_PINV.T                              # forward map for every report
        dt = np.diff(t, prepend=t[0])
        print('\n=== %s: vx=%.2f vy=%.2f wz=%.2f, %d wheel reports'
              % (name, cmd[0], cmd[1], cmd[2], len(w)))
        print('  wheel       fl       fr       rl       rr   [rad/s]')
        print('  predicted ' + ' '.join('%8.3f' % v for v in pred))
        print('  measured  ' + ' '.join('%8.3f' % v for v in meas))
        print('  ratio     ' + ' '.join('%8.4f' % v for v in meas / pred))
        print('  slip residual eps: mean %+.4f sd %.4f rad/s' % (eps.mean(), eps.std()))
        if key == 'wz':
            wheel, truth, unit = np.sum(xi[:, 2] * dt), p1[2] - p0[2], 'rad'
        else:
            wheel = np.sum(np.hypot(xi[:, 0], xi[:, 1]) * dt)
            truth, unit = math.hypot(p1[0] - p0[0], p1[1] - p0[1]), 'm'
        print('  wheels %.4f %s, truth %.4f %s: error %+.2f %%, correction %.4f'
              % (wheel, unit, truth, unit, (wheel - truth) / truth * 100, truth / wheel))


def main():
    ap = argparse.ArgumentParser(description='mecanum kinematics check on the simulated robot')
    ap.add_argument('--speed', type=float, default=0.2)
    ap.add_argument('--dist', type=float, default=1.0)
    ap.add_argument('--wz', type=float, default=0.5)
    a = ap.parse_args()
    rclpy.init()
    node = KinematicsCheck()
    try:
        while rclpy.ok() and node.pose is None:        # wait for the simulator
            rclpy.spin_once(node, timeout_sec=0.5)
        node.segment('X (forward)', (a.speed, 0.0, 0.0), a.dist, 'x')
        node.segment('Y (left)', (0.0, a.speed, 0.0), a.dist, 'y')
        node.segment('Z (one turn CCW)', (0.0, 0.0, a.wz), 2 * math.pi, 'wz')
    finally:
        for _ in range(5):
            node.send()                                # ALWAYS leave the robot stopped
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
