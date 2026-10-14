#!/usr/bin/env python3
"""nav_repeat.py - repeatability of Nav2: N runs start -> goal, final pose error measured against the truth.

Needs: the simulator, and Nav2 with AMCL on a saved map (nav2_bringup bringup_launch.py map:=...).
For every run the robot is first sent back to the start pose (by Nav2 itself, as you would on a real floor),
then to the goal. When Nav2 reports the goal reached, the script waits 1 s and records
  - the TRUE final pose (/ground_truth/odom, converted into the map frame: map = world - spawn pose),
  - the AMCL estimate (/amcl_pose), so you can split the error into "localisation" and "control",
  - the run time and the number of recovery behaviours Nav2 used.
It finishes with mean, sample standard deviation and RMS of the radial error, and the goal-checker tolerance.

Usage
  python3 ~/labs/week09/scripts/nav_repeat.py --ros-args -p use_sim_time:=true
  ... -p goal_x:=3.0 -p goal_y:=1.0 -p goal_yaw:=1.57 -p runs:=5      (map frame, metres / rad)
  ... -p set_initial_pose:=false          if you already set AMCL with "2D Pose Estimate" in rviz2

Expected output (default goal, xy_goal_tolerance 0.25 m)
  run  dx[mm]  dy[mm]  dth[deg]  amcl_err[mm]  t[s]  recov
    1    -118     +36     +3.1           21    42      0
  ...
  radial error: mean 128 mm, s 35 mm, RMS 132 mm (n = 5)   goal tolerance 250 mm / 14.3 deg
"""
import math
import statistics as st
import rclpy
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import Odometry
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def pose(nav, x, y, yaw):
    p = PoseStamped()
    p.header.frame_id = 'map'
    p.header.stamp = nav.get_clock().now().to_msg()
    p.pose.position.x, p.pose.position.y = x, y
    p.pose.orientation.z, p.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
    return p


def main():
    rclpy.init()
    nav = BasicNavigator()
    P = lambda n, v: nav.declare_parameter(n, v).value
    goal = (P('goal_x', 3.0), P('goal_y', 1.0), P('goal_yaw', 0.0))     # map frame = world (0.0, 0.6)
    start = (P('start_x', 0.0), P('start_y', 0.0), P('start_yaw', 0.0))
    runs, spawn = P('runs', 5), (P('spawn_x', -3.0), P('spawn_y', -0.4))
    limit = P('timeout', 90.0)             # s per leg; a stuck run is cancelled and reported
    s = {}
    nav.create_subscription(Odometry, '/ground_truth/odom', lambda m: s.update(truth=m.pose.pose), 10)
    nav.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', lambda m: s.update(amcl=m.pose.pose), 10)

    def truth_map():                        # world -> map (spawn yaw is 0 in the lab world)
        t = s['truth']
        return t.position.x - spawn[0], t.position.y - spawn[1], yaw_of(t.orientation)

    while 'truth' not in s:
        rclpy.spin_once(nav, timeout_sec=0.1)
    if P('set_initial_pose', True):         # = a perfect "2D Pose Estimate" click in rviz2
        nav.setInitialPose(pose(nav, *truth_map()))
    nav.waitUntilNav2Active()
    rows = []
    for i in range(1, runs + 1):
        for target in (start, goal):
            t0 = nav.get_clock().now()
            nav.goToPose(pose(nav, *target))
            rec = 0
            while not nav.isTaskComplete():
                fb = nav.getFeedback()
                rec = fb.number_of_recoveries if fb else rec
                if (nav.get_clock().now() - t0).nanoseconds > limit * 1e9:
                    nav.cancelTask()
            result = nav.getResult()
        dt = (nav.get_clock().now() - t0).nanoseconds * 1e-9
        end = nav.get_clock().now()
        while (nav.get_clock().now() - end).nanoseconds < 1e9:        # settle 1 s, keep callbacks running
            rclpy.spin_once(nav, timeout_sec=0.05)
        x, y, th = truth_map()
        a = s.get('amcl')
        amcl_err = math.hypot(a.position.x - x, a.position.y - y) if a else math.nan
        row = (1000 * (x - goal[0]), 1000 * (y - goal[1]), math.degrees(wrap(th - goal[2])), 1000 * amcl_err, dt, rec)
        rows.append(row)
        if i == 1:
            print('run  dx[mm]  dy[mm]  dth[deg]  amcl_err[mm]  t[s]  recov  result')
        print('%3d  %+6.0f  %+6.0f  %+8.1f  %12.0f  %4.0f  %5d  %s' % ((i,) + row + (result.name,)), flush=True)
    e = [math.hypot(r[0], r[1]) for r in rows]
    rms = math.sqrt(sum(v * v for v in e) / len(e))
    sd = st.stdev(e) if len(e) > 1 else math.nan
    print('radial error: mean %.0f mm, s %.0f mm, RMS %.0f mm (n = %d);  mean |dth| %.1f deg, max %.1f deg'
          % (st.mean(e), sd, rms, len(e), st.mean(abs(r[2]) for r in rows), max(abs(r[2]) for r in rows)))
    print('mean AMCL error %.0f mm;  mean run time %.0f s;  recoveries %d'
          % (st.mean(r[3] for r in rows), st.mean(r[4] for r in rows), sum(r[5] for r in rows)))
    print('compare with: ros2 param get /controller_server general_goal_checker.xy_goal_tolerance')
    nav.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
