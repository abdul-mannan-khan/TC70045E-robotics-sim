# P1 – Security: a patrol robot that calls in a drone

| | Part A – Assessment 1 (Weeks 1–6) | Part B – Assessment 2 (Weeks 7–12) |
|---|---|---|
| You build | a **mobile robot** that patrols a building at night by itself and writes an **alarm log** of every checkpoint it could not reach | a **security drone** that takes your robot's alarm log, flies to each alarmed spot, photographs it and comes home – and lands at once if its position data fails |
| Lectures | Week 2 (ROS 2 bricks, safety stop), Week 3 (Nav2 navigation, patrol) | Week 10 (drone with ROS 2: bridges, mission node, watchdog); Week 9 to meet AirSim; Week 12 (pre-flight check) optional |
| Simulator | Gazebo + RViz + ROS 2 Nav2 | AirSim + PX4 + ROS 2 (town world) |
| Container | `abdulmannan617/tc70045e-ros2:humble` – laptop, no GPU | `abdulmannan617/tc70045e-drone:latest` – NVIDIA GPU: Vast.ai |
| Demo videos (Blackboard) | `TC70045E_Week02_demo.mp4`, `TC70045E_Week03_demo.mp4` | `TC70045E_Week09_demo.mp4`, `TC70045E_Week10_demo.mp4` |

**How Part B extends Part A:** the robot and the drone talk through a file – the robot's `alarms.csv`. Part A
produces it; Part B's drone reads it ([`../tools/handover.py`](../tools/handover.py)) and turns the alarmed checkpoints
into its route. In Assessment 2 you show the whole chain: robot patrol → alarm log → drone check → photos.

---

## Part A – the patrol robot (Assessment 1)

### Start (every session)

On your laptop (Week 0 guide): `docker start tc70045e`, open <http://localhost:6080>, **Connect**, **Terminator**,
`update-labs`, split into T1, T2, T3. Once:

```bash
mkdir -p ~/work/project && cp ~/labs/projects/P1_security/results_partA.csv ~/labs/projects/P1_security/results_partB.csv ~/work/project/
cp ~/labs/solutions/week03/patrol.py ~/work/project/my_patrol.py
```

T1 every time: `ros2 launch ~/labs/week03/launch/nav.launch.py gui:=true` – wait for `AMCL confirmed the start pose`.

### Baseline to reproduce

T2: `python3 ~/labs/solutions/week03/patrol.py 1` → one line per checkpoint, then
`RESULT 5 of 5 waypoints reached, total 93 s, mean 18.5 s per waypoint`. **Course measurements (7 Oct 2026):** 5 of 5
in three cold starts, 91–95 s per lap. T3 while it drives to the doorway: `python3 ~/labs/week03/scripts/drop_box.py 2.0 -1.0`
– Nav2 drives round the box. `drop_box.py --remove` takes it away.

### Where to edit, and how

Open `~/work/project/my_patrol.py` in VSCodium (or `nano`), Ctrl+F for the text in the second column. Run it with
`python3 ~/work/project/my_patrol.py 2` (2 laps).

| Step | Search for | Change | Check |
|---|---|---|---|
| 1 your own round | `WAYPOINTS = [` | your checkpoints `('name', x, y, heading_deg),` – read x, y with RViz **Publish Point** and `ros2 topic echo /clicked_point` (T3); at least 5, both rooms, 0.5 m from walls | every checkpoint REACHED |
| 2 the alarm log (**required** – Part B needs it) | the line that starts `print('lap %d` | below it, add the two lines shown under this table | `~/work/project/alarms.csv` has one row per checkpoint visit |
| 3 an intruder's obstacle | T3 during the patrol | `drop_box.py X Y` on a checkpoint | that checkpoint is FAILED in the log, the patrol carries on |
| 4 giving up sooner | `TIME_LIMIT = 90.0` | `30`, `60`, `90` s | time lost on a blocked checkpoint |
| 5 safety distance | T3 after the launch | `ros2 param set /global_costmap/global_costmap inflation_layer.inflation_radius 0.15` (default 0.35; try 0.15 / 0.35 / 0.8) | path shape and time |

The alarm-log lines for step 2 – paste them directly below the `print('lap %d …` line, with the same 12 spaces in
front of `with` (the loop already has `name`, `x`, `y`, `ok` and `seconds`; checked to run):

```python
            with open(os.path.expanduser('~/work/project/alarms.csv'), 'a') as log:
                log.write('%s,%.2f,%.2f,%s,%.1f\n' % (name, x, y, 'REACHED' if ok else 'FAILED', seconds))
```

Put `import os` at the top of the file if it is not there, and before the first run create the file with its header:
`echo "name,x,y,status,time_s" > ~/work/project/alarms.csv`.

### Part A experiments (minimum)

