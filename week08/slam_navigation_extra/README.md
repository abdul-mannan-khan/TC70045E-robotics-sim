# Week 09 SLAM and Autonomous Navigation

Everything this week runs in the module's ROS 2 Humble container on your laptop, with the simulated lab robot
(`tc70045e_sim`: four-wheel mecanum, 2D LiDAR on `/scan`, wheel odometry on `/odom_raw`, truth on `/ground_truth/odom`).

```bash
cd ../docker && docker compose up -d ros2     # then open http://localhost:6080 in your browser
```

Inside the container this folder is `~/labs/week09`. Save your own maps in `~/ws/maps` and bags in `~/bags`.

| What | Where | Notes |
|---|---|---|
| Commands from the lecture, in order | [`commands.md`](commands.md) | |
| `drive_loop.py` | [`scripts/drive_loop.py`](scripts/drive_loop.py) | drives a fixed 24 m circuit on the truth and scores SLAM (TF `map -> base_footprint`) and wheel odometry against it; `-p drive:=false` to score while you teleoperate; `-p csv:=file` |
| `map_metrics.py` | [`scripts/map_metrics.py`](scripts/map_metrics.py) | room size / scale error / rotation / wall thickness / unknown area of a saved map (plain Python, no ROS) |
| `nav_repeat.py` | [`scripts/nav_repeat.py`](scripts/nav_repeat.py) | N runs start -> goal with `nav2_simple_commander`; final pose error from the truth, AMCL error, time, recoveries; mean, s, RMS |

Frames: every SLAM map starts where the robot started, so **map = world - spawn pose**, spawn = (-3.0, -0.4, 0).

## Activity 1 - slam_toolbox (terminal per line)

```bash
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$(ros2 pkg prefix tc70045e_sim)/share/tc70045e_sim/config/slam_toolbox.yaml use_sim_time:=true
python3 ~/labs/week09/scripts/drive_loop.py --ros-args -p use_sim_time:=true -p csv:=$HOME/ws/w9_slamtb.csv
mkdir -p ~/ws/maps && ros2 run nav2_map_server map_saver_cli -f ~/ws/maps/lab_slamtb --ros-args -p use_sim_time:=true
python3 ~/labs/week09/scripts/map_metrics.py ~/ws/maps/lab_slamtb.yaml
```

Expected (measured 21 Sep 2026, simulated):

```
[drive_loop]: loop finished: 24.4 m in 133 s
error at the end [m]   SLAM 0.005   odometry 1.182
RMS error        [m]   SLAM 0.014   odometry 0.660
room width  10.00 m (true 10.00 m)  scale error +0.0 %  (+-0.5 %)
room depth   8.05 m (true 8.00 m)  scale error +0.6 %  (+-0.6 %)
```

## Activity 2 - Cartographer (restart the simulator first)

```bash
CFG=$(ros2 pkg prefix tc70045e_sim)/share/tc70045e_sim/config
ros2 run cartographer_ros cartographer_node -configuration_directory $CFG \
  -configuration_basename cartographer_2d.lua --ros-args -p use_sim_time:=true
ros2 run cartographer_ros cartographer_occupancy_grid_node -resolution 0.05 -publish_period_sec 1.0 \
  --ros-args -p use_sim_time:=true
```

Then the same `drive_loop.py` (`-p csv:=$HOME/ws/w9_carto.csv`), `map_saver_cli -f ~/ws/maps/lab_carto`, `map_metrics.py`.
Expected: SLAM end error 0.01-0.02 m, RMS about 0.04 m; room 10.10 x 8.05 m. CPU: Cartographer median ~15 %,
slam_toolbox ~6 % of one core.

## Activity 3 - AMCL + Nav2 (restart the simulator first)

```bash
ros2 launch nav2_bringup bringup_launch.py map:=$HOME/ws/maps/lab_slamtb.yaml \
  params_file:=$(ros2 pkg prefix tc70045e_sim)/share/tc70045e_sim/config/nav2_params.yaml use_sim_time:=true
python3 ~/labs/week09/scripts/nav_repeat.py --ros-args -p use_sim_time:=true
ros2 param set /controller_server general_goal_checker.xy_goal_tolerance 0.05
ros2 param set /controller_server general_goal_checker.yaw_goal_tolerance 0.1
python3 ~/labs/week09/scripts/nav_repeat.py --ros-args -p use_sim_time:=true -p set_initial_pose:=false
```

Default goal: map (3.0, 1.0) = world (0.0, 0.6). Measured (simulated): default tolerance mean 251 mm, s 10 mm (the error *is*
the 0.25 m tolerance); goal checker tightened alone -> robot never converges (DWB's own `FollowPath.xy_goal_tolerance`
is still 0.25 m) - intended failure; all tolerances 0.05 m / 0.1 rad in a copy of the params file -> mean 82 mm, s 7 mm:

```bash
cp $(ros2 pkg prefix tc70045e_sim)/share/tc70045e_sim/config/nav2_params.yaml ~/ws/nav2_tight.yaml
sed -i "s/xy_goal_tolerance: 0.25/xy_goal_tolerance: 0.05/g; s/yaw_goal_tolerance: 0.25/yaw_goal_tolerance: 0.1/" ~/ws/nav2_tight.yaml
```

Then relaunch `bringup_launch.py` with `params_file:=$HOME/ws/nav2_tight.yaml` and run `nav_repeat.py` again.

The simulated robot has **no command timeout**: if a script is killed hard, stop the robot with
`ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"`.

Note: the module's `nav2_params.yaml` still has `velocity_smoother.max_accel: [2.5, 0.0, 3.2]`, which zeroes every
sideways command (the controller asks for vy on `/cmd_vel_nav`, the robot receives 0 on `/cmd_vel`). This is kept as a
teaching point - see the lecture, Section 5.2, and the optional extension.
