# P2 – Explore faster: frontier selection for autonomous mapping

**Question:** a robot with a 2-D LiDAR starts in an unknown building and must map it by itself. It always drives to a
*frontier* – the edge between what it knows and what it does not. Which frontier should it choose next, and how much
does that choice change the time, the distance driven and the quality of the map?

| | |
|---|---|
| Sensors → actuators | 2-D LiDAR (+ wheel odometry) → two drive motors, through the Nav2 navigation stack |
| Simulator | Gazebo + RViz; slam_toolbox builds the map, Nav2 drives |
| Container | `abdulmannan617/tc70045e-ros2:humble` – **no GPU needed**, your laptop is enough |
| Starts from | [Week 8](../../week08/README.md) – lab README, demo video `TC70045E_Week08_demo.mp4` on Blackboard |
| You change | numbers on the command line first; later one line of Python (the score) |

## What you will learn

Docker and the browser desktop · ROS 2 parameters and launch files · occupancy-grid maps, SLAM and Nav2 · what a
frontier is · how a single scoring rule changes a robot's behaviour · measuring coverage, time and map accuracy.

## 1. Start (every session)

On your laptop: `docker start tc70045e`, open <http://localhost:6080>, **Connect**, **Terminator**, `update-labs`.
Split the terminal into T1 and T2. Once:

```bash
mkdir -p ~/work/project ~/maps && cp ~/labs/projects/P2_frontier_exploration/results_template.csv ~/work/project/results.csv
cp ~/labs/solutions/week08/explorer.py ~/work/project/my_explorer.py
```

## 2. The baseline you reproduce (Assessment 1)

| `config` | T1 | T2 |
|---|---|---|
| `wander` | `ros2 launch ~/labs/week08/launch/explore.launch.py brain:=wander` | – (it runs 600 s) |
| `k=1 (solution)` | `ros2 launch ~/labs/week08/launch/explore.launch.py` | `python3 ~/labs/solutions/week08/explorer.py --ros-args -p use_sim_time:=true` |

T1 prints `explored … m^2   driven … m` every 30 s; the explorer prints one line per goal and at the end
`RESULT 16 goals, 325 s, 70.4 m driven, explored 75.9 m^2`. Then save and measure the map (T2):

```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/run1 --ros-args -p use_sim_time:=true
python3 ~/labs/week04/scripts/map_metrics.py ~/maps/run1.yaml          # room width and depth, scale error
```

**Course measurements (14–15 Oct 2026):** wander 68 – 74 m² after 600 s and never knows it is finished; the
solution knows 70 m² after about 150 s and finishes by itself after 313 – 345 s with 73 – 76 m² known; the room
measures within 0.15 m of the true 10 × 8 m.

**Known failure – record it, do not hide it:** in some runs the SLAM position jumps (the robot "thinks" it is a few
metres from where it is), after which every goal fails and the robot looks stuck. Count such runs in your results
(`notes`: "stuck"), and run again. How often it happens is itself a result.

## 3. Where to edit, and how

| To test… | Where | Change | What to think about |
|---|---|---|---|
| near vs big frontiers | T2 command | add `-p distance_weight:=0.0` (size only), `0.5`, `1.0` (solution), `2.0` | score = size − k × distance |
| ignoring small frontiers | T2 command | `-p min_size:=4`, `8` (default), `16` cells (1 cell = 5 cm) | noise vs missing corners |
| sensor range | T1 command | `lidar_range:=3.5` (default), `6.0`, `12.0` | a better sensor or a smarter brain? |
| giving up sooner | T2 command | `-p goal_timeout:=30.0` (default 60 s) | time wasted on unreachable goals |
| **a new scoring rule** (Assessment 2) | `~/work/project/my_explorer.py` | search for `score = size - self.k * d` and replace it, e.g. `score = size / (d + 0.5)` (big per metre), or add a penalty for turning round | this is your own contribution |

Run your copy with `python3 ~/work/project/my_explorer.py --ros-args -p use_sim_time:=true …`. To change the
score: open the file in VSCodium, Ctrl+F `score =`, change only the part after `=`, keep the line's leading spaces,
save. Ask Claude Code to explain `choose()` first – and check its explanation by running the code.

## 4. Experiments

* **Assessment 1 (Week 6):** the two baseline configurations, **2 runs each**, plus **one sweep of
  `distance_weight`** (three values, 1 run each).
* **Assessment 2 (Week 12):** **3 or more runs** per configuration; at least **two factors** (e.g. `distance_weight`
  and `lidar_range`), and **one scoring rule of your own** compared with the solution.

## 5. Results file and figures

Columns: `config, run, date, computer, time_to_70m2_s, finished_s, goals, goals_failed, driven_m, known_m2,
room_width_m, room_depth_m, stuck, notes`. `time_to_70m2_s`: read it from T1's 30-s lines (the first line at or
above 70 m²); leave it empty if never.

```bash
python3 ~/labs/projects/tools/plot_results.py ~/work/project/results.csv --metric finished_s \
    --ylabel "time until the explorer finished [s]" --out ~/work/project/fig_time.png
```

## 6. Your paper (Assessment 2)

* **Possible title:** *Distance-weighted frontier selection for LiDAR-based autonomous exploration: a simulation
  study of time, path length and map accuracy.*
* **Contribution:** the measured trade-off between "near" and "big", the effect of sensor range, and your own score
  compared with the course solution – with the failure rate reported.
* **Figures:** RViz map at the end; time-to-70 m² per configuration; coverage against time for two configurations
  (from T1's 30-s lines, typed into a small CSV with columns `t,known_m2`).
* **Limits:** one 80 m² floor plan, simulated LiDAR, run-to-run randomness.
