"""Week 8 - autonomous exploration: the robot maps an unknown building by itself.

One launch file, the Week 2 and Week 3 bricks together:
  robot     tc70045e_sim/sim.launch.py      the lab robot in Gazebo (camera off)
  slam      slam_toolbox (Week 2)           builds /map from nothing, publishes TF map -> odom; it uses the laser
                                            only up to lidar_range (default 3.5 m): the robot must GO to places to map them
  nav2      nav2_bringup navigation_launch  planner + controller on the GROWING map (no AMCL, no map_server);
                                            not started with brain:=wander
  rviz      rviz2 with week08/rviz/explore.rviz   map, costmaps, plan, robot
  coverage  week08/scripts/coverage.py      prints the explored area every 30 s
  brain     brain:=wander    Week 2's wander brick + safety brick (reactive driving, no plan) - the baseline
            brain:=none      nothing drives: run YOUR explorer.py in a second terminal

Usage (in the container):
  ros2 launch ~/labs/week08/launch/explore.launch.py brain:=wander        # A1: how far does luck get you?
  ros2 launch ~/labs/week08/launch/explore.launch.py                      # then, T2: python3 .../explorer.py
  ... world:=lab                       the lab WITH its 8 cm step (below the laser): watch what a LiDAR-only robot does
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

WEEK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABS = os.path.dirname(WEEK)
DEFAULTS = {'brain': 'none', 'gui': 'true', 'rviz': 'true', 'time_limit': '600.0', 'lidar_range': '3.5', 'world': 'nostep'}


def lab_without_step(share):
    """The lab world without its 8 cm low step: the step is below the laser, so a LiDAR-only robot drives into it and
    gets stuck (measured: wander stuck at the step in 3 of 4 runs). world:=lab keeps it - try it and watch."""
    s = open(os.path.join(share, 'worlds', 'lab.world')).read()
    a = s.index('<model name="low_step">')
    s = s[:a] + s[s.index('</model>', a) + len('</model>'):]
    path = '/tmp/week08_lab_nostep.world'
    open(path, 'w').write(s)
    return path


def bricks(context):
    arg = lambda name: LaunchConfiguration(name).perform(context)
    sim_share = get_package_share_directory('tc70045e_sim')
    out = [IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(sim_share, 'launch', 'sim.launch.py')),
        launch_arguments={'gui': arg('gui'), 'camera': 'false',
                          'world': lab_without_step(sim_share) if arg('world') == 'nostep' else arg('world')}.items()),
        Node(package='slam_toolbox', executable='async_slam_toolbox_node', name='slam_toolbox', output='log',
             parameters=[os.path.join(sim_share, 'config', 'slam_toolbox.yaml'),     # the map uses only the first
                         {'use_sim_time': True, 'max_laser_range': float(arg('lidar_range'))}]),   # lidar_range m
        ExecuteProcess(cmd=['python3', os.path.join(WEEK, 'scripts', 'coverage.py'), '--ros-args',
                            '-p', 'use_sim_time:=true', '-p', 'time_limit:=' + arg('time_limit')], output='screen')]
    if arg('brain') != 'wander':                                      # Nav2 only for a planning brain: with no goal
        out.append(TimerAction(period=8.0, actions=[IncludeLaunchDescription(  # it still publishes zero /cmd_vel,
            PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('nav2_bringup'), 'launch',
                                                       'navigation_launch.py')),          # which would stop wander
            launch_arguments={'use_sim_time': 'true', 'autostart': 'true',
                              'params_file': os.path.join(LABS, 'week03', 'config', 'nav2_params.yaml')}.items())]))
    if arg('rviz') == 'true':
        out.append(Node(package='rviz2', executable='rviz2', output='log',
                        arguments=['-d', os.path.join(WEEK, 'rviz', 'explore.rviz')],
                        parameters=[{'use_sim_time': True}]))
    if arg('brain') == 'wander':                                      # exactly the Week 2 explorer: wander -> safety
        out.append(ExecuteProcess(cmd=['python3', os.path.join(LABS, 'week02', 'scripts', 'safety_stop.py')],
                                  output='screen'))
        out.append(TimerAction(period=15.0, actions=[ExecuteProcess(
            cmd=['python3', os.path.join(LABS, 'week02', 'scripts', 'wander.py'), '--ros-args',
                 '-r', 'cmd_vel:=cmd_vel_in'], output='screen')]))
    return out


def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument(k, default_value=v) for k, v in DEFAULTS.items()]
                             + [OpaqueFunction(function=bricks)])
