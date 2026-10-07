#!/usr/bin/env python3
"""go_to.py - send ONE goal to Nav2 from Python, and watch it being reached.

Needs:  ros2 launch ~/labs/week03/launch/nav.launch.py gui:=true      (robot + map + AMCL + Nav2 + RViz)
Run:    python3 ~/labs/week03/scripts/go_to.py 3.0 1.0 90
        x y in metres in the MAP frame (read them with "Publish Point" in RViz: ros2 topic echo /clicked_point),
        yaw in degrees (0 = facing +x, 90 = facing +y)

This is what "2D Goal Pose" in RViz does, written as a program: nav2_simple_commander's BasicNavigator sends the
goal to Nav2's navigate_to_pose action, prints the distance remaining while the robot drives, and reports
SUCCEEDED / CANCELED / FAILED and the time it took.
"""
import math
import sys

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult


def make_pose(nav, x, y, yaw_deg):
    p = PoseStamped()
    p.header.frame_id = 'map'
    p.header.stamp = nav.get_clock().now().to_msg()
    p.pose.position.x, p.pose.position.y = x, y
    p.pose.orientation.z = math.sin(math.radians(yaw_deg) / 2)
    p.pose.orientation.w = math.cos(math.radians(yaw_deg) / 2)
    return p


def main():
    x, y = float(sys.argv[1]), float(sys.argv[2])
    yaw = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    rclpy.init()
    nav = BasicNavigator()
    # Wait for Nav2 only. (The default, localizer='amcl', RESETS AMCL to (0, 0) if this script does not hear the
    # robot's pose at once - wrong whenever the robot is not at the start. nav.launch.py sets the start pose.)
    nav.waitUntilNav2Active(localizer='controller_server')
    t0 = nav.get_clock().now()
    nav.goToPose(make_pose(nav, x, y, yaw))
    i = 0
    while not nav.isTaskComplete():
        fb = nav.getFeedback()
        if fb and i % 10 == 0:
            print('distance remaining %.2f m' % fb.distance_remaining)
        i += 1
        rclpy.spin_once(nav, timeout_sec=0.1)
    seconds = (nav.get_clock().now() - t0).nanoseconds * 1e-9
    names = {TaskResult.SUCCEEDED: 'SUCCEEDED', TaskResult.CANCELED: 'CANCELED', TaskResult.FAILED: 'FAILED'}
    print('RESULT %s after %.1f s (simulation time)' % (names.get(nav.getResult(), 'UNKNOWN'), seconds))
    rclpy.shutdown()


if __name__ == '__main__':
    main()
