# Week 09 – commands and code from the lecture, in order

Generated from the lecture (Week 09: LiDAR SLAM and Autonomous Navigation – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## What the container ships instead: slam_toolbox

```bash
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false
```

```bash
ros2 topic hz /scan          # 5.5 Hz nominal; 4-5.5 Hz on a busy laptop
ros2 topic hz /clock         # ~200 Hz: simulated time is running
```

```bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$(ros2 pkg prefix tc70045e_sim)/share/tc70045e_sim/config/slam_toolbox.yaml \
  use_sim_time:=true
```

```bash
python3 ~/labs/week09/scripts/drive_loop.py --ros-args \
  -p use_sim_time:=true -p csv:=$HOME/ws/w9_slamtb.csv
```

```bash
top -b -d 2 -n 30 -c -w 512 | grep [a]sync_slam_toolbox
```

```bash
mkdir -p ~/ws/maps
ros2 run nav2_map_server map_saver_cli -f ~/ws/maps/lab_slamtb \
  --ros-args -p use_sim_time:=true
cat ~/ws/maps/lab_slamtb.yaml
```

```bash
python3 ~/labs/week09/scripts/map_metrics.py ~/ws/maps/lab_slamtb.yaml
```

```text
[drive_loop]: loop finished: 24.4 m in 132 s
samples: 264 at 2 Hz (no map -> base_footprint TF in 0 of them)
error at the end [m]   SLAM 0.006   odometry 1.294
RMS error        [m]   SLAM 0.021   odometry 0.741
max error        [m]   SLAM 0.049   odometry 1.529

image: lab_slamtb.pgm
mode: trinary
resolution: 0.05
origin: [-2.03, -3.65, 0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.25

resolution 0.050 m, 201 x 162 cells, occupied 1443, free 27783, unknown 3336
map rotation relative to the walls: +0.0 deg
room width  10.00 m (true 10.00 m)  scale error +0.0 %  (+-0.5 %)
room depth   8.05 m (true 8.00 m)  scale error +0.6 %  (+-0.6 %)
north wall thickness: median 1 cells = 0.05 m
known (free + occupied) area: 73.1 m^2 of 80.0 m^2 room
```

## 3.4 Trade-offs

```bash
ros2 node list          # expect an empty list (or only rviz2)
```

```text
CFG=$(ros2 pkg prefix tc70045e_sim)/share/tc70045e_sim/config
ros2 run cartographer_ros cartographer_node \
  -configuration_directory $CFG -configuration_basename cartographer_2d.lua \
  --ros-args -p use_sim_time:=true
```

```bash
ros2 run cartographer_ros cartographer_occupancy_grid_node \
  -resolution 0.05 -publish_period_sec 1.0 --ros-args -p use_sim_time:=true
```

```bash
python3 ~/labs/week09/scripts/drive_loop.py --ros-args \
  -p use_sim_time:=true -p csv:=$HOME/ws/w9_carto.csv
top -b -d 2 -n 30 -c -w 512 | grep [c]artographer_node
```

```bash
ros2 run tf2_tools view_frames      # prints the tree as YAML, writes frames_<date>.pdf here
rqt_graph
```

```bash
ros2 run nav2_map_server map_saver_cli -f ~/ws/maps/lab_carto \
  --ros-args -p use_sim_time:=true
python3 ~/labs/week09/scripts/map_metrics.py ~/ws/maps/lab_carto.yaml
```

```text
[drive_loop]: loop finished: 24.4 m in 132 s
error at the end [m]   SLAM 0.007   odometry 1.458
RMS error        [m]   SLAM 0.036   odometry 0.832
max error        [m]   SLAM 0.079   odometry 1.696

resolution 0.050 m, 215 x 174 cells, occupied 1729, free 27731, unknown 7950
map rotation relative to the walls: +0.0 deg
room width  10.10 m (true 10.00 m)  scale error +1.0 %  (+-0.5 %)
room depth   8.05 m (true 8.00 m)  scale error +0.6 %  (+-0.6 %)
north wall thickness: median 1 cells = 0.05 m
```

## 5.2 Planners and controllers

```bash
ros2 launch nav2_bringup bringup_launch.py \
  map:=$HOME/ws/maps/lab_slamtb.yaml \
  params_file:=$(ros2 pkg prefix tc70045e_sim)/share/tc70045e_sim/config/nav2_params.yaml \
  use_sim_time:=true
```

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: map}, pose: {position: {x: 3.0, y: 1.0}, orientation: {w: 1.0}}}}"
```

```bash
ros2 topic echo /ground_truth/odom --once --field pose.pose.position   # world frame
ros2 topic echo /amcl_pose --once --field pose.pose.position          # map frame
```

```bash
python3 ~/labs/week09/scripts/nav_repeat.py --ros-args -p use_sim_time:=true
```

```bash
ros2 param get /controller_server general_goal_checker.xy_goal_tolerance
ros2 param set /controller_server general_goal_checker.xy_goal_tolerance 0.05
ros2 param set /controller_server general_goal_checker.yaw_goal_tolerance 0.1
python3 ~/labs/week09/scripts/nav_repeat.py --ros-args \
  -p use_sim_time:=true -p set_initial_pose:=false
