"""Spawn one TC70045E lab robot into a running Gazebo, with its helper nodes.

  ros2 launch tc70045e_sim robot.launch.py namespace:=robot1 x:=0 y:=0 yaw:=0

Nodes started (all in the robot's namespace):
  robot_state_publisher   URDF -> static transforms (frames prefixed with "<namespace>/" when a namespace is given)
  wheel_odometry          wheel_speeds, vel_raw, odom_raw and TF odom -> base_footprint (off with odom_tf:=false)
  magnetometer            imu/mag
  stereo_depth            D455-style camera/... topics (only with camera:=true)
  battery                 battery, voltage, power/current, power/rails
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def setup(context):
    ns = LaunchConfiguration('namespace').perform(context).strip('/')
    prefix = ns + '/' if ns else ''
    camera = LaunchConfiguration('camera').perform(context)
    odom_tf = LaunchConfiguration('odom_tf').perform(context) == 'true'
    sim_time = {'use_sim_time': True}
    xacro_file = os.path.join(get_package_share_directory('tc70045e_sim'), 'urdf', 'lab_robot.urdf.xacro')
    urdf = ParameterValue(Command(['xacro ', xacro_file, ' prefix:=', prefix, ' camera:=', camera,
                                   ' camera_rate:=', LaunchConfiguration('camera_rate'),
                                   ' camera_width:=', LaunchConfiguration('camera_width'),
                                   ' camera_height:=', LaunchConfiguration('camera_height')]), value_type=str)
    spawn_args = ['-entity', ns or 'lab_robot', '-topic', 'robot_description',
                  '-x', LaunchConfiguration('x'), '-y', LaunchConfiguration('y'), '-z', '0.01',
                  '-Y', LaunchConfiguration('yaw')]
    if ns:
        spawn_args += ['-robot_namespace', '/' + ns]
    nodes = [
        Node(package='robot_state_publisher', executable='robot_state_publisher', namespace=ns,
             parameters=[{'robot_description': urdf}, sim_time]),
        Node(package='gazebo_ros', executable='spawn_entity.py', namespace=ns, output='screen', arguments=spawn_args),
        Node(package='tc70045e_sim', executable='wheel_odometry', namespace=ns, output='screen',
             parameters=[sim_time, {'frame_prefix': prefix, 'publish_tf': odom_tf}]),
        Node(package='tc70045e_sim', executable='magnetometer', namespace=ns,
             parameters=[sim_time, {'frame_id': prefix + 'imu_link'}]),
        Node(package='tc70045e_sim', executable='battery', namespace=ns, parameters=[sim_time]),
    ]
    if camera == 'true':
        nodes.append(Node(package='tc70045e_sim', executable='stereo_depth', namespace=ns, parameters=[sim_time]))
    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value=''),
        DeclareLaunchArgument('x', default_value='-3.0'),
        DeclareLaunchArgument('y', default_value='-0.4'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('camera', default_value='true'),
        DeclareLaunchArgument('camera_rate', default_value='15'),
        DeclareLaunchArgument('camera_width', default_value='848'),
        DeclareLaunchArgument('camera_height', default_value='480'),
        DeclareLaunchArgument('odom_tf', default_value='true',
                              description='false when an EKF publishes odom -> base_footprint instead'),
        OpaqueFunction(function=setup),
    ])
