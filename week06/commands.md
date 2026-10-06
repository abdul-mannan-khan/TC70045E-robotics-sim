# Week 06 – commands and code from the lecture, in order

Generated from the lecture (Week 6: Odometry, IMU Fusion and EKF State Estimation – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 1.3 The pose update implemented in the lab kit

```text
vx, vy, wz = forward(w, self.r_nom, self.L_nom)
th = self.th + 0.5 * wz * dt if self.integration == 'midpoint' else self.th
self.x += (vx * math.cos(th) - vy * math.sin(th)) * dt
self.y += (vx * math.sin(th) + vy * math.cos(th)) * dt
self.th = math.atan2(math.sin(self.th + wz * dt), math.cos(self.th + wz * dt))
```

## 1.4 The error model

```bash
cd docker
docker compose up -d ros2           # then open http://localhost:6080
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false
```

```bash
ros2 service call /reset_world std_srvs/srv/Empty
```

```bash
python3 ~/labs/week06/scripts/evaluate_drift.py ~/bags/w5_run1 --est /odom_raw
```

```bash
ros2 param list /wheel_odometry
ros2 param get /wheel_odometry wheel_radius
ros2 param get /wheel_odometry lx_plus_ly
```

```bash
ros2 bag record -s mcap --use-sim-time -o ~/bags/w6_fwd \
  /odom_raw /ground_truth/odom /wheel_speeds /imu/data_raw /tf /tf_static
python3 ~/labs/week06/scripts/drive_square.py straight --distance 2.0
python3 ~/labs/week06/scripts/evaluate_drift.py ~/bags/w6_fwd --est /odom_raw
```

```text
r_cal = 0.0375 * k_d          L_cal = 0.18 * k_d / k_theta
```

```bash
ros2 run tc70045e_sim wheel_odometry --ros-args -r __node:=wheel_odometry_cal \
  -r odom_raw:=odom_cal -r vel_raw:=vel_cal -r wheel_speeds:=wheel_speeds_cal \
  -p use_sim_time:=true -p publish_tf:=false \
  -p wheel_radius:=0.03787 -p lx_plus_ly:=0.18686
```

```bash
python3 ~/labs/week06/scripts/drive_square.py square --dir cw
```

```bash
python3 ~/labs/week06/scripts/calibrated_odometry.py --ros-args -p use_sim_time:=true \
  -p wheel_radius:=0.03789 -p lx_plus_ly:=0.18727 -p yaw_per_metre:=-0.0130 \
  -r odom_cal:=odom_c3 -r __node:=odom_c3
```

## 3.4 The Madgwick filter

```bash
ros2 run imu_filter_madgwick imu_filter_madgwick_node --ros-args \
  -p use_mag:=false -p publish_tf:=false -p world_frame:=enu -p use_sim_time:=true
ros2 param get /imu_filter_madgwick gain
```

```bash
ros2 launch ~/labs/week06/scripts/madgwick_sweep.launch.py
```

```bash
python3 ~/labs/week06/scripts/evaluate_drift.py ~/bags/w6_beta_nomag \
  --est /imu/data_b0p01 /imu/data_b0p05 /imu/data_b0p1 /imu/data_b0p3
```

## 4.2 Predict

```text
f(x) = [ x + v*cos(psi)*dt ,
         y + v*sin(psi)*dt ,
         psi + omega*dt    ,
         v                 ,
         omega             ]

          | 1  0  -v*sin(psi)*dt   cos(psi)*dt   0  |
          | 0  1   v*cos(psi)*dt   sin(psi)*dt   0  |
F = df/dx=| 0  0        1               0       dt |
          | 0  0        0               1        0 |
          | 0  0        0               0        1 |
```

## 4.5 robot_localization on the lab robot

```text
frequency: 30.0
two_d_mode: true
odom_frame: odom
base_link_frame: base_footprint
world_frame: odom
# order: x y z | roll pitch yaw | vx vy vz | vroll vpitch vyaw | ax ay az
odom0: /odom_raw
odom0_config: [false, false, false,  false, false, false,
               true,  true,  false,  false, false, true,
               false, false, false]
imu0: /imu/data
imu0_config:  [false, false, false,  false, false, false,
               false, false, false,  false, false, true,
               false, false, false]
```

```bash
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false odom_tf:=false

ros2 run imu_filter_madgwick imu_filter_madgwick_node --ros-args \
  -p use_mag:=false -p publish_tf:=false -p world_frame:=enu -p use_sim_time:=true

ros2 run robot_localization ekf_node --ros-args --params-file \
  $(ros2 pkg prefix tc70045e_sim)/share/tc70045e_sim/config/ekf.yaml -r odometry/filtered:=/odom
```

```bash
ros2 node info /ekf_filter_node
ros2 topic hz /odom
ros2 run tf2_ros tf2_echo odom base_footprint
```

```bash
ros2 topic echo /odom_raw --once --field twist.covariance
ros2 topic echo /imu/data --once --field angular_velocity_covariance
ros2 topic echo /odom --once --field pose.covariance
```

```bash
ros2 bag record -s mcap --use-sim-time -o ~/bags/w6_ekf_1 \
  /odom /odom_raw /imu/data /ground_truth/odom /tf /tf_static
python3 ~/labs/week06/scripts/drive_square.py square --dir cw
python3 ~/labs/week06/scripts/evaluate_drift.py ~/bags/w6_ekf_1 --est /odom_raw /odom --plot
```

```bash
ros2 run robot_localization ekf_node --ros-args --params-file   ~/labs/week06/params/ekf_cal.yaml -r odometry/filtered:=/odom
```

## 🤖 AI co-pilot

```text
Here is my robot_localization ekf.yaml for a 4-wheel mecanum robot fusing
wheel odometry (/odom_raw, nav_msgs/Odometry, integrated from encoder
velocities) with a Madgwick-filtered IMU (/imu/data), magnetometer off,
on a flat floor.

For EACH of the 15 booleans in odom0_config and imu0_config, state (a) the
state variable it refers to, in order, (b) whether my value is defensible,
and (c) if not, the double-counting or observability problem it creates.
Then tell me which quantity, if any, I fuse from two sources, and whether
that is a problem. Give me a table and your reasoning, not a new file.
```
