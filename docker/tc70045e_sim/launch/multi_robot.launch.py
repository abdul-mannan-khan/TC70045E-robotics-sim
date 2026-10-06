"""Two lab robots in one world, each in its own namespace (Week 12).

  ros2 launch tc70045e_sim multi_robot.launch.py gui:=false
Robot 1: namespace robot1, frames robot1/..., spawned at (-3.0, -0.4)
Robot 2: namespace robot2, frames robot2/..., spawned at ( 3.0, -1.0), facing west
Cameras are off by default (camera:=true turns them on - two cameras need a strong laptop).
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    share = os.path.join(get_package_share_directory('tc70045e_sim'), 'launch')
    robot = os.path.join(share, 'robot.launch.py')
    cam = LaunchConfiguration('camera')
    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('camera', default_value='false'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(share, 'world.launch.py')),
                                 launch_arguments={'world': 'lab', 'gui': LaunchConfiguration('gui')}.items()),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(robot), launch_arguments={
            'namespace': 'robot1', 'x': '-3.0', 'y': '-0.4', 'camera': cam}.items()),
        TimerAction(period=3.0, actions=[
            IncludeLaunchDescription(PythonLaunchDescriptionSource(robot), launch_arguments={
                'namespace': 'robot2', 'x': '3.0', 'y': '-1.0', 'yaw': '3.14159', 'camera': cam}.items())]),
    ])
