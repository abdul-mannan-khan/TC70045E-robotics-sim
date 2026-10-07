#!/usr/bin/env python3
"""drop_box.py - put an obstacle into the Gazebo world (or take it away) while Nav2 is driving.

Run:    python3 ~/labs/week03/scripts/drop_box.py 1.5 0.0            a 0.4 m box at map (1.5, 0.0)
        python3 ~/labs/week03/scripts/drop_box.py --remove            remove it again

The map does not know about the box: Nav2 sees it only through the LiDAR, in the LOCAL costmap, and has to drive
round it (or, if the way is blocked, run its recovery behaviours and plan another way).
Coordinates are in the MAP frame. The map starts where the robot started, so world = map + (-3.0, -0.4).
"""
import sys

import rclpy
from gazebo_msgs.srv import DeleteEntity, SpawnEntity

SPAWN_X, SPAWN_Y = -3.0, -0.4          # where the robot starts in the Gazebo world (= the map origin)
NAME = 'week03_box'
BOX = """<sdf version="1.6"><model name="{n}"><static>true</static><link name="link">
  <collision name="c"><geometry><box><size>0.4 0.4 0.5</size></box></geometry></collision>
  <visual name="v"><geometry><box><size>0.4 0.4 0.5</size></box></geometry>
    <material><ambient>0.9 0.4 0.0 1</ambient><diffuse>0.9 0.4 0.0 1</diffuse></material></visual>
</link></model></sdf>"""


def call(node, client, request):
    if not client.wait_for_service(timeout_sec=10.0):
        sys.exit('Gazebo service %s not found - is the simulator running?' % client.srv_name)
    future = client.call_async(request)
    rclpy.spin_until_future_complete(node, future)
    return future.result()


def main():
    rclpy.init()
    node = rclpy.create_node('drop_box')
    if '--remove' in sys.argv:
        req = DeleteEntity.Request()
        req.name = NAME
        res = call(node, node.create_client(DeleteEntity, '/delete_entity'), req)
        print('removed' if res.success else 'nothing to remove: %s' % res.status_message)
    else:
        x, y = float(sys.argv[1]), float(sys.argv[2])
        req = SpawnEntity.Request()
        req.name, req.xml = NAME, BOX.format(n=NAME)
        req.initial_pose.position.x, req.initial_pose.position.y = x + SPAWN_X, y + SPAWN_Y
        req.initial_pose.position.z = 0.25
        res = call(node, node.create_client(SpawnEntity, '/spawn_entity'), req)
        print('box at map (%.2f, %.2f)' % (x, y) if res.success else 'failed: %s' % res.status_message)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
