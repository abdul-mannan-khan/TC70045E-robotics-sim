#!/usr/bin/env python3
"""three_goals.py - send three Nav2 goals on the camera-only map and score each against the truth (Week 7).

Needs: ros2 launch ~/labs/week07/launch/rgbd_nav.launch.py mode:=localization nav:=true
Run:   python3 ~/labs/week07/scripts/three_goals.py

For each goal (map frame = where the robot started when the map was made) it prints the Nav2 result, the time,
and how far the robot REALLY stopped from the goal - measured with /ground_truth/odom (a test harness: Nav2 and
RTAB-Map never see it). A goal that is not reached within the time limit is cancelled and the next one is tried.
Expected (measured, see the README): REACHED for all three, stopping 0.1-0.3 m from the goal.
"""
import math

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from nav_msgs.msg import Odometry

# goals in the MAP frame (x m, y m, yaw deg); the map frame starts at the robot's spawn pose (world -3.0, -0.4)
GOALS = [('room 1, upper side', 1.5, 2.6, 90), ('the doorway', 4.0, -1.0, 0), ('room 2, by the crate', 5.2, -0.4, 0)]
SPAWN = (-3.0, -0.4)
TIME_LIMIT = 120.0


def make_pose(nav, x, y, yaw_deg):
    p = PoseStamped()
    p.header.frame_id = 'map'
    p.header.stamp = nav.get_clock().now().to_msg()
    p.pose.position.x, p.pose.position.y = x, y
    p.pose.orientation.z, p.pose.orientation.w = math.sin(math.radians(yaw_deg) / 2), math.cos(math.radians(yaw_deg) / 2)
    return p


def main():
    rclpy.init()
    nav = BasicNavigator()
    truth = {}
    nav.create_subscription(Odometry, '/ground_truth/odom',
                            lambda m: truth.update(x=m.pose.pose.position.x, y=m.pose.pose.position.y), 10)
    nav.waitUntilNav2Active(localizer='controller_server')     # RTAB-Map localises, not AMCL
    reached = 0
    for name, x, y, yaw in GOALS:
        t0 = nav.get_clock().now()
        nav.goToPose(make_pose(nav, x, y, yaw))
        while not nav.isTaskComplete():
            rclpy.spin_once(nav, timeout_sec=0.1)
            if (nav.get_clock().now() - t0).nanoseconds * 1e-9 > TIME_LIMIT:
                nav.cancelTask()
        sec = (nav.get_clock().now() - t0).nanoseconds * 1e-9
        ok = nav.getResult() == TaskResult.SUCCEEDED
        reached += ok
        for _ in range(10):
            rclpy.spin_once(nav, timeout_sec=0.05)
        miss = math.hypot(truth['x'] - SPAWN[0] - x, truth['y'] - SPAWN[1] - y) if truth else float('nan')
        print('%-22s %-8s %5.1f s   really stopped %.2f m from the goal' % (name, 'REACHED' if ok else 'FAILED', sec, miss),
              flush=True)
    print('RESULT %d of %d goals reached' % (reached, len(GOALS)), flush=True)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
