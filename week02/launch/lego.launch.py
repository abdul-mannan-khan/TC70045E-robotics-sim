"""Snap ROS 2 bricks together with on/off switches - the Week 2 'Lego' launch file.

Usage (inside the container):
  ros2 launch ~/labs/week02/launch/lego.launch.py                                   # robot + rviz only
  ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true                        # + mapping
  ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true wander:=true safety:=true   # an explorer
  ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true nav:=true              # click goals in rviz

Bricks (each one is an existing package or a Week 2 script):
  sim      tc70045e_sim sim.launch.py        the robot (simulated): /scan /imu/data_raw /odom_raw, TF, eats /cmd_vel
  camera   the robot's D455-style camera     /camera/color/image_raw, /camera/aligned_depth_to_color/image_raw (424x240)
  rviz     rviz2 + week02/rviz/lego.rviz     shows robot, laser, map, path
  slam     slam_toolbox (online async)       /scan + TF  ->  /map and TF map->odom
  nav      nav2_bringup navigation_launch    /map + /scan + a goal  ->  /cmd_vel  (needs slam:=true)
  safety   week02/scripts/safety_stop.py     /cmd_vel_in + /scan  ->  /cmd_vel
  wander   week02/scripts/wander.py          /scan  ->  cmd_vel (to /cmd_vel_in when safety:=true)
Keyboard driving needs its own terminal (it reads the keys):
  ros2 run teleop_twist_keyboard teleop_twist_keyboard                                    # without safety
  ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_in  # with safety:=true
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

HERE = os.path.dirname(os.path.realpath(__file__))
WEEK = os.path.dirname(HERE)
SWITCHES = {'gui': 'false', 'rviz': 'true', 'camera': 'false', 'slam': 'false', 'nav': 'false', 'safety': 'false',
            'wander': 'false'}


def bricks(context):
    on = {k: LaunchConfiguration(k).perform(context) == 'true' for k in SWITCHES}
    sim_share = get_package_share_directory('tc70045e_sim')
    out = [IncludeLaunchDescription(  # the robot brick - always on
        PythonLaunchDescriptionSource(os.path.join(sim_share, 'launch', 'sim.launch.py')),
        launch_arguments={'gui': 'true' if on['gui'] else 'false', 'camera': 'true' if on['camera'] else 'false',
                          'camera_width': '424', 'camera_height': '240'}.items())]   # D455-style RGB-D camera
    if on['rviz']:
        out.append(Node(package='rviz2', executable='rviz2', arguments=['-d', os.path.join(WEEK, 'rviz', 'lego.rviz'),
                                   '-f', 'map' if on['slam'] else 'odom'],   # view from the map once there is one
                        parameters=[{'use_sim_time': True}], output='log'))
    if on['slam']:
        out.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('slam_toolbox'), 'launch',
                                                       'online_async_launch.py')),
            launch_arguments={'use_sim_time': 'true',
                              'slam_params_file': os.path.join(sim_share, 'config', 'slam_toolbox.yaml')}.items()))
    if on['nav']:
        out.append(TimerAction(period=15.0, actions=[IncludeLaunchDescription(  # wait for the map to exist
            PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('nav2_bringup'), 'launch',
                                                       'navigation_launch.py')),
            launch_arguments={'use_sim_time': 'true',
                              'params_file': os.path.join(sim_share, 'config', 'nav2_params.yaml')}.items())]))
    if on['safety']:
        out.append(ExecuteProcess(cmd=['python3', os.path.join(WEEK, 'scripts', 'safety_stop.py')], output='screen'))
    if on['wander']:
        target = 'cmd_vel_in' if on['safety'] else 'cmd_vel'
        out.append(TimerAction(period=12.0, actions=[ExecuteProcess(  # let Gazebo spawn the robot first
            cmd=['python3', os.path.join(WEEK, 'scripts', 'wander.py'), '--ros-args', '-r', 'cmd_vel:=' + target],
            output='screen')]))
    return out


def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument(k, default_value=v, description='brick on/off')
                              for k, v in SWITCHES.items()] + [OpaqueFunction(function=bricks)])
