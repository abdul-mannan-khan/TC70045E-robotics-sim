# P1 – How much does a gyroscope help? IMU + wheel-odometry fusion with an EKF

**Question:** a mobile robot that counts its wheel turns drifts by about a metre on a 24 m drive. How much of that
drift does a cheap MEMS gyroscope remove when the two are fused in an extended Kalman filter (EKF) – and what decides
whether the fusion helps or hurts?

| | |
|---|---|
| Sensors → actuators | wheel encoders + MEMS IMU (gyroscope, accelerometer) → two drive motors |
| Simulator | Gazebo (the world) + RViz (what the robot knows); `robot_localization` EKF; slam_toolbox |
| Container | `abdulmannan617/tc70045e-ros2:humble` – **no GPU needed**, your laptop is enough |
| Starts from | [Week 5](../../week05/README.md) – lab README, demo video `TC70045E_Week05_demo.mp4` on Blackboard |
| You change | a settings file (`ekf.yaml`) and the start command – **no Python needed** |

## What you will learn

Docker and the browser desktop · ROS 2 launch files, topics, parameters and transforms · how an IMU and wheel
encoders measure motion and how each goes wrong (wheel slip, gyro bias) · what an EKF does with them · measuring
against ground truth, over several runs.

## 1. Start (every session)

On your laptop (Week 0 guide, [docs/GETTING_STARTED.md](../../docs/GETTING_STARTED.md)): `docker start tc70045e`,
open <http://localhost:6080>, **Connect**, open **Terminator**, run `update-labs`. Make your project folder once:

```bash
mkdir -p ~/work/project && cp ~/labs/projects/P1_imu_ekf_fusion/results_template.csv ~/work/project/results.csv
cp ~/labs/solutions/week05/ekf.yaml ~/work/project/ekf_solution.yaml
```

## 2. The baseline you reproduce (Assessment 1)

Each run drives the 24.4 m circuit by itself (210 s) and prints a table at the end. **Do not touch the robot while
it drives.** Before every new run: Ctrl+C, wait for the `$` prompt.

| Configuration (`config` column) | Command (one line) |
|---|---|
| `wheels only` | `ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=raw drive:=true` |
| `EKF as given` | `ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=ekf drive:=true` |
| `EKF solution` | `ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=ekf drive:=true ekf_config:=$HOME/work/project/ekf_solution.yaml` |

The printed table looks like this – copy the numbers into your results file, one row per run:

```
                    end [m]   RMS [m]   max [m]   heading at end [deg]
wheel odometry        1.339     0.772     1.576     -15.2
EKF                   0.351     0.190     0.402      -4.1
SLAM                  0.011     0.019     0.051      -0.2
```

**Course measurements (14 Oct 2026)** – yours should be in the same range, not identical (every start draws a new
gyro bias): wheels alone 1.12 – 1.34 m off at the end; EKF as given the same as the wheels; EKF solution
0.03 – 0.83 m (median 0.35 m over 9 runs); SLAM about 1 cm.

## 3. Where to edit, and how

Edit **your copy** `~/work/project/my_ekf.yaml` (make it with
`cp ~/work/project/ekf_solution.yaml ~/work/project/my_ekf.yaml`), and run it with
`ekf_config:=$HOME/work/project/my_ekf.yaml` at the end of the launch line.

| To test… | In | Search for (Ctrl+F) | Change | What to expect / think about |
|---|---|---|---|---|
| the gyro's turn-on bias | launch line | – | add `gyro_cal:=false` | more heading error, more spread between runs |
| fast vs gentle driving | launch line | – | `turn_rate:=0.6` or `1.0` (default 0.3 rad/s); `speed:=0.3` (default 0.15 m/s) | wheels slip more in fast turns: does the EKF gain grow? |
| a longer drive | launch line | – | `laps:=2` or `3` | does the error grow with distance? for the wheels and for the EKF? |
| how much the EKF trusts its model | `my_ekf.yaml` | `process_noise_covariance` | the 12th diagonal value (yaw rate, `0.02`): try `0.002` and `0.2` | small = trusts its own prediction, large = follows the sensors |
| adding the accelerometer | `my_ekf.yaml` | `imu0_config` | last row `false, false, false` → `true, true, false` | a common mistake – measure why it is one |
| the old, wrong set-up | `my_ekf.yaml` | `odom0_config` | first row `false, false, false` → `true, true, false` | the wheels' position counted twice: the gain disappears |

YAML rules: keep the indentation, keep the commas and the square brackets; `true`/`false` in lower case. If the
launch then fails, the error message names the line.

Optional, for the ambitious: `csv:=$HOME/work/project/run1.csv` on the launch line also saves the trails (truth,
wheels, EKF, SLAM, twice a second). Plot the headings against time:
`python3 ~/labs/projects/tools/plot_timeseries.py ~/work/project/run1.csv --columns truth_yaw,raw_yaw,ekf_yaw --out ~/work/project/fig_yaw.png`.

## 4. Experiments

* **Assessment 1 (Week 6):** the three baseline configurations, **at least 2 runs each**, plus **one change of your
  own** from the table, 3 runs.
* **Assessment 2 (Week 12):** **at least two more factors** from the table (or your own idea, agreed with the module
  leader), **3 or more runs** for every configuration, one of them as a sweep of at least three values (e.g.
  `turn_rate` 0.3 / 0.6 / 1.0).

## 5. Results file and figures

`results_template.csv` has one row per run. Columns: `config, run, date, computer, wheel_end_m, wheel_heading_deg,
ekf_end_m, ekf_rms_m, ekf_heading_deg, slam_end_m, notes`.

```bash
python3 ~/labs/projects/tools/plot_results.py ~/work/project/results.csv --metric ekf_end_m \
    --ylabel "EKF position error at the end [m]" --out ~/work/project/fig_ekf_end.png
```

## 6. Your paper (Assessment 2)

* **Possible title:** *Gyro-aided EKF odometry for an indoor mobile robot: a simulation study of drift, bias and
  driving style.*
* **Contribution:** a measured answer – "fusing the yaw-rate gyro cut the end error from X to Y m (n runs), but only
  when …" – plus the conditions under which it does not help.
* **Figures:** RViz screenshot with the three trails; bar chart of end error per configuration; a sweep plot
  (error against turn rate or laps).
* **Be honest about limits:** simulated sensors and noise models; one floor plan; SLAM corrects drift here anyway
  (Week 5 explains when the EKF still matters).
