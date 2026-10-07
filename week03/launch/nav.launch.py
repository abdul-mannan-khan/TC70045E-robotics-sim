"""Week 3 - the navigation brick: from a map to autonomous delivery.

One launch file, five bricks:
  robot      tc70045e_sim/sim.launch.py        the lab robot in Gazebo (gui:=true shows the Gazebo window)
  map        nav2 map_server                   the saved map (default: the lab map in week03/maps)
  amcl       nav2 amcl                         "where am I on this map?" - particles matched to the LiDAR
  nav2       nav2 planner + controller + ...   plans a path on the map and follows it, avoiding obstacles
  rviz       rviz2 with week03/rviz/nav.rviz   map, particles, costmaps, plans, 2D Pose Estimate / 2D Goal Pose

Usage (in the container):
  ros2 launch ~/labs/week03/launch/nav.launch.py gui:=true
  ros2 launch ~/labs/week03/launch/nav.launch.py gui:=true map:=$HOME/labs/week02/my_map.yaml   # your Week 2 map

The robot starts where the map was started (the map origin), so AMCL is told "you are at (0, 0), facing +x"
automatically after Nav2 has come up. If it is lost, use "2D Pose Estimate" in RViz.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

WEEK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bricks(context):
    arg = lambda name: LaunchConfiguration(name).perform(context)
    sim_share = get_package_share_directory('tc70045e_sim')
    out = [IncludeLaunchDescription(                                  # robot brick
        PythonLaunchDescriptionSource(os.path.join(sim_share, 'launch', 'sim.launch.py')),
        launch_arguments={'gui': arg('gui'), 'camera': 'false'}.items())]
    if arg('rviz') == 'true':
        out.append(Node(package='rviz2', executable='rviz2', output='log',
                        arguments=['-d', os.path.join(WEEK, 'rviz', 'nav.rviz')],
                        parameters=[{'use_sim_time': True}]))
    out.append(TimerAction(period=8.0, actions=[IncludeLaunchDescription(   # map + amcl + nav2 bricks
        PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('nav2_bringup'), 'launch',
                                                   'bringup_launch.py')),
        launch_arguments={'map': arg('map'), 'use_sim_time': 'true', 'autostart': 'true',
                          'params_file': os.path.join(sim_share, 'config', 'nav2_params.yaml')}.items())]))
    out.append(TimerAction(period=20.0, actions=[ExecuteProcess(       # tell AMCL the start pose: map origin
        cmd=['ros2', 'topic', 'pub', '--times', '3', '--rate', '1', '/initialpose',
             'geometry_msgs/msg/PoseWithCovarianceStamped',
             '{header: {frame_id: map}, pose: {pose: {orientation: {w: 1.0}}, '
             'covariance: [0.05, 0, 0, 0, 0, 0, 0, 0.05, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '
             '0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.03]}}'],
        output='log')]))
    return out


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true', description='show the Gazebo window'),
        DeclareLaunchArgument('rviz', default_value='true', description='start RViz'),
        DeclareLaunchArgument('map', default_value=os.path.join(WEEK, 'maps', 'lab_map.yaml'),
                              description='map yaml file (map_server)'),
        OpaqueFunction(function=bricks)])
