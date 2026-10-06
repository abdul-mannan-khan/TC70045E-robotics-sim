"""The Week 5 experiment in one command: (optionally) the simulated lab robot + the sensor monitor.

  ros2 launch lab_sensing monitor_launch.py                      # monitor only (simulator already running)
  ros2 launch lab_sensing monitor_launch.py with_sim:=true       # simulator (no GUI, no camera) + monitor
  ros2 launch lab_sensing monitor_launch.py expected_hz:=50.0    # override one parameter from the YAML
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

DEFAULT_PARAMS = os.path.expanduser('~/labs/week05/params/sensor_monitor_params.yaml')


def generate_launch_description():
    sim_launch = os.path.join(get_package_share_directory('tc70045e_sim'), 'launch', 'sim.launch.py')
    return LaunchDescription([
        DeclareLaunchArgument('monitor_params', default_value=DEFAULT_PARAMS),   # not 'params_file': the
        # simulator's launch files use that name and launch arguments are global - a real integration trap
        DeclareLaunchArgument('expected_hz', default_value='100.0'),
        DeclareLaunchArgument('with_sim', default_value='false'),

        IncludeLaunchDescription(PythonLaunchDescriptionSource(sim_launch),
                                 launch_arguments={'gui': 'false', 'camera': 'false'}.items(),
                                 condition=IfCondition(LaunchConfiguration('with_sim'))),

        Node(package='lab_sensing', executable='sensor_monitor', name='sensor_monitor', output='screen',
             parameters=[LaunchConfiguration('monitor_params'),
                         {'expected_hz': LaunchConfiguration('expected_hz')}]),
    ])
