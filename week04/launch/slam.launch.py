"""Week 4 - add a sensor, upgrade the SLAM: LiDAR + D455 camera, slam_toolbox -> RTAB-Map.

One launch file, the same bricks as Week 2 plus the camera brick and a second SLAM brick:
  robot    tc70045e_sim/sim.launch.py      the lab robot in Gazebo (gui:=true shows the Gazebo window)
  camera   the robot's D455-style camera   /camera/color/image_raw, /camera/aligned_depth_to_color/image_raw (424x240)
  slam     slam:=toolbox                   Week 2: slam_toolbox, LiDAR only
           slam:=rtabmap                   RTAB-Map with the settings in week04/config/rtabmap.yaml (your activity);
                                           rgbd_sync pairs each colour image with its depth image -> /rgbd_image
  rviz     rviz2 with week04/rviz/slam.rviz   map, laser, camera image, depth cloud, robot
  drive    week04/scripts/drive_loop.py    drives the same 24 m circuit every time and scores the SLAM pose

Usage (in the container):
  ros2 launch ~/labs/week04/launch/slam.launch.py slam:=toolbox                 # Week 2 again: LiDAR only
  ros2 launch ~/labs/week04/launch/slam.launch.py slam:=rtabmap                 # RTAB-Map, rtabmap.yaml
  ros2 launch ~/labs/week04/launch/slam.launch.py slam:=rtabmap drive:=true     # ... and drive the circuit
  ros2 launch ~/labs/week04/launch/slam.launch.py slam:=rtabmap config:=$HOME/labs/solutions/week04/rtabmap.yaml

Both SLAM bricks publish the map on /map and the TF map -> odom, so RViz, map_saver and the scripts work with either.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

WEEK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULTS = {'gui': 'true', 'rviz': 'true', 'camera': 'true', 'slam': 'rtabmap', 'drive': 'false',
            'config': os.path.join(WEEK, 'config', 'rtabmap.yaml')}


def bricks(context):
    arg = lambda name: LaunchConfiguration(name).perform(context)
    sim_share = get_package_share_directory('tc70045e_sim')
    out = [IncludeLaunchDescription(                                  # robot + camera bricks
        PythonLaunchDescriptionSource(os.path.join(sim_share, 'launch', 'sim.launch.py')),
        launch_arguments={'gui': arg('gui'), 'camera': arg('camera'),
                          'camera_width': '424', 'camera_height': '240'}.items())]
    if arg('rviz') == 'true':
        out.append(Node(package='rviz2', executable='rviz2', output='log',
                        arguments=['-d', os.path.join(WEEK, 'rviz', 'slam.rviz')],
                        parameters=[{'use_sim_time': True}]))
    if arg('slam') == 'toolbox':                                      # slam brick, Week 2 version
        out.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('slam_toolbox'), 'launch',
                                                       'online_async_launch.py')),
            launch_arguments={'use_sim_time': 'true',
                              'slam_params_file': os.path.join(sim_share, 'config', 'slam_toolbox.yaml')}.items()))
    elif arg('slam') == 'rtabmap':                                    # slam brick, Week 4 version
        if arg('camera') == 'true':                                   # pair colour + depth + camera_info first
            out.append(Node(package='rtabmap_sync', executable='rgbd_sync', name='rgbd_sync', output='log',
                            parameters=[{'use_sim_time': True, 'approx_sync': False}],   # one sensor, same stamps
                            remappings=[('rgb/image', '/camera/color/image_raw'),
                                        ('rgb/camera_info', '/camera/color/camera_info'),
                                        ('depth/image', '/camera/aligned_depth_to_color/image_raw'),
                                        ('rgbd_image', '/rgbd_image')]))
        out.append(Node(
            package='rtabmap_slam', executable='rtabmap', name='rtabmap', namespace='rtabmap', output='log',
            arguments=['--delete_db_on_start'],                       # a new map every launch
            parameters=[arg('config'), {'use_sim_time': True}],
            remappings=[('odom', '/odom_raw'), ('scan', '/scan'),     # wheel odometry and LiDAR
                        ('rgbd_image', '/rgbd_image'),                # the D455, paired by rgbd_sync
                        ('map', '/map')]))                            # same map topic as slam_toolbox
    if arg('drive') == 'true':
        out.append(TimerAction(period=20.0, actions=[ExecuteProcess(   # let Gazebo and the SLAM brick start first
            cmd=['python3', os.path.join(WEEK, 'scripts', 'drive_loop.py'), '--ros-args', '-p', 'use_sim_time:=true',
                 '-p', 'speed:=0.15', '-p', 'turn_rate:=0.3'], output='screen')]))
    return out


def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument(k, default_value=v) for k, v in DEFAULTS.items()]
                             + [OpaqueFunction(function=bricks)])
