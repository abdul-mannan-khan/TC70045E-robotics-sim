#!/usr/bin/env python3
"""SOLUTION - Week 3 activity: a security patrol through both rooms with Nav2.

Needs:  ros2 launch ~/labs/week03/launch/nav.launch.py gui:=true
Run:    python3 ~/labs/solutions/week03/patrol.py [laps]

Visits the waypoints in order, LAPS times, one goal at a time. For every waypoint it prints the result and the
time; a waypoint that fails (blocked, or not reached within the time limit) is reported and skipped - the patrol
goes on. At the end: how many waypoints were reached, the total time and the mean time per waypoint.
"""
import math
import sys

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

# Waypoints in the MAP frame (x m, y m, yaw deg) - read with "Publish Point" in RViz (ros2 topic echo /clicked_point).
WAYPOINTS = [
    ('doorway between the rooms', 4.0, -1.0, 0),
    ('room 2, upper side', 5.0, 3.0, 90),
    ('room 2, lower side', 4.8, -2.8, -90),
    ('room 1, upper side', 2.5, 3.0, 180),
    ('start', 0.0, 0.0, 180),
]
TIME_LIMIT = 90.0          # seconds of simulation time per waypoint


def make_pose(nav, x, y, yaw_deg):
    p = PoseStamped()
    p.header.frame_id = 'map'
    p.header.stamp = nav.get_clock().now().to_msg()
    p.pose.position.x, p.pose.position.y = x, y
    p.pose.orientation.z = math.sin(math.radians(yaw_deg) / 2)
    p.pose.orientation.w = math.cos(math.radians(yaw_deg) / 2)
    return p


def visit(nav, x, y, yaw):
    """Drive to one waypoint. Returns (reached, seconds)."""
    nav.clearAllCostmaps()                         # forget obstacles that have gone (e.g. a box someone removed)
    t0 = nav.get_clock().now()
    nav.goToPose(make_pose(nav, x, y, yaw))
    while not nav.isTaskComplete():
        rclpy.spin_once(nav, timeout_sec=0.1)
        if (nav.get_clock().now() - t0).nanoseconds * 1e-9 > TIME_LIMIT:
            nav.cancelTask()                       # give up on this waypoint, carry on with the next one
    seconds = (nav.get_clock().now() - t0).nanoseconds * 1e-9
    return nav.getResult() == TaskResult.SUCCEEDED, seconds


def main():
    laps = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    rclpy.init()
    nav = BasicNavigator()
    # Wait for Nav2 only. (The default, localizer='amcl', RESETS AMCL to (0, 0) if this script does not hear the
    # robot's pose at once - wrong whenever the robot is not at the start. nav.launch.py sets the start pose.)
    nav.waitUntilNav2Active(localizer='controller_server')
    reached, times = 0, []
    for lap in range(1, laps + 1):
        for name, x, y, yaw in WAYPOINTS:
            ok, seconds = visit(nav, x, y, yaw)
            times.append(seconds)
            reached += ok
            print('lap %d  %-26s %-8s %5.1f s' % (lap, name, 'REACHED' if ok else 'FAILED', seconds))
    total = len(WAYPOINTS) * laps
    print('RESULT %d of %d waypoints reached, total %.0f s, mean %.1f s per waypoint'
          % (reached, total, sum(times), sum(times) / len(times)))
    rclpy.shutdown()


if __name__ == '__main__':
    main()
