#!/usr/bin/env python3
"""drive_and_score.py - drive the 24 m circuit and score every position estimate against the truth (Week 5).

Started by fusion.launch.py (20 s after the simulator). It
  1. drives the Week 4 circuit (west room -> door -> round the crate -> back -> round the pillar -> start),
     steering on /ground_truth/odom - a test harness: the odometry, the EKF and SLAM never see that topic;
  2. publishes three trails for RViz, all in the start (map) frame:
        /trail/truth  green    where the robot really went
        /trail/raw    red      wheel odometry   /odom_raw
        /trail/ekf    blue     the EKF          /odometry/filtered  (only when the EKF runs)
  3. at the end prints one table: position error at the end, RMS and max, and heading error at the end, for
     wheel odometry, the EKF and SLAM (TF map -> base_footprint, when a SLAM node runs).

Usage (normally via the launch file):
  python3 ~/labs/week05/scripts/drive_and_score.py --ros-args -p use_sim_time:=true
  ... -p drive:=false            only score and draw trails: drive yourself with teleop, Ctrl+C to finish
  ... -p turn_rate:=1.0          turn faster (A4)
  ... -p laps:=2                 drive the circuit twice
  ... -p csv:=run.csv            also save the poses

Expected output (end of the run, odom:=ekf with the solution ekf.yaml; your numbers will differ slightly):
  loop finished: 24.4 m in 210 s
                      end [m]   RMS [m]   max [m]   heading at end [deg]
  wheel odometry        1.3       0.6       1.3      -14
  EKF                   0.1       ...
  SLAM                  0.02      ...
"""
import math
import sys
import time
import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry, Path
from tf2_ros import Buffer, TransformListener

# circuit in WORLD coordinates (lab world); the robot starts at (-3.0, -0.4) facing +x  (same as Week 4)
CIRCUIT = [(-0.2, -1.5), (2.0, -1.2), (2.0, 1.5), (4.0, 0.6), (3.4, -0.9), (2.0, -1.2), (-0.2, -1.5),
           (-0.5, 1.6), (-2.5, 2.1), (-3.6, 2.1), (-3.6, -0.4), (-3.0, -0.4)]
NAMES = [('raw', 'wheel odometry'), ('ekf', 'EKF'), ('slam', 'SLAM')]


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