```

```bash
cp $(ros2 pkg prefix tc70045e_sim)/share/tc70045e_sim/config/nav2_params.yaml ~/ws/nav2_tight.yaml
sed -i "s/xy_goal_tolerance: 0.25/xy_goal_tolerance: 0.05/g; s/yaw_goal_tolerance: 0.25/yaw_goal_tolerance: 0.1/" \
  ~/ws/nav2_tight.yaml
grep -n goal_tolerance ~/ws/nav2_tight.yaml
ros2 launch nav2_bringup bringup_launch.py map:=$HOME/ws/maps/lab_slamtb.yaml \
  params_file:=$HOME/ws/nav2_tight.yaml use_sim_time:=true
python3 ~/labs/week09/scripts/nav_repeat.py --ros-args -p use_sim_time:=true
```

```bash
ros2 bag record -s mcap -o ~/bags/w9_nav_run /amcl_pose /plan /cmd_vel /scan \
  /tf /tf_static /ground_truth/odom
```

```text
# default tolerances: xy 0.25 m, yaw 0.25 rad (14.3 deg)
run  dx[mm]  dy[mm]  dth[deg]  amcl_err[mm]  t[s]  recov  result
  1    -215     -94     +15.8            19    12      0  SUCCEEDED
  2    -253     -50     +15.9           228    11      0  SUCCEEDED
  3    -223    -115     +14.1            11    12      0  SUCCEEDED
  4    -239    -103     +14.3            40    12      0  SUCCEEDED
  5    -240     -76     +14.6            34    12      0  SUCCEEDED
radial error: mean 251 mm, s 10 mm, RMS 251 mm (n = 5);  mean |dth| 15.0 deg, max 15.9 deg
mean AMCL error 66 mm;  mean run time 12 s;  recoveries 0

# step 6: goal checker 0.05 m / 0.1 rad set live, DWB still at 0.25 m
  1    +163     -53      +1.7            99    56     22  FAILED
  2    -295     -76      +1.1            72    90      7  CANCELED
  ... runs 3-5 the same: CANCELED after 90 s, 7-8 recoveries each
radial error: mean 259 mm, s 52 mm, RMS 263 mm (n = 5);  mean |dth| 1.4 deg
mean AMCL error 66 mm;  mean run time 83 s;  recoveries 52

# step 7: every tolerance 0.05 m / 0.1 rad in ~/ws/nav2_tight.yaml
  1     -76     +35      +6.5            72    15      0  SUCCEEDED
  2     -91     +10      -2.4            60    15      0  SUCCEEDED
  3     -82     +12      -1.8            26    15      0  SUCCEEDED
  4     -66     -26      +5.9             8    14      0  SUCCEEDED
  5     -83      +2      +3.9            56    17      0  SUCCEEDED
radial error: mean 82 mm, s 7 mm, RMS 83 mm (n = 5);  mean |dth| 4.1 deg, max 6.5 deg
mean AMCL error 44 mm;  mean run time 15 s;  recoveries 0

radial error   e_i = sqrt(dx_i^2 + dy_i^2)
mean           e_bar = (1/n) * sum(e_i)                   -> accuracy  (bias)
std. deviation s     = sqrt( sum((e_i - e_bar)^2) / (n-1) ) -> repeatability
RMS            e_rms = sqrt( (1/n) * sum(e_i^2) )
```

## 📐 Evaluate it — the numbers you must record this week

```text
I am configuring ROS 2 Humble Nav2 for a holonomic mecanum robot.
Measured facts (do not assume others):
  footprint 0.34 m x 0.26 m, inscribed radius 0.13 m
  max speeds vx 0.30, vy 0.25 m/s, wz 1.0 rad/s
  2D LiDAR: 720 points/rev, 5.5 Hz, range 0.15-12 m
  narrowest doorway on the route: 0.80 m
  local costmap 3 m x 3 m at 0.05 m resolution
For the inflation layer, give inflation_radius and cost_scaling_factor.
Show the cost(d) curve at d = 0.13, 0.20, 0.30, 0.40 m using
cost = 253 * exp(-k * (d - r_inscribed)), and state explicitly whether
the 0.80 m doorway remains traversable with your values. If it does not,
say so and revise. Cite the Nav2 parameter names exactly as in Humble.
```
