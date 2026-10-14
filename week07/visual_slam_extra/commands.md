# Week 10 – commands and code from the lecture, in order

Generated from the lecture (Week 10: Visual and RGB-D SLAM with the D455 – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 2.2 ORB-SLAM2

```bash
ros2 launch tc70045e_sim sim.launch.py gui:=false camera_width:=424 camera_height:=240
```

```bash
ros2 topic list | grep camera
ros2 topic hz /camera/color/image_raw
ros2 topic hz /camera/aligned_depth_to_color/image_raw
ros2 topic echo /camera/color/camera_info --once --field k
ros2 topic info -v /camera/color/image_raw | grep -A2 QoS
```

```bash
python3 ~/labs/week10/scripts/orb_features.py --ros-args \
  -p use_sim_time:=true -p save:=$HOME/ws/orb_lab.png
```

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{angular: {z: 0.3}}"
# Ctrl+C after ~10 s, then:
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"
```

```bash
ros2 launch tc70045e_sim sim.launch.py gui:=false world:=range x:=5.81 y:=0 \
  camera_width:=424 camera_height:=240
```

```text
# ros2 topic hz  (laptop shared with other simulations; ~17 / 11 Hz when it is not)
/camera/color/image_raw                   average rate: 6.988
/camera/aligned_depth_to_color/image_raw  average rate: 7.545
# camera_info k and width
[223.4095407  0.  212.5  0.  223.4095407  120.5  0.  0.  1.]    width 424
# QoS: Reliability: RELIABLE

# lab world, robot still on its start mark
summary over 170 frames: keypoints mean 239 min 239 | good matches mean 239 |
  inliers 100.0 % | median Hamming 0 | ORB 2.8 ms, matching 1.7 ms per frame

# turning on the spot at 0.3 rad/s
kp  229  ratio-test matches  148  RANSAC inliers  140  median Hamming    7
summary over 112 frames: keypoints mean 203 min 138 | good matches mean 156 |
  inliers 94.7 % | median Hamming 9 | ORB 2.4 ms, matching 1.5 ms per frame

# range world, 1.0 m from the plain grey wall (x:=5.81)
summary over 187 frames: keypoints mean 0 min 0 | good matches mean 0 |
  inliers 0.0 % | median Hamming n/a | ORB 1.1 ms, matching 0.0 ms per frame
# range world, x:=0 (wall 6.8 m away; floor markers and targets in view)
summary over 246 frames: keypoints mean 59 min 59 | good matches mean 57 |
  inliers 100.0 % | median Hamming 0 | ORB 1.5 ms, matching 0.6 ms per frame
```

## 4.1 The bandwidth problem

```text
pts = pc2.read_points_numpy(msg, field_names=('x', 'y', 'z'), skip_nans=True)
keep = (pts[:, 2] > z_min) & (pts[:, 2] < z_max)          # pass-through
pts = pts[keep]
keys = np.floor(pts / leaf).astype(np.int64)          # voxel grid: one point per occupied voxel
_, first = np.unique(keys, axis=0, return_index=True)
pts = pts[np.sort(first)]
```

## 4.2 Octomap: occupancy in 3D

```bash
ros2 run depth_image_proc point_cloud_xyzrgb_node --ros-args -p use_sim_time:=true \
  -r rgb/image_rect_color:=/camera/color/image_raw \
  -r rgb/camera_info:=/camera/color/camera_info \
  -r depth_registered/image_rect:=/camera/aligned_depth_to_color/image_raw \
  -r points:=/camera/depth/color/points
```

```bash
ros2 topic echo /camera/depth/color/points --once --field point_step
ros2 topic hz /camera/depth/color/points
ros2 topic bw /camera/depth/color/points
```

```bash
python3 ~/labs/week10/scripts/cloud_filter.py --ros-args -p use_sim_time:=true \
  -r __node:=cloud_pt -r input:=/camera/depth/color/points -r output:=/cloud_pt \
  -p z_min:=0.3 -p z_max:=4.0 -p leaf:=0.001
```

```bash
python3 ~/labs/week10/scripts/cloud_filter.py --ros-args -p use_sim_time:=true \
  -r input:=/camera/depth/color/points -r output:=/cloud_voxel \
  -p z_min:=0.3 -p z_max:=4.0 -p leaf:=0.05
```

```bash
ros2 topic bw /cloud_pt
ros2 topic bw /cloud_voxel
ros2 topic hz /cloud_voxel
```

```bash
ros2 run octomap_server octomap_server_node --ros-args -p use_sim_time:=true \
  -p frame_id:=odom -p resolution:=0.05 -p sensor_model.max_range:=4.0 \
  -r cloud_in:=/cloud_voxel
```

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{angular: {z: 0.3}}"
# Ctrl+C after about 21 s (one turn), then stop the robot:
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"
```

```bash
ros2 run octomap_server octomap_saver_node --ros-args \
  -p octomap_path:=$HOME/ws/maps/lab_octo.bt
ls -l ~/ws/maps/lab_octo.bt
```

```text
# ros2 topic echo ... --field point_step / width      -> 32 / 424  (x 240 rows)
# ("A message was lost!!!" lines from echo on a big, slow topic are harmless)
Stage (424 x 240, lab world)     | points/frame | msg size | rate   | bandwidth
---------------------------------+--------------+----------+--------+-----------
raw /camera/depth/color/points   |   101 760    | 3.26 MB  | 3.9 Hz | 12.1 MB/s
after pass-through 0.3-4.0 m     |   ~44 000    | 0.53 MB  |        |  1.8 MB/s
after voxel grid 0.05 m          |    ~8 500    |  102 kB  | 5.5 Hz |  0.61 MB/s
[cloud_pt]: in 101760 -> out 44085 points (43.3% kept)
[cloud_filter]: in 101760 -> out 8456 points (8.3% kept)
# after one ~21 s turn on the spot at 0.3 rad/s
[octomap_saver]: Map received (114727 nodes, 0.050000 m res), saving to .../lab_octo.bt
Writing 83639 nodes to output stream... done.
-rw-r--r-- 1 root root 29589 ... /root/ws/maps/lab_octo.bt
# for comparison, over the same ~21 s: raw cloud ~12 MB/s x 21 s = ~250 MB,
# voxel-filtered cloud ~0.5 MB/s x 21 s = ~10 MB, octree file 30 kB
```

## 5.2 Fusing the LiDAR

```bash
ros2 launch tc70045e_sim sim.launch.py gui:=false odom_tf:=false \
  camera_width:=424 camera_height:=240
```

```bash
ros2 launch rtabmap_launch rtabmap.launch.py \
  rgb_topic:=/camera/color/image_raw \
  depth_topic:=/camera/aligned_depth_to_color/image_raw \
  camera_info_topic:=/camera/color/camera_info \
  frame_id:=base_footprint use_sim_time:=true approx_sync:=true \
  rtabmap_viz:=false rviz:=false args:="-d --Reg/Force3DoF true"
```

```bash
python3 ~/labs/week10/scripts/rtabmap_stats.py --ros-args -p use_sim_time:=true
```

```bash
python3 ~/labs/week09/scripts/drive_loop.py --ros-args -p use_sim_time:=true \
  -p speed:=0.15 -p turn_rate:=0.3 -p csv:=$HOME/ws/w10_rtab_vo.csv
```

```bash
top -b -d 3 -n 20 -c -w 512 | grep -E "[r]tabmap_slam/rtabmap|[r]gbd_odometry"
```

```bash
ls -lh ~/.ros/rtabmap.db
cp ~/.ros/rtabmap.db ~/ws/rtabmap_vo.db
rtabmap-databaseViewer ~/ws/rtabmap_vo.db     # optional: browse nodes, loop closures, 3D cloud
```

```text
# run 1: visual odometry, Force3DoF (424 x 240, camera ~7 Hz on a shared laptop)
[drive_loop]: loop finished: 24.4 m in 210 s
error at the end [m]   SLAM 0.028   odometry 1.393
RMS error        [m]   SLAM 1.089   odometry 0.797
max error        [m]   SLAM 1.694   odometry 1.636
node 141: LOOP CLOSURE with node 128
node 231: LOOP CLOSURE with node 1        ... (232, 233, 234 -> 1)
updates 204 | loop closures 5 | proximity closures 3 | time per update mean 39 ms,
  max 302 ms | WM 178 nodes
top: rgbd_odometry median 67 %, peak 87 %, RSS 207 MB; rtabmap median 15 %, peak 25 %, RSS 411 MB
-rw-r--r-- 1 root root 27M ... /root/.ros/rtabmap.db

# run 2: wheel odometry (/odom_raw), Force3DoF
error at the end [m]   SLAM 0.005   odometry 1.131
RMS error        [m]   SLAM 0.624   odometry 0.644
max error        [m]   SLAM 1.327   odometry 1.327
updates 188 | loop closures 4 | proximity closures 3 | time per update mean 27 ms, ...
top: rtabmap median 14 %, peak 20 %, RSS 368 MB

# run 3: wheel odometry + LiDAR (subscribe_scan), Force3DoF
error at the end [m]   SLAM 0.010   odometry 1.247
RMS error        [m]   SLAM 0.685   odometry 0.705
updates 192 | loop closures 4 | proximity closures 3 | ...   rtabmap median 13 %, peak 27 %, RSS 345 MB

# run 2 without Force3DoF (args:="-d"): every loop closure rejected
[ WARN] ... Very large angular variance (1000000.000000) detected! Please fix odometry covariance ...
[ WARN] ... Graph optimization failed! Rejecting last loop closures added.
[ WARN] ... Loop closure 230->1 rejected!
error at the end [m]   SLAM 1.090   odometry 1.090        (the map was never corrected)
```

```text
Quantity (simulated, same laptop)     | LiDAR SLAM (W9) | RGB-D SLAM (W10) | Wheel+RGB-D / fused
--------------------------------------+-----------------+------------------+-------------
end-of-loop error vs truth (m)        |                 |                  |
RMS / max trajectory error (m)        |                 |                  |
wheel-odometry error, same run (m)    |                 |                  |
loop + proximity closures (count)     |                 |                  |
median / peak CPU, % of one core      |                 |                  |
resident memory, MB                   |                 |                  |
map update rate, Hz                   |                 |                  |
driving speed, m/s and rad/s          |  0.25 / 0.4     |  0.15 / 0.3      |
tracking failures (count)             |                 |                  |
```

## 📐 Evaluate it — the numbers you must record this week

```text
ROS 2 Humble in Docker, simulated D455-style camera (Gazebo),
rtabmap_launch rtabmap.launch.py with use_sim_time:=true,
frame_id:=base_footprint, approx_sync:=true. rtabmap runs but
/rtabmap/map stays empty and rgbd_odometry warns every 5 s.

Evidence (real output, not invented):
  ros2 topic hz /camera/color/image_raw                  -> 7.1 Hz
  ros2 topic hz /camera/aligned_depth_to_color/image_raw -> 7.0 Hz
  ros2 topic info -v /camera/color/image_raw  -> publisher RELIABLE
  (paste the exact rgbd_odometry warning here)

Give me a RANKED list of at most 5 hypotheses. For each: the single
command that confirms or refutes it, and the expected output of that
command if the hypothesis is TRUE. Do not suggest fixes yet.
```
