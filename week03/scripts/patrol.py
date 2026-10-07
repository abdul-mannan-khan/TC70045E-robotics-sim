#!/usr/bin/env python3
"""patrol.py - YOUR Week 3 activity: a security patrol through both rooms with Nav2.

Needs:  ros2 launch ~/labs/week03/launch/nav.launch.py gui:=true
Run:    python3 ~/labs/week03/scripts/patrol.py [laps]

The robot must visit your waypoints in order, LAPS times, and report for every waypoint whether it was reached and
how long it took. A waypoint that cannot be reached must not stop the patrol: report it and go on to the next one.
There are three TODOs below. go_to.py (same folder) shows how to send one goal - start from it.
"""
import math
import sys

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

# TODO 1 (Week 3 activity): choose at least FOUR waypoints that take the robot through BOTH rooms and back to the
#   start. Find the coordinates in RViz: select "Publish Point", click on the map, and read x and y in a terminal
#   running  ros2 topic echo /clicked_point . Keep each waypoint at least 0.5 m away from walls and furniture.
#   Format: (name, x in metres, y in metres, yaw in degrees)  - all in the MAP frame.
WAYPOINTS = [
    ('start', 0.0, 0.0, 0),
]
TIME_LIMIT = 90.0          # seconds of simulation time allowed per waypoint


def make_pose(nav, x, y, yaw_deg):
    p = PoseStamped()
    p.header.frame_id = 'map'
    p.header.stamp = nav.get_clock().now().to_msg()
    p.pose.position.x, p.pose.position.y = x, y
    p.pose.orientation.z = math.sin(math.radians(yaw_deg) / 2)
    p.pose.orientation.w = math.cos(math.radians(yaw_deg) / 2)
    return p


def visit(nav, x, y, yaw):
    """Drive to one waypoint. Must return (reached, seconds)."""
    # TODO 2: send the goal with nav.goToPose(make_pose(nav, x, y, yaw)), then wait in a loop until
    #   nav.isTaskComplete() is True (call rclpy.spin_once(nav, timeout_sec=0.1) inside the loop).
    #   If more than TIME_LIMIT seconds pass (use nav.get_clock().now() before and inside the loop),
    #   call nav.cancelTask() so the patrol can go on.
    #   reached = (nav.getResult() == TaskResult.SUCCEEDED)
    reached, seconds = False, 0.0
    return reached, seconds


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
    # TODO 3: print one RESULT line: how many waypoints were reached out of how many, the total time and the
    #   mean time per waypoint, e.g.  RESULT 8 of 8 waypoints reached, total 212 s, mean 26.5 s per waypoint
    rclpy.shutdown()


if __name__ == '__main__':
    main()
