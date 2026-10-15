# P4 – Driverless shuttle: from a robot shuttle in the hall to a self-driving shuttle on the road

| | Part A – Assessment 1 (Weeks 1–6) | Part B – Assessment 2 (Weeks 7–12) |
|---|---|---|
| You build | a **robot shuttle** that runs between stops in a building: it drives to each stop by itself and you make it **know where it is** by fusing its wheels with its gyroscope (EKF). You write its **timetable** from measured run times | the **road shuttle**: a self-driving car in CARLA that keeps its lane, holds its speed with a PI controller, and **drives your timetable** – drive, stop, drive on – first through the CARLA API, then as a ROS 2 node |
| Lectures | Week 3 (Nav2, goals from Python), Week 5 (IMU + wheel odometry → EKF) | Week 11 (CARLA without and with ROS 2, cruise control, drive-by-wire) |
| Simulator | Gazebo + RViz, Nav2, robot_localization | CARLA 0.9.15, Town04 (+ CARLA ROS 2 bridge) |
| Container | `abdulmannan617/tc70045e-ros2:humble` – laptop, no GPU | `abdulmannan617/tc70045e-carla:latest` – NVIDIA GPU (8 GB+): Vast.ai |
| Demo videos (Blackboard) | `TC70045E_Week03_demo.mp4`, `TC70045E_Week05_demo.mp4` | `TC70045E_Week11_demo.mp4` |

**How Part B extends Part A:** the shuttle's **timetable** (`timetable.csv`) is made in Part A from your robot's
measured run times between stops; Part B's car drives it. The control and estimation ideas carry over too: a PI
controller and its steady-state error (Week 1), sensors measured against the truth over repeated runs (Week 5). In
Assessment 2 you show both shuttles keeping the same timetable.

---

## Part A – the robot shuttle (Assessment 1)

### Start (every session)

Laptop: `docker start tc70045e`, <http://localhost:6080>, **Connect**, **Terminator**, `update-labs`, T1–T3. Once:

```bash
mkdir -p ~/work/project && cp ~/labs/projects/P4_driverless_shuttle/results_partA.csv ~/labs/projects/P4_driverless_shuttle/results_partB.csv ~/work/project/
cp ~/labs/solutions/week05/ekf.yaml ~/work/project/my_ekf.yaml
```

### A1 – the shuttle runs between stops (Week 3)

T1: `ros2 launch ~/labs/week03/launch/nav.launch.py gui:=true` (wait for `AMCL confirmed the start pose`). Choose three
or more stops in the two rooms (RViz **Publish Point**, `ros2 topic echo /clicked_point`), and drive stop to stop with
`python3 ~/labs/week03/scripts/go_to.py X Y YAW` – it prints `RESULT SUCCEEDED after … s`. **Course:** start → doorway
(4.0, −1.0) SUCCEEDED in 14–16 s in three cold starts. Run your route 3 times and write the timetable
`~/work/project/timetable.csv` (Excel is fine): a header `leg,drive_s,dwell_s` and one line per leg – its **mean
driving time** over your runs and the **dwell time** you choose at the stop, e.g. `start-doorway,15.2,10`.

### A2 – the shuttle knows where it is (Week 5)

Each run drives a 24.4 m circuit by itself and prints the position error of the wheels, the EKF and SLAM against the
truth. Before each launch: Ctrl+C and wait for the `$` prompt.

| `config` | T1 |
|---|---|
| `wheels only` | `ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=raw drive:=true` |
| `EKF as given` | `ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=ekf drive:=true` |
| `EKF solution` | `ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=ekf drive:=true ekf_config:=$HOME/labs/solutions/week05/ekf.yaml` |

**Course (14 Oct 2026):** wheels alone 1.12–1.34 m off after 24 m; EKF solution 0.03–0.83 m (median 0.35 m, 9 runs);
SLAM about 1 cm.

### Where to edit, and how

Your copy `~/work/project/my_ekf.yaml`, run with `ekf_config:=$HOME/work/project/my_ekf.yaml` on the launch line.

