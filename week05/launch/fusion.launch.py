"""Week 5 - fuse for better localisation: wheel odometry + IMU -> EKF -> SLAM.

One launch file, the Week 4 bricks plus three new ones:
  robot     tc70045e_sim/sim.launch.py       the lab robot in Gazebo, no camera this week (gui:=true shows Gazebo)
  gyro_cal  week05/scripts/gyro_bias.py      measures the gyro's turn-on bias in the first 11 s (robot still) and
                                             subtracts it: /imu/data_raw -> /imu/data_cal   (gyro_cal:=false skips it)
  imu       imu_filter_madgwick              gyro + accelerometer -> /imu/data (+ orientation)
  ekf       robot_localization ekf_node      /odom_raw + /imu/data -> /odometry/filtered and TF odom -> base_footprint
                                             settings: week05/config/ekf.yaml (your activity)
  slam      slam_toolbox (Week 2)            uses whichever odometry owns TF odom -> base_footprint
  rviz      rviz2 with week05/rviz/fusion.rviz   map, laser, robot, and three trails: truth, wheel odometry, EKF
  drive     week05/scripts/drive_and_score.py    drives the 24 m circuit and scores every estimate against the truth

The switch that matters:  odom:=raw   wheel odometry owns odom -> base_footprint (Weeks 2-4), EKF off
                          odom:=ekf   the EKF owns it (the simulator is started with odom_tf:=false)

Usage (in the container):
  ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=raw drive:=true             # A2: the baseline
  ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=ekf drive:=true             # with your ekf.yaml
  ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=ekf slam:=false drive:=true # odometry only, no SLAM
  ... gyro_cal:=false                                                                  # A4: an uncalibrated gyro
  ... turn_rate:=1.0 lidar_range:=3.5                                                  # a harder robot
  ... ekf_config:=$HOME/labs/solutions/week05/ekf.yaml                                 # the solution
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

WEEK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULTS = {'odom': 'ekf', 'gyro_cal': 'true', 'gui': 'true', 'rviz': 'true', 'slam': 'true', 'drive': 'false',
            'ekf_config': os.path.join(WEEK, 'config', 'ekf.yaml'),
            'speed': '0.15', 'turn_rate': '0.3', 'lidar_range': '12.0', 'laps': '1', 'csv': ''}


def bricks(context):
    arg = lambda name: LaunchConfiguration(name).perform(context)
    ekf = arg('odom') == 'ekf'
    sim_share = get_package_share_directory('tc70045e_sim')
    out = [IncludeLaunchDescription(                                  # robot brick (the EKF owns odom TF if on)
        PythonLaunchDescriptionSource(os.path.join(sim_share, 'launch', 'sim.launch.py')),
        launch_arguments={'gui': arg('gui'), 'camera': 'false',
                          'odom_tf': 'false' if ekf else 'true'}.items()),
        Node(package='imu_filter_madgwick', executable='imu_filter_madgwick_node', name='imu_filter',
             output='log',                                            # imu brick: gyro + accel -> orientation
             parameters=[{'use_sim_time': True, 'use_mag': False, 'publish_tf': False,
                          'world_frame': 'enu', 'gain': 0.1}],
             remappings=[('imu/data_raw', '/imu/data_cal' if arg('gyro_cal') == 'true' else '/imu/data_raw')])]
    if arg('gyro_cal') == 'true':                                     # gyro calibration brick
        out.append(ExecuteProcess(cmd=['python3', os.path.join(WEEK, 'scripts', 'gyro_bias.py'), '--ros-args',
                                       '-p', 'use_sim_time:=true'], output='screen'))
    if ekf:                                                           # ekf brick
        out.append(Node(package='robot_localization', executable='ekf_node', name='ekf_filter_node',
                        output='screen', parameters=[arg('ekf_config'), {'use_sim_time': True}]))
    if arg('slam') == 'true':                                         # slam brick, Week 2 settings
        out.append(Node(package='slam_toolbox', executable='async_slam_toolbox_node', name='slam_toolbox',
                        output='log',
                        parameters=[os.path.join(sim_share, 'config', 'slam_toolbox.yaml'),
                                    {'use_sim_time': True, 'max_laser_range': float(arg('lidar_range'))}]))
    else:                                                             # no SLAM: map = odom, so RViz still works
        out.append(Node(package='tf2_ros', executable='static_transform_publisher', output='log',
                        arguments=['--frame-id', 'map', '--child-frame-id', 'odom'],
                        parameters=[{'use_sim_time': True}]))
    if arg('rviz') == 'true':
        out.append(Node(package='rviz2', executable='rviz2', output='log',
                        arguments=['-d', os.path.join(WEEK, 'rviz', 'fusion.rviz')],
                        parameters=[{'use_sim_time': True}]))
    score = ['python3', os.path.join(WEEK, 'scripts', 'drive_and_score.py'), '--ros-args',
             '-p', 'use_sim_time:=true', '-p', 'drive:=' + arg('drive'), '-p', 'speed:=' + arg('speed'),
             '-p', 'turn_rate:=' + arg('turn_rate'), '-p', 'laps:=' + arg('laps')]
    if arg('csv'):
        score += ['-p', 'csv:=' + arg('csv')]
    out.append(TimerAction(period=30.0, actions=[ExecuteProcess(cmd=score, output='screen')]))   # after the gyro calibration
    return out


def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument(k, default_value=v) for k, v in DEFAULTS.items()]
                             + [OpaqueFunction(function=bricks)])
