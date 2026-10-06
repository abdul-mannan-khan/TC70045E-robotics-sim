"""Start the whole Week 1 control loop - sensor, controller and actuator - with one command.

Usage    ros2 launch ~/labs/week01/scripts/thermal_loop.launch.py
         ros2 launch ~/labs/week01/scripts/thermal_loop.launch.py setpoint:=24.0
The three programs are plain Python files rather than an installed package, so they are started with
ExecuteProcess. From Week 5 you build proper packages with colcon and use Node(...) instead.
"""
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration

HERE = os.path.dirname(os.path.realpath(__file__))


def generate_launch_description():
    setpoint = LaunchConfiguration('setpoint')
    return LaunchDescription([
        DeclareLaunchArgument('setpoint', default_value='26.0', description='temperature setpoint, degrees C'),
        ExecuteProcess(cmd=['python3', os.path.join(HERE, 'room_sensor.py')], output='screen'),
        ExecuteProcess(cmd=['python3', os.path.join(HERE, 'fan_driver.py')], output='screen'),
        ExecuteProcess(cmd=['python3', os.path.join(HERE, 'fan_controller.py'),
                            '--ros-args', '-p', ['setpoint:=', setpoint]], output='screen'),
    ])
