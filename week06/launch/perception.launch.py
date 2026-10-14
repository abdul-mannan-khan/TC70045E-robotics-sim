"""Week 6 - see and understand with the D455: find objects and put them on the map.

One launch file, the Week 4 bricks without the second SLAM:
  robot    tc70045e_sim/sim.launch.py      the lab robot in Gazebo with the D455 camera (424 x 240)
  slam     slam_toolbox (Week 2)           the map, and TF map -> odom
  rviz     rviz2 with week06/rviz/perception.rviz   map, robot, camera image, mask image, depth cloud, the /boxes markers
  tour     week06/scripts/tour.py          drives past the red and the green box and stops to look at each

Your brick, box_finder.py, runs in a second terminal (so you see what it prints):
  python3 ~/labs/week06/scripts/box_finder.py --ros-args -p use_sim_time:=true

Usage (in the container):
  ros2 launch ~/labs/week06/launch/perception.launch.py                    # robot + camera + SLAM + RViz
  ros2 launch ~/labs/week06/launch/perception.launch.py tour:=true         # ... and drive the tour
  ros2 launch ~/labs/week06/launch/perception.launch.py tour:=true turn_rate:=0.6   # TODO 3: turn faster
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

WEEK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULTS = {'gui': 'true', 'rviz': 'true', 'tour': 'false', 'turn_rate': '0.3'}


def bricks(context):
    arg = lambda name: LaunchConfiguration(name).perform(context)
    sim_share = get_package_share_directory('tc70045e_sim')
    out = [IncludeLaunchDescription(                                  # robot + camera bricks
        PythonLaunchDescriptionSource(os.path.join(sim_share, 'launch', 'sim.launch.py')),
        launch_arguments={'gui': arg('gui'), 'camera': 'true',
                          'camera_width': '424', 'camera_height': '240'}.items()),
        IncludeLaunchDescription(                                     # slam brick, Week 2
            PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('slam_toolbox'), 'launch',
                                                       'online_async_launch.py')),
            launch_arguments={'use_sim_time': 'true',
                              'slam_params_file': os.path.join(sim_share, 'config', 'slam_toolbox.yaml')}.items())]
    if arg('rviz') == 'true':
        out.append(Node(package='rviz2', executable='rviz2', output='log',
                        arguments=['-d', os.path.join(WEEK, 'rviz', 'perception.rviz')],
                        parameters=[{'use_sim_time': True}]))
    if arg('tour') == 'true':
        out.append(TimerAction(period=25.0, actions=[ExecuteProcess(   # let Gazebo, camera and SLAM start first
            cmd=['python3', os.path.join(WEEK, 'scripts', 'tour.py'), '--ros-args', '-p', 'use_sim_time:=true',
                 '-p', 'turn_rate:=' + arg('turn_rate')], output='screen')]))
    return out


def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument(k, default_value=v) for k, v in DEFAULTS.items()]
                             + [OpaqueFunction(function=bricks)])