| To test… | In | Change |
|---|---|---|
| the gyro's turn-on bias | launch line | `gyro_cal:=false` |
| a faster shuttle | launch line | `speed:=0.3` (default 0.15 m/s), `turn_rate:=0.6` (default 0.3) |
| a longer service | launch line | `laps:=2` / `3` |
| how much the EKF trusts its model | `my_ekf.yaml`, Ctrl+F `process_noise_covariance` | the 12th value on the diagonal (yaw rate, `0.02`): `0.002` / `0.2` |
| a classic mistake | `my_ekf.yaml`, Ctrl+F `odom0_config` | first row `false, false, false` → `true, true, false` (the wheels' position counted twice) |

YAML: keep indentation, commas, brackets; `true` / `false` in lower case.

### Part A experiments (minimum)

Your stop-to-stop route 3 times and your timetable · the three EKF configurations 2 runs each · one factor from the
table at three values (3 runs).

---

## Part B – the road shuttle (Assessment 2)

### Start (every session)

1. Rent a GPU machine with the **CARLA** image ([docs/RUN_ON_VAST.md](../../docs/RUN_ON_VAST.md), 12 GB GPU
   comfortable); note instance, price, times. Desktop → terminal → `update-labs`, T1–T3. Copy `timetable.csv` and
   `results_partB.csv` into `~/work/project/`. Once:
   `cp ~/labs/week11/scripts/02_cruise_control_api.py ~/work/project/my_shuttle.py`
2. T1: `carla-sim start --town Town04` – wait for `CARLA is up`.
3. **At the end:** download `~/work/project/` (and `~/cruise_api.csv` after each run), then **Destroy** the machine.

### Baseline to reproduce

| | |
|---|---|
| T2 | `python3 ~/labs/week11/scripts/02_cruise_control_api.py --target 50 --show` → `RESULT last 10 s: mean 50.0 km/h, max error 0.1 km/h` |
| T2 | the same with `--ki 0` → `mean 46.8 km/h, max error 3.4 km/h` – the P controller's steady-state error |
| T2 | ROS 2: the bridge (Week 11 A3 command), then `python3 ~/labs/week11/scripts/03_cruise_control_ros2.py --ros-args -p target_kmh:=50.0` → 0 → 55 km/h peak → 50.0 km/h |

(Course measurements, 15 Oct 2026.) Every run writes `~/cruise_api.csv` (time, speed, throttle, brake): copy it to
`~/work/project/<config>_run<N>.csv` before the next run.

### The hand-over: drive your timetable

In `~/work/project/my_shuttle.py`:

1. Ctrl+F `def main():` and, **above** it, paste the lines below. Then write your own timetable into the first line:
   each leg of `timetable.csv` becomes "drive at 50 km/h from time T" followed by "0 km/h from time T + drive_s"
   (the stop), and the next leg starts after `dwell_s`. Example – one leg of 20 s, a 10 s stop, then on:
   ```python
   TIMETABLE = [(0, 50), (20, 0), (30, 50)]    # (from this time [s], target speed [km/h]): drive, stop 10 s, drive on


   def target_at(t):
       target = TIMETABLE[0][1]
       for start, kmh in TIMETABLE:
           if t >= start:
               target = kmh
       return target
   ```
2. Ctrl+F `err = a.target - kmh` and change it to `err = target_at(i * s.fixed_delta_seconds) - kmh`.
3. Run: `python3 ~/work/project/my_shuttle.py --show --seconds 60`. Checked to run as Python; the stop-and-go drive
   itself was not run by the course – watch the first one.

| Then test… | Change | Look at (plot `~/cruise_api.csv`) |
|---|---|---|
| controller tuning | `--kp 0.05` / `0.15` / `0.30`, `--ki 0` / `0.02` / `0.05` | overshoot, time to reach speed, stopping |
| comfort | your timetable: gentler steps (50 → 30 → 0 instead of 50 → 0) | largest deceleration from the log |
| the ROS 2 shuttle (Week 11 A3) | ask Claude Code to add the same `target_at` to your copy of `03_cruise_control_ros2.py`, then run it through the bridge | the same timetable as a ROS 2 node: same result? |

### Part B experiments (minimum)

The course cruise control 3 runs (with and without `--ki`) · your timetable 3 runs · controller tuning at ≥ 3
values (3 runs each) · the ROS 2 node once with your timetable.

---

## Results and figures

`results_partA.csv`: `config, run, date, computer, leg, leg_time_s, wheel_end_m, ekf_end_m, ekf_rms_m,
ekf_heading_deg, slam_end_m, notes` · `results_partB.csv`: `config, run, date, computer, kp, ki, timetable,
mean_speed_last10_kmh, max_error_kmh, stops_held, max_decel_note, log_file, notes`.
`python3 ~/labs/projects/tools/plot_timeseries.py ~/work/project/tt_run1.csv --columns speed_kmh,throttle,brake --out ~/work/project/fig_run.png`

**Paper idea:** *A driverless shuttle from the test hall to the road: odometry fusion on a ground robot and PI speed
control with a timetable in CARLA.* Figures: the three trails in RViz; EKF error per configuration; the car's speed
against its timetable; P against PI.
