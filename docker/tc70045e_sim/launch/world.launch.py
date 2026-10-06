"""Start Gazebo Classic with one of the TC70045E worlds.

  ros2 launch tc70045e_sim world.launch.py world:=lab gui:=true
  world: lab (10 m x 8 m laboratory, default) | range (target wall for range tests) | a path to any .world file
  gui:   true opens the Gazebo window; false runs the server only (faster on a laptop without a GPU)
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def resolve(context):
    share = get_package_share_directory('tc70045e_sim')
    world = LaunchConfiguration('world').perform(context)
    path = world if world.endswith('.world') else os.path.join(share, 'worlds', world + '.world')
    gz = get_package_share_directory('gazebo_ros')
    return [
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(gz, 'launch', 'gzserver.launch.py')),
                                 launch_arguments={'world': path, 'verbose': 'false',
                                                   'params_file': os.path.join(share, 'config', 'gazebo.yaml')}.items()),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(gz, 'launch', 'gzclient.launch.py')),
                                 condition=IfCondition(LaunchConfiguration('gui'))),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='lab'),
        DeclareLaunchArgument('gui', default_value='true'),
        OpaqueFunction(function=resolve),
    ])
