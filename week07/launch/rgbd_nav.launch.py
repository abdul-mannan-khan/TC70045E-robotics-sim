"""Week 7 - D455 RGB-D SLAM and navigation: map with the camera only, then navigate on that map.

One launch file, two modes:
  mode:=mapping        robot + D455 + RTAB-Map (camera only, your rtabmap_camera.yaml) + RViz [+ drive the circuit]
                       the map is kept in a database: ~/maps/w7_camera.db (a new one every mapping run)
  mode:=localization   the same, but RTAB-Map loads the database and only LOCALISES (recognises places it has seen)
                       + nav:=true starts Nav2 on that map; its obstacle layers use the depth camera, not the LiDAR

Bricks:
  robot      tc70045e_sim/sim.launch.py       the lab robot in Gazebo with the D455 (424 x 240)
  rgbd_sync  rtabmap_sync                     pairs each colour image with its depth image -> /rgbd_image
  rtabmap    rtabmap_slam                     the camera-only SLAM brick; publishes /map and TF map -> odom
  cloud      depth_image_proc point_cloud_xyz the depth image as a point cloud (/camera/depth/points) for Nav2
  nav2       nav2_bringup navigation_launch   planner, controller, behaviours (no AMCL, no map_server)
  rviz       rviz2 with week07/rviz/rgbd_nav.rviz
  drive      week04/scripts/drive_loop.py     the Week 4 circuit, scored against the truth (mapping)

Usage (in the container):
  ros2 launch ~/labs/week07/launch/rgbd_nav.launch.py mode:=mapping drive:=true
  ros2 launch ~/labs/week07/launch/rgbd_nav.launch.py mode:=localization nav:=true
  ... config:=$HOME/labs/solutions/week07/rtabmap_camera.yaml     # the solution settings
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode

WEEK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABS = os.path.dirname(WEEK)
DEFAULTS = {'mode': 'mapping', 'nav': 'false', 'drive': 'false', 'gui': 'true', 'rviz': 'true',
            'config': os.path.join(WEEK, 'config', 'rtabmap_camera.yaml'),
            'database': os.path.join(os.path.expanduser('~'), 'maps', 'w7_camera.db')}


def bricks(context):
    arg = lambda name: LaunchConfiguration(name).perform(context)
    mapping = arg('mode') == 'mapping'
    os.makedirs(os.path.dirname(arg('database')), exist_ok=True)
    sim_share = get_package_share_directory('tc70045e_sim')
    out = [IncludeLaunchDescription(                                  # robot + camera bricks
        PythonLaunchDescriptionSource(os.path.join(sim_share, 'launch', 'sim.launch.py')),
        launch_arguments={'gui': arg('gui'), 'camera': 'true',
                          'camera_width': '424', 'camera_height': '240'}.items()),
        Node(package='rtabmap_sync', executable='rgbd_sync', name='rgbd_sync', output='log',
             parameters=[{'use_sim_time': True, 'approx_sync': False}],
             remappings=[('rgb/image', '/camera/color/image_raw'), ('rgb/camera_info', '/camera/color/camera_info'),
                         ('depth/image', '/camera/aligned_depth_to_color/image_raw'), ('rgbd_image', '/rgbd_image')])]
    loc = {} if mapping else {'Mem/IncrementalMemory': 'false', 'Mem/InitWMWithAllNodes': 'true'}
    out.append(Node(                                                  # the SLAM brick
        package='rtabmap_slam', executable='rtabmap', name='rtabmap', namespace='rtabmap', output='log',
        arguments=['--delete_db_on_start'] if mapping else [],
        parameters=[arg('config'), {'use_sim_time': True, 'database_path': arg('database')}, loc],
        remappings=[('odom', '/odom_raw'), ('scan', '/scan'), ('rgbd_image', '/rgbd_image'), ('map', '/map')]))
    if arg('rviz') == 'true':
        out.append(Node(package='rviz2', executable='rviz2', output='log',
                        arguments=['-d', os.path.join(WEEK, 'rviz', 'rgbd_nav.rviz')],
                        parameters=[{'use_sim_time': True}]))
    if arg('nav') == 'true':
        out.append(ComposableNodeContainer(                           # depth image -> point cloud for Nav2
            name='depth_cloud', namespace='', package='rclcpp_components', executable='component_container',
            composable_node_descriptions=[ComposableNode(
                package='depth_image_proc', plugin='depth_image_proc::PointCloudXyzNode', name='point_cloud_xyz',
                parameters=[{'use_sim_time': True}],
                remappings=[('image_rect', '/camera/aligned_depth_to_color/image_raw'),
                            ('camera_info', '/camera/color/camera_info'), ('points', '/camera/depth/points')])],
            output='log'))
        out.append(TimerAction(period=15.0, actions=[IncludeLaunchDescription(   # after RTAB-Map has a map
            PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('nav2_bringup'), 'launch',
                                                       'navigation_launch.py')),
            launch_arguments={'use_sim_time': 'true', 'autostart': 'true',
                              'params_file': os.path.join(WEEK, 'config', 'nav2_params.yaml')}.items())]))
    if arg('drive') == 'true':
        out.append(TimerAction(period=25.0, actions=[ExecuteProcess(
            cmd=['python3', os.path.join(LABS, 'week04', 'scripts', 'drive_loop.py'), '--ros-args',
                 '-p', 'use_sim_time:=true', '-p', 'speed:=0.15', '-p', 'turn_rate:=0.3'], output='screen')]))
    return out


def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument(k, default_value=v) for k, v in DEFAULTS.items()]
                             + [OpaqueFunction(function=bricks)])