class DriveAndScore(Node):
    def __init__(self):
        super().__init__('drive_and_score')
        p = self.declare_parameter
        self.drive = p('drive', True).value
        self.speed, self.turn = p('speed', 0.15).value, p('turn_rate', 0.3).value
        self.laps = p('laps', 1).value
        self.spawn = (p('spawn_x', -3.0).value, p('spawn_y', -0.4).value, p('spawn_yaw', 0.0).value)
        self.csv = p('csv', '').value
        self.truth = None
        self.ekf_z = None
        self.est = {'raw': None, 'ekf': None}
        self.rows, self.wp, self.lap, self.done, self.dist, self.last = [], 0, 0, False, 0.0, None
        self.tf = Buffer()
        TransformListener(self.tf, self)
        self.cmd = self.create_publisher(Twist, '/cmd_vel', 10)
        self.trail_pub = {k: self.create_publisher(Path, '/trail/' + k, 1) for k in ('truth', 'raw', 'ekf')}
        self.trail = {k: Path() for k in ('truth', 'raw', 'ekf')}
        for t in self.trail.values():
            t.header.frame_id = 'map'
        self.create_subscription(Odometry, '/ground_truth/odom', self.on_truth, 10)
        self.create_subscription(Odometry, '/odom_raw', lambda m: self.on_est('raw', m), 10)
        self.create_subscription(Odometry, '/odometry/filtered', lambda m: self.on_est('ekf', m), 10)
        self.create_timer(0.05, self.control)     # 20 Hz driver
        self.create_timer(0.5, self.log)          # 2 Hz log + trails
        self.t0 = None

    def on_truth(self, m):
        pp = m.pose.pose
        self.truth = (pp.position.x, pp.position.y, yaw_of(pp.orientation))

    def on_est(self, key, m):
        pp = m.pose.pose
        if key == 'ekf':                                  # for TODO 3: the states no sensor measures
            self.ekf_z = (pp.position.z, m.pose.covariance[14])
        self.est[key] = (pp.position.x, pp.position.y, yaw_of(pp.orientation))

    def truth_in_map(self):
        """World pose -> start (map) frame: subtract the spawn pose."""
        x, y, th = self.truth
        sx, sy, sth = self.spawn
        dx, dy = x - sx, y - sy
        c, s = math.cos(-sth), math.sin(-sth)
        return c * dx - s * dy, s * dx + c * dy, wrap(th - sth)

    def control(self):
        if not self.drive or self.truth is None or self.done:
            return
        x, y, th = self.truth
        if self.last:
            self.dist += math.hypot(x - self.last[0], y - self.last[1])
        self.last = (x, y)
        if self.t0 is None:
            self.t0 = self.get_clock().now()
        gx, gy = CIRCUIT[self.wp]
        d = math.hypot(gx - x, gy - y)
        err = wrap(math.atan2(gy - y, gx - x) - th)
        cmd = Twist()
        if d < 0.08:
            self.wp += 1
            if self.wp == len(CIRCUIT):
                self.wp, self.lap = 0, self.lap + 1
                if self.lap == self.laps:
                    self.done = True
                    self.cmd.publish(Twist())             # no command timeout: stop explicitly
                    sec = (self.get_clock().now() - self.t0).nanoseconds * 1e-9
                    self.get_logger().info('loop finished: %.1f m in %.0f s' % (self.dist, sec))
                    self.log()
                    self.report()
            return
        if abs(err) > 0.15:                               # turn on the spot towards the waypoint
            cmd.angular.z = max(-self.turn, min(self.turn, 1.5 * err))
        else:                                             # drive, slowing for the last 0.4 m
            cmd.linear.x = self.speed * min(1.0, d / 0.4 + 0.2)
            cmd.angular.z = max(-self.turn, min(self.turn, 1.5 * err))
        self.cmd.publish(cmd)

    def slam_pose(self):
        try:
            tr = self.tf.lookup_transform('map', 'base_footprint', rclpy.time.Time())
        except Exception:                                 # no SLAM running
            return None
        q = tr.transform.rotation
        return tr.transform.translation.x, tr.transform.translation.y, yaw_of(q)

    def log(self):
        if self.truth is None or self.est['raw'] is None:
            return
        now = self.get_clock().now()
        truth = self.truth_in_map()
        self.rows.append((now.nanoseconds * 1e-9, truth, self.est['raw'], self.est['ekf'], self.slam_pose()))
        for key, pose in (('truth', truth), ('raw', self.est['raw']), ('ekf', self.est['ekf'])):
            if pose is None:
                continue
            ps = PoseStamped()
            ps.header.frame_id, ps.header.stamp = 'map', now.to_msg()
            ps.pose.position.x, ps.pose.position.y = pose[0], pose[1]
            ps.pose.orientation.z, ps.pose.orientation.w = math.sin(pose[2] / 2), math.cos(pose[2] / 2)
            self.trail[key].poses.append(ps)
            self.trail[key].header.stamp = ps.header.stamp
            self.trail_pub[key].publish(self.trail[key])

    def report(self):
        if not self.rows:
            print('no data logged - is the simulator running with use_sim_time?')
            return
        print('samples: %d at 2 Hz over %.0f s' % (len(self.rows), self.rows[-1][0] - self.rows[0][0]))
        print('                    end [m]   RMS [m]   max [m]   heading at end [deg]')
        for i, (_, name) in enumerate(NAMES):
            pairs = [(r[1], r[2 + i]) for r in self.rows if r[2 + i] is not None]
            if not pairs:
                print('%-18s  (not running)' % name)
                continue
            e = [math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in pairs]
            rms = math.sqrt(sum(v * v for v in e) / len(e))
            dh = math.degrees(wrap(pairs[-1][1][2] - pairs[-1][0][2]))
            print('%-18s  %7.3f   %7.3f   %7.3f   %+7.1f' % (name, e[-1], rms, max(e), dh))
        if self.ekf_z:
            print('EKF height z at the end: %.3f m, its variance %.3g m^2  (a flat floor: should be 0 and small)'
                  % self.ekf_z)
        if self.csv:
            with open(self.csv, 'w') as f:
                f.write('t,truth_x,truth_y,truth_yaw,raw_x,raw_y,raw_yaw,ekf_x,ekf_y,ekf_yaw,slam_x,slam_y,slam_yaw\n')
                for r in self.rows:
                    vals = [r[0]] + [v for pose in r[1:] for v in (pose if pose else (math.nan,) * 3)]
                    f.write(','.join('%.4f' % v for v in vals) + '\n')
            print('saved', self.csv)


def main():
    sys.stdout.reconfigure(line_buffering=True)          # print the table at once, even under ros2 launch
    # keep the ROS context alive on Ctrl+C so that the final zero Twist can still be published
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = DriveAndScore()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
        if node.done:                                     # keep the trails on screen after the loop
            end = time.time() + 3600
            while rclpy.ok() and time.time() < end:
                rclpy.spin_once(node, timeout_sec=0.5)
    except KeyboardInterrupt:
        if not node.done:
            node.report()
    finally:
        for _ in range(5):                                # the simulated robot has no command timeout
            node.cmd.publish(Twist())
            time.sleep(0.02)
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