The course patrol 3 runs · your own round, 2 laps × 2 runs · one blocked checkpoint (your alarm log shows FAILED) ·
one factor of step 4 or 5 at three values.

---

## Part B – the security drone (Assessment 2)

### Start (every session)

1. Rent a GPU machine with the **drone** image ([docs/RUN_ON_VAST.md](../../docs/RUN_ON_VAST.md), about
   $0.10–0.20 an hour, 80 GB disk). Note the instance number, price and times. Open its desktop, terminal, `update-labs`.
2. Copy your Part A files onto it (Firefox → your OneDrive, or `git clone` your fork): at least `alarms.csv` and
   `results_partB.csv` into `~/work/project/`. Once: `cp ~/labs/solutions/week10/mission_node.py ~/work/project/my_drone.py`
3. T1: `drone-sim start --world neighborhood` (wait for `PX4 SITL is ready for take-off`) · T2:
   `python3 ~/labs/week10/scripts/03_airsim_ros2_bridge.py` · T3: `python3 ~/labs/week10/scripts/04_px4_ros2_bridge.py`
   · optional RViz: `rviz2 -d ~/labs/week10/scripts/airsim.rviz`
4. **At the end:** download `~/work/project/` and `~/mission/`, then **Destroy** the machine.

### Baseline to reproduce

T4: `python3 ~/labs/solutions/week10/mission_node.py` – take-off to 15 m, a 10 m square, a photo at each corner
(`~/mission/wp01.png` …), landing, `RESULT 34 s, 39.1 m flown, worst waypoint miss 0.42 m, finished 0.10 m from the start`.
**Course (15 Oct 2026):** 4 of 4 in 34 s, worst miss 0.42–0.47 m. Watchdog: Ctrl+C in T2 during the flight →
`WATCHDOG: no odometry for 1 s - landing now`.

### Where to edit, and how – the hand-over

1. **Check the hand-over first, without flying:**
   `python3 ~/labs/projects/tools/handover.py ~/work/project/alarms.csv --scale 3 --only FAILED`
   It prints the drone waypoints (your building's map × 3, so a 10 m room becomes a 30 m town block). Every point must
   be within 30 m of take-off – the tool refuses farther ones.
2. **Use it in your drone:** in `~/work/project/my_drone.py`, Ctrl+F `WAYPOINTS = [`, and replace that line with:
   ```python
   import os, sys
   sys.path.insert(0, os.path.expanduser('~/labs/projects/tools'))
   from handover import load_points
   WAYPOINTS = load_points('~/work/project/alarms.csv', scale=3.0, only='FAILED') + [(0.0, 0.0)]
   ```
3. **Fly it:** T4 `python3 ~/work/project/my_drone.py` – one photo per alarm in `~/mission/`.

| Then test… | Search for | Change |
|---|---|---|
| speed against accuracy | `SPEED, TOL, STILL = 2.0, 0.5, 0.2` | first number `1.0` / `2.0` / `3.0` m/s |
| sharp evidence photos | same line | third number (`STILL`) `0.1` / `0.2` / `0.5` m/s; measure with `python3 ~/labs/projects/tools/sharpness.py ~/mission/wp*.png` |
| the safety watchdog | `return time.monotonic() - self.t_odom < 1.0` | `0.5` / `1.0` / `2.0` s, and Ctrl+C in T2 at the same point of the flight each time |
| optional: a pre-flight check before every call-out | T4, before the flight | `python3 ~/labs/solutions/week12/preflight.py --alt 15 --length 30 --width 30 && python3 ~/work/project/my_drone.py` (Week 12) |

The hand-over and routes longer than the course's 10 m square were not flown by the course: start with one alarm,
watch the drone in AirSim, and keep to the streets at 15 m.

### Part B experiments (minimum)

The course mission 3 runs · the whole chain (patrol with ≥ 2 blocked checkpoints → alarm log → drone) **3 times** ·
two factors from the table at ≥ 3 values, 3 runs each · the watchdog test.

---

## Results and figures

`results_partA.csv`: `config, run, date, computer, laps, checkpoints, reached, failed, total_s, mean_s_per_checkpoint,
inflation_m, time_limit_s, obstacles, notes` · `results_partB.csv`: `config, run, date, computer, alarms_in,
waypoints_reached, photos, time_s, flown_m, worst_miss_m, end_from_start_m, speed_mps, still_mps, watchdog_s,
sharpness_mean, watchdog_fired, notes`.
`python3 ~/labs/projects/tools/plot_results.py ~/work/project/results_partB.csv --metric worst_miss_m --out ~/work/project/fig.png`

**Paper idea:** *A ground-robot patrol with drone call-out for building security: ROS 2 Nav2 and PX4 in simulation.*
Figures: the patrol in Gazebo + RViz; the alarm log; the drone's route over the town; an evidence photo; miss distance
against speed.
