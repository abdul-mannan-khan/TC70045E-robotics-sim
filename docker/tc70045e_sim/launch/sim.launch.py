"""The whole simulated lab robot in one command (Gazebo world + robot + helper nodes).

  ros2 launch tc70045e_sim sim.launch.py                            # laboratory world, Gazebo window, camera on
  ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false   # lightest: LiDAR, IMU and odometry only
  ros2 launch tc70045e_sim sim.launch.py world:=range x:=0 y:=0     # range-test world, robot facing the target wall
  ros2 launch tc70045e_sim sim.launch.py odom_tf:=false             # when robot_localization (EKF) owns odom -> base
  ros2 launch tc70045e_sim sim.launch.py camera_width:=424 camera_height:=240   # faster camera on a slow laptop

Drive it:  ros2 run teleop_twist_keyboard teleop_twist_keyboard     (Shift + J / L moves sideways)
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

DEFAULTS = {'world': 'lab', 'gui': 'true', 'x': '-3.0', 'y': '-0.4', 'yaw': '0.0', 'camera': 'true',
            'camera_rate': '15', 'camera_width': '848', 'camera_height': '480', 'odom_tf': 'true'}
ROBOT_ARGS = ['x', 'y', 'yaw', 'camera', 'camera_rate', 'camera_width', 'camera_height', 'odom_tf']


def generate_launch_description():
    share = os.path.join(get_package_share_directory('tc70045e_sim'), 'launch')
    return LaunchDescription(
        [DeclareLaunchArgument(k, default_value=v) for k, v in DEFAULTS.items()] + [
            IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(share, 'world.launch.py')),
                                     launch_arguments={'world': LaunchConfiguration('world'),
                                                       'gui': LaunchConfiguration('gui')}.items()),
            IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(share, 'robot.launch.py')),
                                     launch_arguments={a: LaunchConfiguration(a) for a in ROBOT_ARGS}.items()),
        ])
