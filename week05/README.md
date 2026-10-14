# Week 05 – Fuse for Better Localisation: IMU + Wheel Odometry → EKF

Since Week 2 the robot has known where it is from two things: **wheel odometry** (count the wheel turns) and
**SLAM** (match the laser scan to the map). Wheel odometry alone drifts: on the 24 m circuit of Week 4 it ended
**more than a metre** from the truth. This week you add a third sensor that has been on the robot all along, the
**IMU** (gyroscope + accelerometer), and fuse it with the wheels in an **extended Kalman filter** (EKF,
`robot_localization`). Then you **measure** what the fusion gained – against the simulator's true position.

**Watch the demo video first:** `TC70045E_Week05_demo.mp4` in the Week 5 folder on Blackboard. It shows every step
below, with Gazebo (the simulated world) and RViz (what the robot knows) side by side.

| Time in class | Part |
|---|---|
| 45 min | lecture: why wheel odometry drifts, inside a MEMS IMU, how an EKF combines sensors |
| 10 min | Step 0 – start the container |
| 70 min | Activities A1–A4 |
| 55 min | Your activity (the TODO) – configure the EKF and prove it helps |

---

## Step 0 – Start the container (once per session)

Exactly as in Week 2 ([week02/README.md](../week02/README.md#step-0--start-the-container-once-per-session)):
`docker start tc70045e`, open <http://localhost:6080>, **Connect**, open **Terminator** and run `update-labs`.
Split Terminator into three terminals (T1, T2, T3).
Check: `ls ~/labs/week05` lists `config  launch  odometry_calibration  qos_and_rosbag  README.md  rviz  scripts`.

**Before every new launch:** Ctrl+C in T1 and wait for the `$` prompt. If the launch then dies with
"process has died … gzserver", run `pkill -f gzserver`, wait 5 s, launch again.

## The bricks this week

| Brick / file | What it does |
|---|---|
| [`launch/fusion.launch.py`](launch/fusion.launch.py) | robot in Gazebo + gyro calibration + IMU filter + EKF + slam_toolbox + RViz + the scoring script. Switches: `odom:=raw` or `odom:=ekf`, `ekf_config:=…`, `gyro_cal`, `slam`, `drive`, `gui`, `rviz` |
| [`config/ekf.yaml`](config/ekf.yaml) | the EKF settings. **Your activity** has three TODOs in this file |
| [`scripts/gyro_bias.py`](scripts/gyro_bias.py) | gyro calibration: lets the robot settle for 3 s, measures the gyro's offset over the next 8 s while the robot stands still, then subtracts it (`/imu/data_raw` → `/imu/data_cal`) |
| [`scripts/drive_and_score.py`](scripts/drive_and_score.py) | drives the Week 4 circuit (24.4 m, 210 s), draws three trails in RViz and prints the error of wheel odometry, EKF and SLAM against the truth |
| [`rviz/fusion.rviz`](rviz/fusion.rviz) | map, laser, robot, and the trails: **green** truth, **red** wheel odometry, **blue** EKF |

The important switch is **who publishes the transform `odom → base_footprint`** (where the robot is in the odometry
frame). With `odom:=raw` it is the wheel-odometry node, as in Weeks 2–4. With `odom:=ekf` the launch file tells the
simulator not to publish it (`odom_tf:=false`) and the EKF publishes it instead. There must only ever be **one**
publisher of a transform.

The scoring script steers on `/ground_truth/odom`, the simulator's exact position. It is a test harness: the wheel
odometry, the EKF and SLAM never see that topic.

---

## A1 – Wheel odometry drifts (20 min)

**Goal:** see how far wheel odometry alone goes wrong, and that SLAM corrects it.

| | |
|---|---|
| T1 | `ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=raw drive:=true` |

`drive:=true` starts the robot on the 24 m circuit 30 s after the launch (after the gyro calibration). **Do not drive the robot yourself** while it
runs. Watch RViz: the **green** trail is where the robot really goes, the **red** trail is where wheel odometry thinks
it goes.

**You should see:** the red trail bends away from the green one at every turn. At the end (210 s) T1 prints a table, e.g.

```
                    end [m]   RMS [m]   max [m]   heading at end [deg]
wheel odometry        1.339     0.772     1.576     -15.2
EKF                 (not running)
SLAM                  0.011     0.019     0.051      -0.2
```

Measured on three runs: wheel odometry **1.1 – 1.3 m** off at the end, heading **−9° to −15°**; SLAM **1 – 2 cm**.
**Check:** the heading error is only about 10°. Why is the position error then more than a metre? (Lecture: error ≈
distance × sin(heading error).)

## A2 – Meet the gyro (15 min)

**Goal:** see the IMU's data and its turn-on bias – a gyro that says "turning" when the robot stands still.

Leave A1 running (the robot is stopped at the end), or launch again with `drive:=false`.

| | |
|---|---|
| T2 | `ros2 topic hz /imu/data_raw` (Ctrl+C after 5 s) |
| T2 | `ros2 topic echo --once /imu/data_raw --field angular_velocity` |
| T2 | `python3 ~/labs/week05/scripts/gyro_bias.py --ros-args -p use_sim_time:=true -r /imu/data_cal:=/imu/test` (Ctrl+C after its log line) |

**You should see:** about 100 Hz. The robot is not moving, yet `angular_velocity.z` is not zero: a few thousandths
of a rad/s. `gyro_bias.py` waits 3 s, averages 8 s of data and prints the offset, e.g.
`gyro bias measured over 8.0 s (801 samples): ... z +0.0025 rad/s (z = +0.14 deg/s)` (measured on twelve starts:
−0.23 to +0.20 °/s). The simulated gyro draws a new
turn-on bias every time it starts (as a real MEMS gyro does at every power-up), so your number differs.
**Check:** integrate it – how many degrees of heading error would 0.10 °/s cause on the 210 s circuit?

## A3 – The EKF, as given (20 min)

**Goal:** start the EKF brick with the settings in [`config/ekf.yaml`](config/ekf.yaml) as they are now, and see
that it does not help yet.

| | |
|---|---|
| T1 | Ctrl+C, then `ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=ekf drive:=true` |
| T2 | `ros2 topic hz /odometry/filtered` (measured: 25 Hz; it is set to 30 and slows down on a busy computer) |

Open [`config/ekf.yaml`](config/ekf.yaml) while it drives and read the comments. Each sensor has a list of 15
`true`/`false` values: which parts of the robot's state (position, angles, velocities, accelerations) the EKF takes
from that sensor.

**You should see:** the **blue** EKF trail lies exactly on the **red** wheel trail. At the end the table shows the same
error for both (measured: 1.11 m and 1.11 m). The EKF is running – but it only uses the wheels, and it takes the
wheels' *position* as if it were a measurement. Your activity fixes that.

## A4 – Who owns the transform? (15 min)

**Goal:** check that exactly one node publishes `odom → base_footprint`.

With A3 still running (or launched again):

| | |
|---|---|
| T2 | `ros2 param get /wheel_odometry publish_tf` |
| T2 | `ros2 param get /ekf_filter_node publish_tf` |
| T2 | `ros2 run tf2_ros tf2_echo odom base_footprint` (Ctrl+C after a few lines) |
| T3 | `ros2 topic echo --once /odometry/filtered --field pose.pose.position` |

**You should see:** with `odom:=ekf` the wheel-odometry node says `False` and the EKF says `True`: one owner. The
translation that `tf2_echo` prints is the position in `/odometry/filtered`. Now Ctrl+C T1, launch with `odom:=raw`
and ask again: the wheel-odometry node says `True` and the EKF is `Node not found`. The lecture shows what goes wrong
with two owners: the transform jumps between two answers.

---

## Your activity (the TODO) – configure the EKF and prove it helps (55 min)

**What you build:** an EKF configuration that fuses the wheels and the gyro correctly, and a table that shows – with
numbers – how much better the robot knows where it is.

1. **Copy the settings** (keep the original): `cp ~/labs/week05/config/ekf.yaml ~/labs/week05/config/my_ekf.yaml`
2. **Open your copy** in VSCodium (desktop icon) or `nano ~/labs/week05/config/my_ekf.yaml`. Three TODOs:
   * **TODO 1 – `imu0_config`:** the gyro measures the **yaw rate** (turning speed about the vertical axis) directly,
     without the wheels' slip. Switch on that one entry. (The order of the 15 values is in the comment at the top.)
   * **TODO 2 – `odom0_config`:** the wheel odometry's **position and heading** are just its velocities added up.
     Give the EKF the velocities *and* the position, and it counts the same measurement twice – and believes the
     wheels' position over everything else. Decide which entries to switch off.
   * **TODO 3 – `two_d_mode`:** the robot drives on a flat floor. No sensor here measures height, roll or pitch.
     What should the filter do with them?
3. **Run it** (one TODO at a time is best – then you see what each one does):
   `ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=ekf drive:=true ekf_config:=$HOME/labs/week05/config/my_ekf.yaml`
4. **Once more without the gyro calibration**, to see the turn-on bias of A2 in the result:
   `... ekf_config:=$HOME/labs/week05/config/my_ekf.yaml gyro_cal:=false`
5. **Done when** – all four are true:
   * in RViz the **blue** EKF trail stays close to the **green** truth while the **red** wheel trail bends away;
   * the final table shows the EKF's end error **smaller than the wheel odometry's** (if it is not, run it again:
     the gyro differs every start – and if it is still not, check TODO 2);
   * the line `EKF height z at the end` shows 0.000 m and a variance below 0.001 m² (TODO 3);
   * you have a table: one row per configuration (as given, TODO 1, TODO 1+2, all three, all three without
     `gyro_cal`) × (EKF end error, RMS, heading at the end, SLAM end error).

### Solution (compare after you have tried)

[`../solutions/week05/ekf.yaml`](../solutions/week05/ekf.yaml) – run it with
`ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=ekf drive:=true ekf_config:=$HOME/labs/solutions/week05/ekf.yaml`.

Measured 14 Oct 2026 (simulated, 24.4 m circuit, 210 s; every start draws a new gyro bias, so runs differ):

| Configuration | Runs | EKF error at the end | EKF heading at the end | SLAM error at the end |
|---|---|---|---|---|
| wheel odometry alone (`odom:=raw`) | 2 | (wheels) 1.12 – 1.34 m | −10° to −15° | 1.1 – 1.2 cm |
| EKF as given | 2 | 1.11 – 1.30 m – the same as the wheels | −9° to −14° | 0.1 – 2.3 cm |
| TODO 1 only (gyro on, wheel position still fused) | 1 | 1.28 m – still the wheels | −10° | – |
| TODO 1 + 2 (two_d_mode still false) | 2 | 0.02 – 0.47 m | +3° to +12° | 1.1 cm – but z variance 4 × 10⁸ m² |
| **all three (solution), gyro calibrated** | 9 | **0.03 – 0.83 m** (median 0.35 m) | −16° to +6° | 0.4 – 0.8 cm |
| solution, `gyro_cal:=false` | 3 | 0.02 – 1.20 m | −6° to +23° | 1.0 – 1.2 cm |

Wheel odometry in the same runs: 0.97 – 1.50 m and −8° to −15°. The EKF was better than the wheels in every
run – by 1.5 times in the worst run and 50 times in the best.

What the numbers say:
* **TODO 2 is the one that unlocks the EKF.** While the wheels' position is fused, the EKF follows the wheels whatever
  else you give it.
* **TODO 3 changes nothing you can see in x and y** – but in 3D mode the height's variance grows to 4 × 10⁸ m²: the
  filter says "I have no idea how high I am". Anything that reads the covariance (Nav2, a second EKF, a logger)
  gets nonsense.
* **The gyro calibration matters:** without it one run ended 23° and 1.2 m off – as bad as the wheels.
* **Even calibrated, the EKF drifts – and by a different amount every run.** The heading error comes from the gyro's
  readings during the drive: in one run we measured its bias at 0.0033 rad/s at standstill but 0.0029 rad/s on
  average over the drive (bias instability). No calibration at the start can remove that – a sensor that sees the
  world can. Here that sensor is the LiDAR, through SLAM. Run your configuration more than once before you conclude.
* **SLAM was within about 2 cm with or without the EKF.** In this lab the laser always sees walls; even with fast turns
  (`turn_rate:=1.0`) and a 3.5 m laser range (`lidar_range:=3.5`) slam_toolbox stayed at 1 cm. The EKF earns its
  place where the laser cannot help: long featureless corridors, open halls, glass walls, smoke – and between two
  laser scans, where Nav2's controller needs a smooth pose 20 times a second.

### For your report

Your table, a screenshot of RViz with the three trails, and one paragraph: which TODO made the biggest difference,
and why? Did the EKF make the **SLAM** result better in this lab – and if not, when would it matter? Label all results
as simulated.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| RViz: no red/blue/green trails | the trails start when `drive_and_score.py` starts, 30 s after the launch |
| No blue trail | the launch was started with `odom:=raw` (no EKF), or the EKF has no data: `ros2 topic hz /odometry/filtered` |
| T1: `Failed to meet update rate!` from `ekf_node` | the computer is busy; harmless if it appears now and then |
| The EKF trail spins or jumps away | an `imu0_config` entry other than the yaw rate is on (e.g. accelerations: integrated twice they drift fast) |
| The robot in RViz flickers between two places | two publishers of `odom → base_footprint`: start with `odom:=ekf`, which switches the wheel TF off |
| Launch dies: "process has died … gzserver" | `pkill -f gzserver`, wait 5 s, launch again |

Optional extras from the previous course, in this folder: [`odometry_calibration/`](odometry_calibration/) (calibrate
the wheel radius and track width, sweep the Madgwick filter gain, EKF on a square) and
[`qos_and_rosbag/`](qos_and_rosbag/) (quality of service, recording and replaying with rosbag2).
