"""madgwick_sweep.launch.py - four Madgwick filters with different gains on the SAME IMU stream (TC70045E Week 6).

Each filter reads /imu/data_raw (and /imu/mag when use_mag:=true) and publishes /imu/data_b<gain> with the
decimal point written as p (a '.' is not allowed in a ROS name): /imu/data_b0p01, _b0p05, _b0p1, _b0p3.
Because all four see identical samples, any difference between them is caused by beta alone - a paired
comparison. No TF is published.

  ros2 launch ~/labs/week06/scripts/madgwick_sweep.launch.py                      # gyro + accelerometer
  ros2 launch ~/labs/week06/scripts/madgwick_sweep.launch.py use_mag:=true        # + raw magnetometer
  ros2 launch ~/labs/week06/scripts/madgwick_sweep.launch.py use_mag:=true mag_bias_x:=6.0e-6 \
      mag_bias_y:=-4.0e-6 mag_bias_z:=3.0e-6                                       # + hard-iron correction [T]
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

GAINS = ['0.01', '0.05', '0.1', '0.3']


def generate_launch_description():
    args = [DeclareLaunchArgument('use_mag', default_value='false')] + \
        [DeclareLaunchArgument('mag_bias_' + ax, default_value='0.0') for ax in 'xyz']
    nodes = [Node(package='imu_filter_madgwick', executable='imu_filter_madgwick_node',
                  name='madgwick_b' + g.replace('.', 'p'),
                  parameters=[{'use_sim_time': True, 'gain': float(g), 'world_frame': 'enu',
                               'publish_tf': False, 'use_mag': LaunchConfiguration('use_mag'),
                               'mag_bias_x': LaunchConfiguration('mag_bias_x'),
                               'mag_bias_y': LaunchConfiguration('mag_bias_y'),
                               'mag_bias_z': LaunchConfiguration('mag_bias_z')}],
                  remappings=[('imu/data', '/imu/data_b' + g.replace('.', 'p'))])
             for g in GAINS]
    return LaunchDescription(args + nodes)
