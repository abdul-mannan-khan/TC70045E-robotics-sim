# P1 – Mobile robot: an autonomous night-security patrol robot

**The job:** after closing time a mobile robot patrols a two-room building on its own. It drives a round of
checkpoints you choose, reports each one as checked or blocked, keeps going when someone has left an obstacle in the
way, and comes back to its start. You build the patrol, make it robust, and measure how reliable it is.

| | |
|---|---|
| Robot | the course's mobile robot: 2-D LiDAR, wheel odometry, IMU, two drive motors |
| Simulator | Gazebo (the building) + RViz (the map and the plan), ROS 2 Nav2 navigation |
| Container | `abdulmannan617/tc70045e-ros2:humble` – **no GPU needed**, your laptop is enough |
| Starts from | [Week 3](../../week03/README.md) – demo video `TC70045E_Week03_demo.mp4` on Blackboard |
| You change | the checkpoint list (clicked in RViz), a few numbers, obstacles you drop into the building |

**What you will be able to show at the end:** the robot patrolling both rooms by itself in Gazebo, a box dropped in
its way, the robot driving round it – or reporting the checkpoint blocked and carrying on – and a table of how reliable
your patrol is.

## What you will learn

Docker and the browser desktop · ROS 2 topics, parameters and launch files · maps, localisation (AMCL), path planning
and costmaps in Nav2 · how a robot avoids obstacles it did not know about · measuring reliability over repeated runs.

## 1. Start (every session)

On your laptop (Week 0 guide, [docs/GETTING_STARTED.md](../../docs/GETTING_STARTED.md)): `docker start tc70045e`,
open <http://localhost:6080>, **Connect**, open **Terminator**, run `update-labs`, split it into T1, T2, T3. Once:

```bash
mkdir -p ~/work/project && cp ~/labs/projects/P1_security_patrol_robot/results_template.csv ~/work/project/results.csv
cp ~/labs/solutions/week03/patrol.py ~/work/project/my_patrol.py
```

T1 every time: `ros2 launch ~/labs/week03/launch/nav.launch.py gui:=true` – wait until it prints
`AMCL confirmed the start pose` (about 15 s).

## 2. The baseline you reproduce (Assessment 1)

T2: `python3 ~/labs/solutions/week03/patrol.py 1` (one lap). One line per checkpoint, then e.g.
`RESULT 5 of 5 waypoints reached, total 93 s, mean 18.5 s per waypoint`.

**Course measurements (7 Oct 2026):** 5 of 5 checkpoints reached in three cold starts, 91–95 s per lap, about 18.5 s
per checkpoint. Drive past a box: `python3 ~/labs/week03/scripts/drop_box.py 2.0 -1.0` in T3 while the robot heads for
the doorway – Nav2 drove round it (about 14.5 s to the doorway). `drop_box.py --remove` takes it away.

## 3. Where to edit, and how

Open `~/work/project/my_patrol.py` in VSCodium (or `nano`) and press Ctrl+F for the text in the second column.
Run your copy with `python3 ~/work/project/my_patrol.py 2` (the number is the laps).

| To build or test… | Search for / where | Change | What to look at |
|---|---|---|---|
| **your own patrol round** | `WAYPOINTS = [` | replace the five lines with your checkpoints: `('name', x, y, heading_deg),` – find x, y with RViz **Publish Point** and `ros2 topic echo /clicked_point` in T3. Keep 0.5 m from walls | each checkpoint REACHED? time per checkpoint |
| more laps | the run command | `… my_patrol.py 3` | does it stay reliable lap after lap? |
| giving up on a blocked checkpoint | `TIME_LIMIT = 90.0` | `30`, `60`, `90` s | time wasted against checkpoints wrongly given up |
| **an intruder's obstacle** | T3 while patrolling | `python3 ~/labs/week03/scripts/drop_box.py X Y` on your route, or on a checkpoint | drive round, or FAILED and carry on? |
| keeping clear of furniture and people | T3, after the launch | `ros2 param set /global_costmap/global_costmap inflation_layer.inflation_radius 0.15` (default 0.35; try 0.15, 0.35, 0.8) | the path's shape, the time, near misses |

Python rules: each checkpoint line ends with a comma, the name stays in quotes, keep the spaces at the start of the
line. If it stops working, compare with `~/labs/solutions/week03/patrol.py`.

**Assessment 2 – your own feature (choose one, or agree another with the module leader):**
* an **alarm log**: write every FAILED checkpoint with the time into a file `~/work/project/alarms.csv`;
* a **second chance**: when a checkpoint fails, try it once more at the end of the lap;
* a **random patrol**: visit the checkpoints in a different order every lap (`import random`, `random.shuffle(...)`),
  so an intruder cannot predict the robot.

Ask Claude Code to explain `visit()` and the lap loop first, then to show you the smallest change for your feature –
and test it with a blocked checkpoint.

## 4. Experiments

* **Assessment 1 (Week 6):** the course patrol, **3 runs**; **your own round** of at least five checkpoints in both
  rooms, **2 laps × 2 runs**; one blocked-checkpoint test.
* **Assessment 2 (Week 12):** **3 runs** per configuration; at least **two factors** (e.g. inflation radius and
  `TIME_LIMIT`, or obstacles in 0 / 1 / 2 places) and **your own feature** compared with the course patrol.

## 5. Results file and figures

Columns: `config, run, date, computer, laps, checkpoints, reached, failed, total_s, mean_s_per_checkpoint,
inflation_m, time_limit_s, obstacles, notes`.

```bash
python3 ~/labs/projects/tools/plot_results.py ~/work/project/results.csv --metric mean_s_per_checkpoint \
    --ylabel "time per checkpoint [s]" --out ~/work/project/fig_time.png
```

## 6. Your paper (Assessment 2)

* **Possible title:** *An autonomous security-patrol robot with ROS 2 Nav2: reliability with unexpected obstacles.*
* **Story:** the job, your patrol and your feature, how often it succeeds, what blocks it, what you would need before
  it patrols a real building.
* **Figures:** Gazebo + RViz screenshot with your checkpoints and the planned path; time per checkpoint for each
  configuration; a map with the dropped obstacles marked.
* **Limits:** one simulated building, no people moving, a perfect map.
