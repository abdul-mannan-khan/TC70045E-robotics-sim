#!/usr/bin/env python3
"""set_start_pose.py - tell AMCL where the robot starts, and keep telling it until AMCL confirms.

Started by nav.launch.py; you can also run it yourself if the robot is lost at the start:
    python3 ~/labs/week03/scripts/set_start_pose.py [x y yaw_deg]        (map frame; default 0 0 0)

Why not publish /initialpose once? On a slow first start, Gazebo, the TF tree or AMCL may not be ready yet and the
message is lost or rejected ("Failed to transform initial pose in time"). This script waits until AMCL listens,
sends the pose stamped "latest available transform" (time 0), and repeats every 2 s until /amcl_pose is within
0.3 m of it - or gives up after 120 s and says so.
"""
import math
import sys
import time

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped


def main():
    x, y, yaw = (float(v) for v in sys.argv[1:4]) if len(sys.argv) >= 4 else (0.0, 0.0, 0.0)
    rclpy.init()
    node = rclpy.create_node('set_start_pose')
    pub = node.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
    got = {}
    node.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', lambda m: got.update(p=m.pose.pose.position), 10)

    msg = PoseWithCovarianceStamped()
    msg.header.frame_id = 'map'                       # stamp left at 0 = use the latest transform
    msg.pose.pose.position.x, msg.pose.pose.position.y = x, y
    msg.pose.pose.orientation.z, msg.pose.pose.orientation.w = math.sin(math.radians(yaw) / 2), math.cos(math.radians(yaw) / 2)
    msg.pose.covariance[0] = msg.pose.covariance[7] = 0.05
    msg.pose.covariance[35] = 0.03

    t0, last = time.time(), 0.0
    while time.time() - t0 < 120.0:
        rclpy.spin_once(node, timeout_sec=0.2)
        p = got.get('p')
        if p is not None and math.hypot(p.x - x, p.y - y) < 0.3:
            node.get_logger().info('AMCL confirmed the start pose: (%.2f, %.2f) after %.0f s' % (p.x, p.y, time.time() - t0))
            break
        if pub.get_subscription_count() > 0 and time.time() - last > 2.0:
            got.pop('p', None)                        # only accept an answer to this message
            pub.publish(msg)
            last = time.time()
    else:
        node.get_logger().error('AMCL did not confirm the start pose within 120 s - use "2D Pose Estimate" in RViz')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
