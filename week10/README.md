# Week 10 Visual and RGB-D SLAM with the D455

Everything this week runs in the module's ROS 2 Humble container with the simulated lab robot and its
D455-style RGB-D camera (same topic names as `realsense2_camera`: `/camera/color/image_raw`,
`/camera/aligned_depth_to_color/image_raw`, `/camera/color/camera_info`).

```bash
cd ../docker && docker compose up -d ros2     # then open http://localhost:6080 in your browser
```

**Always start the simulator with `camera_width:=424 camera_height:=240`** on a laptop without a GPU:
848 x 480 renders at about 2.5 Hz (depth < 1 Hz); 424 x 240 gives 7-17 Hz depending on load (fx = 223.4 px).
Halving the resolution halves f and therefore doubles the simulated depth noise - say so in your report.

| What | Where | Notes |
|---|---|---|
| Commands from the lecture, in order | [`commands.md`](commands.md) | |
| `orb_features.py` | [`scripts/orb_features.py`](scripts/orb_features.py) | ORB keypoints, ratio-test matches, RANSAC inliers, Hamming distance, timings; summary at Ctrl+C |
| `cloud_filter.py` | [`scripts/cloud_filter.py`](scripts/cloud_filter.py) | pass-through + voxel grid in NumPy (Humble `pcl_ros` has no filter nodes) |
| `rtabmap_stats.py` | [`scripts/rtabmap_stats.py`](scripts/rtabmap_stats.py) | counts RTAB-Map loop and proximity closures from `/rtabmap/info`; summary at Ctrl+C |
| `drive_loop.py` | [`../week09/scripts/drive_loop.py`](../week09/scripts/drive_loop.py) | last week's circuit driver + ground-truth scorer; use `-p speed:=0.15 -p turn_rate:=0.3` |

## Activity 1 - ORB features

```bash
ros2 launch tc70045e_sim sim.launch.py gui:=false camera_width:=424 camera_height:=240
python3 ~/labs/week10/scripts/orb_features.py --ros-args -p use_sim_time:=true -p save:=$HOME/ws/orb_lab.png
ros2 launch tc70045e_sim sim.launch.py gui:=false world:=range x:=5.81 y:=0 camera_width:=424 camera_height:=240
```

Measured (simulated): lab scene 239 keypoints/frame, ORB 2.8 ms + matching 1.7 ms; turning at 0.3 rad/s 156 good matches,
median Hamming 9; plain wall at 1 m: **0 keypoints**.

## Activity 2 - point cloud and Octomap

```bash
ros2 run depth_image_proc point_cloud_xyzrgb_node --ros-args -p use_sim_time:=true \
  -r rgb/image_rect_color:=/camera/color/image_raw -r rgb/camera_info:=/camera/color/camera_info \
  -r depth_registered/image_rect:=/camera/aligned_depth_to_color/image_raw -r points:=/camera/depth/color/points
python3 ~/labs/week10/scripts/cloud_filter.py --ros-args -p use_sim_time:=true \
  -r input:=/camera/depth/color/points -r output:=/cloud_voxel -p z_min:=0.3 -p z_max:=4.0 -p leaf:=0.05
ros2 run octomap_server octomap_server_node --ros-args -p use_sim_time:=true \
  -p frame_id:=odom -p resolution:=0.05 -p sensor_model.max_range:=4.0 -r cloud_in:=/cloud_voxel
ros2 run octomap_server octomap_saver_node --ros-args -p octomap_path:=$HOME/ws/maps/lab_octo.bt
```

Measured: raw cloud 101 760 points x 32 B = 3.26 MB/msg, 12 MB/s; pass-through 0.53 MB; voxel 0.05 m 102 kB (8.3 % of points);
octree of the west room after one turn 30 kB. If the saver prints `Problem while waiting for response`, run it again.

## Activity 3 - RTAB-Map on the Week 9 circuit

```bash
ros2 launch tc70045e_sim sim.launch.py gui:=false odom_tf:=false camera_width:=424 camera_height:=240
ros2 launch rtabmap_launch rtabmap.launch.py rgb_topic:=/camera/color/image_raw \
  depth_topic:=/camera/aligned_depth_to_color/image_raw camera_info_topic:=/camera/color/camera_info \
  frame_id:=base_footprint use_sim_time:=true approx_sync:=true rtabmap_viz:=false rviz:=false \
  args:="-d --Reg/Force3DoF true"
python3 ~/labs/week10/scripts/rtabmap_stats.py --ros-args -p use_sim_time:=true
python3 ~/labs/week09/scripts/drive_loop.py --ros-args -p use_sim_time:=true \
  -p speed:=0.15 -p turn_rate:=0.3 -p csv:=$HOME/ws/w10_rtab_vo.csv
```

Wheel-odometry variant: simulator without `odom_tf:=false`, add `visual_odometry:=false odom_topic:=/odom_raw`.
LiDAR fusion: also add `subscribe_scan:=true scan_topic:=/scan`.

Measured (simulated, 424 x 240, ~7 Hz): end-of-loop error 5-28 mm after 4-5 loop + 3 proximity closures, but RMS error during
the circuit 0.62-1.09 m (LiDAR SLAM: 0.014-0.041 m). Visual odometry 54-67 % of one core, mapping 11-15 %, 290-410 MB.
Without `Reg/Force3DoF` and with wheel odometry every loop closure is rejected ("Graph optimization failed").
