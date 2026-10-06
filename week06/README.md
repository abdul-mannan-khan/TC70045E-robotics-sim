# Week 06 - Odometry, IMU Fusion and EKF

Everything here runs in the module's ROS 2 Humble container against the simulated lab robot, and is scored
against the simulator's ground truth (`/ground_truth/odom`). This folder is mounted at `~/labs/week06`.

```bash
cd docker && docker compose up -d ros2          # then open http://localhost:6080
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false     # Laboratories A and B
ros2 service call /reset_world std_srvs/srv/Empty                   # robot back to its spawn pose between runs
```

## What is in the folder

| Path | What it is | Laboratory |
|---|---|---|
| `scripts/drive_square.py` | scripted manoeuvres in simulated time: `square`, `straight`, `lateral`, `spin`, `arc`; always ends with a zero Twist | A, B, C |
| `scripts/evaluate_drift.py` | scores Odometry (position + heading) and Imu (heading) topics in a bag against ground truth; distance and rotation ratios for calibration; `--plot` writes `xy.png` and `heading.png` | A, B, C |
| `scripts/calibrated_odometry.py` | optional: odometry from `/wheel_speeds` plus the curvature term `yaw_per_metre` the firmware lacks, Euler or midpoint; publishes `/odom_cal` (remap it), no TF | A (extension) |
| `scripts/madgwick_sweep.launch.py` | four `imu_filter_madgwick` nodes (beta 0.01, 0.05, 0.1, 0.3) on the same IMU; `/imu/data_b0p01` ... `/imu/data_b0p3`; `use_mag:=true` and `mag_bias_x/y/z:=` [T] | B |
| `params/ekf_cal.yaml` | the simulator's `config/ekf.yaml` with `odom0: /odom_cal` | C |
| `params/ekf_double_count.yaml` | deliberately wrong: also fuses the integrated pose of `/odom_raw` | C |

## How to run it

```bash
# Laboratory A - calibration (one manoeuvre per bag; Ctrl+C the recorder after the script prints "done")
ros2 bag record -s mcap --use-sim-time -o ~/bags/w6_fwd /odom_raw /ground_truth/odom /wheel_speeds /imu/data_raw /tf /tf_static
python3 ~/labs/week06/scripts/drive_square.py straight --distance 2.0
python3 ~/labs/week06/scripts/evaluate_drift.py ~/bags/w6_fwd --est /odom_raw          # dist.rat ~1.010, dpsi -0.7 to -1.5 deg
#   ... same for ~/bags/w6_spin with: drive_square.py spin --turns 2 --dir ccw         # rot.rat ~0.971
# r_cal = 0.0375 * k_d, L_cal = 0.18 * k_d / k_theta; run the firmware node a second time with them (use YOUR numbers):
ros2 run tc70045e_sim wheel_odometry --ros-args -r __node:=wheel_odometry_cal \
    -r odom_raw:=odom_cal -r vel_raw:=vel_cal -r wheel_speeds:=wheel_speeds_cal \
    -p use_sim_time:=true -p publish_tf:=false -p wheel_radius:=0.03787 -p lx_plus_ly:=0.18686
python3 ~/labs/week06/scripts/drive_square.py square --dir cw                           # and: square --dir ccw --pre-turn -90
python3 ~/labs/week06/scripts/evaluate_drift.py ~/bags/w6_sq_cw --est /odom_raw /odom_cal --plot   # e/L 4.6 % -> 0.9 % (cw), 2.5 % -> 0.4 % (ccw)
# optional: curvature correction the firmware lacks
python3 ~/labs/week06/scripts/calibrated_odometry.py --ros-args -p use_sim_time:=true \
    -p wheel_radius:=0.03789 -p lx_plus_ly:=0.18727 -p yaw_per_metre:=-0.0130 -r odom_cal:=odom_c3 -r __node:=odom_c3

# Laboratory B - Madgwick beta sweep
ros2 launch ~/labs/week06/scripts/madgwick_sweep.launch.py                 # then use_mag:=true, then + mag_bias_*
#   (Ctrl+C the previous sweep first: `ros2 node list` must show exactly four /madgwick_b... nodes)
python3 ~/labs/week06/scripts/evaluate_drift.py ~/bags/w6_beta_nomag --est /imu/data_b0p01 /imu/data_b0p05 /imu/data_b0p1 /imu/data_b0p3
#   add --absolute for the magnetometer runs

# Laboratory C - EKF (restart the simulator with odom_tf:=false first)
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false odom_tf:=false
ros2 run imu_filter_madgwick imu_filter_madgwick_node --ros-args -p use_mag:=false -p publish_tf:=false -p world_frame:=enu -p use_sim_time:=true
ros2 run robot_localization ekf_node --ros-args --params-file $(ros2 pkg prefix tc70045e_sim)/share/tc70045e_sim/config/ekf.yaml -r odometry/filtered:=/odom
ros2 bag record -s mcap --use-sim-time -o ~/bags/w6_ekf_1 /odom /odom_raw /imu/data /ground_truth/odom /tf /tf_static
python3 ~/labs/week06/scripts/drive_square.py square --dir cw
python3 ~/labs/week06/scripts/evaluate_drift.py ~/bags/w6_ekf_1 --est /odom_raw /odom --plot   # raw ~4.5 %, fused 0.3-1.9 %
```

Typical results measured in the container on 21 Sept 2026 are in the tutor notes of the lecture.

Notes
- `wheel_radius` / `lx_plus_ly` on `wheel_odometry` are the nominal (firmware) geometry: setting them to your measured
  values calibrates the odometry. `true_*`, `radius_error_pct` and `track_error_pct` describe the simulated robot -
  look at them only after you have finished.
- A ROS name cannot contain '.', hence `/imu/data_b0p1` for beta = 0.1.
- All results are simulated - label them so in the report.
