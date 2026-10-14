# Week 08 – Autonomous Exploration: the Robot Maps an Unknown Building by Itself

In Week 2 the robot mapped the lab while you drove it – or while a "wander" brick drove it at random. In Week 3 it
drove itself, but only on a map that was already there. This week you join the two: the robot starts with **no
map**, decides **where to go next**, sends that goal to Nav2, and keeps going until nothing unknown is left. The
places it decides between are **frontiers** – the edges of what it knows.

**Watch the demo video first:** `TC70045E_Week08_demo.mp4` in the Week 8 folder on Blackboard. It shows every step
below, with Gazebo (the simulated world) and RViz (what the robot knows) side by side.

| Time in class | Part |
|---|---|
| 45 min | lecture: exploration, frontiers, choosing a goal, Nav2 on a growing map |
| 10 min | Step 0 – start the container |
| 65 min | Activities A1–A3 |
| 60 min | Your activity (the TODO) – finish `explorer.py` |

---

## Step 0 – Start the container (once per session)

Exactly as in Week 2 ([week02/README.md](../week02/README.md#step-0--start-the-container-once-per-session)):
`docker start tc70045e`, open <http://localhost:6080>, **Connect**, open **Terminator** and run `update-labs`.
Split Terminator into three terminals (T1, T2, T3).
Check: `ls ~/labs/week08` lists `launch  reactive_lidar  README.md  rviz  scripts  slam_navigation_extra`.

**Before every new launch:** Ctrl+C in T1 and wait for the `$` prompt. If the launch then dies with
"process has died … gzserver", run `pkill -f gzserver`, wait 5 s, launch again.

## The bricks this week

| Brick / file | What it does |
|---|---|
| [`launch/explore.launch.py`](launch/explore.launch.py) | robot + slam_toolbox (from an empty map) + RViz + `coverage.py`; Nav2 for a planning brain. `brain:=wander` adds the Week 2 wander + safety bricks instead. Also `time_limit`, `gui`, `rviz` |
| [`scripts/explorer.py`](scripts/explorer.py) | **your brain**: map → frontiers → choose one → Nav2 goal → repeat. Three TODOs |
| [`scripts/coverage.py`](scripts/coverage.py) | prints the explored area (m² of the map that is free or occupied) and the distance driven every 30 s, and a RESULT line at the time limit |
| `../week04/scripts/map_metrics.py` | room size and scale error of a saved map |

The lab is about 80 m² inside its walls; with the wall cells a complete map is about 74 – 85 m².

---

## A1 – The baseline: wander for 10 minutes (25 min)

**Goal:** measure how far luck gets you – the number your explorer has to beat.

| | |
|---|---|
| T1 | `ros2 launch ~/labs/week08/launch/explore.launch.py brain:=wander` |
| T2 (when T1 prints the RESULT line, after 600 s) | `ros2 run nav2_map_server map_saver_cli -f ~/maps/w8_wander --ros-args -p use_sim_time:=true` |
| T2 | `python3 ~/labs/week04/scripts/map_metrics.py ~/maps/w8_wander.yaml` |

`brain:=wander` is exactly the Week 2 wander + safety bricks; `coverage.py` prints the explored area and the distance
driven every 30 s. The laser is limited to 3.5 m (`lidar_range:=3.5`), so the robot has to drive to see the lab.

**You should see:** the map grows fast at first, then slowly: the last corners are found by chance. Measured (two
runs): 68.4 – 74.3 m² known after 600 s, 42 – 127 m driven; one run reached 70 m² after 270 s, the other never did
(it got stuck after 240 s). **Check:** the robot is still driving at 600 s. Does it know the map is finished?

## A2 – See the frontiers: the explorer as given (17 min)

**Goal:** see the explorer's loop run – and why it needs TODO 1.

| | |
|---|---|
| T1 | Ctrl+C, then `ros2 launch ~/labs/week08/launch/explore.launch.py` (no brain: Nav2 starts and waits) |
| T2 | `python3 ~/labs/week08/scripts/explorer.py --ros-args -p use_sim_time:=true` |

**You should see:** `map and robot position received - exploring`, then at once `no frontier left: exploration
complete` – measured: 0 goals, 0 m driven, 12.3 m² known. As given, no cell counts as a frontier. **Check:** in RViz,
point at the places where white (free) touches grey (unknown). Those are the frontiers it should have found.

## A3 – One goal into the unknown, by hand (15 min)

**Goal:** see that Nav2 can plan into space it has not mapped yet – what the explorer relies on.

| | |
|---|---|
| T1 | keep running from A2 |
| RViz | **Nav2 Goal** tool: click on a grey (unknown) area just past a frontier, drag to set the heading |

**You should see:** Nav2 plans a path through the unknown area (`allow_unknown: true`) and drives; the laser turns grey
cells white or black as the robot goes, and the frontier moves on. **Check:** what happens if you pick a goal behind a
wall?

---

## Your activity (the TODO) – finish explorer.py (60 min)

**What you build:** a brain that finds frontiers, chooses one, remembers what it tried – and knows when it is finished.

1. **Copy the script:** `cp ~/labs/week08/scripts/explorer.py ~/labs/week08/scripts/my_explorer.py`
2. **Open your copy.** As given it finds no frontier at all (A2). Three TODOs:
   * **TODO 1 – `frontiers()`:** a frontier cell is **free** and has an **unknown** neighbour (up, down, left or
     right). Build `near_unknown` by shifting `unknown` one cell in each direction, then `frontier = free & near_unknown`
     – one test on the whole map at once, no loops.
   * **TODO 2 – `choose()`:** as given the score is the frontier's size only. Make it **big and near**:
     `score = size - k * d`, with `k = distance_weight` (`self.k`).
   * **TODO 3 – `choose()`:** skip a frontier within 0.5 m of a goal already tried (`self.tried`). Without it the robot
     is sent to the same frontier again and again – one behind something the laser cannot see past.
3. **Run it** (T1: `ros2 launch ~/labs/week08/launch/explore.launch.py`), T2:
   `python3 ~/labs/week08/scripts/my_explorer.py --ros-args -p use_sim_time:=true -p distance_weight:=0.0`,
   then again with `distance_weight:=1.0`. Save and score each map as in A1.
4. **Done when** – all three are true:
   * T2 prints `no frontier left: exploration complete` before the 600 s time limit;
   * your map is saved and scored with `map_metrics.py`;
   * you have a table: wander / k = 0 / k = 1 × (time to 70 m², finished after, distance driven, known area, scale
     error).

**Extension:** run your explorer with `lidar_range:=12.0` on the launch line. How much does exploration still matter?

### Solution (compare after you have tried)

[`../solutions/week08/explorer.py`](../solutions/week08/explorer.py): `near_unknown` = `unknown` shifted up, down,
left and right (OR), `frontier = free & near_unknown`; `score = size - self.k * d`;
`if any(math.hypot(x - fx, y - fy) < 0.5 for fx, fy in self.tried): continue`.

Measured 14 Oct 2026 (simulated, laser 3.5 m unless stated; time from the launch):

| Brain | 70 m² known after | finished by itself | driven | known at the end | room (true 10 × 8 m) |
|---|---|---|---|---|---|
| wander (A1), run 1 | 270 s | never | 127.4 m | 74.3 m² | 10.05 × 8.05 m |
| wander (A1), run 2 | never (stuck after 240 s) | never | 42.4 m | 68.4 m² | 10.00 × 8.00 m |
| explorer as given (A2) | never | at once, 0 goals | 0 m | 12.3 m² | – |
| k = 0 – size only | 480 s | 533 s, 23 goals (13 failed) | 46.2 m | 71.0 m² | 10.25 × 8.35 m |
| **k = 1 – solution**, run 1 | **150 s** | **325 s**, 16 goals (1 failed) | 70.4 m | 75.9 m² | 10.05 × 8.05 m |
| **k = 1 – solution**, run 2 | **150 s** | **313 s**, 19 goals (8 failed) | 24.7 m | 73.1 m² | 10.15 × 8.09 m |
| solution, laser 12 m | 90 s | 320 s, 13 goals (4 failed) | 47.2 m | 73.9 m² | – |

What the numbers say:
* **A plan beats luck.** The solution knew 70 m² of the lab after 150 s in both runs and then stopped by itself; wander
  took 270 s in one run, never got there in the other, and kept driving to the end.
* **Distance matters.** With k = 0 the robot crossed the lab for the biggest frontier: more goals, more of them
  failed, three times as long to 70 m² – and a less accurate map (scale error +2.5 % and +4.4 %, against +0.5 % and
  +0.6 %).
* **Sensor range shapes the job.** With the full 12 m laser the robot knew 70 m² after 90 s: in a room smaller than
  the sensor's range there is little to explore. A building larger than the range is where exploration pays.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `explorer.py` waits at the start | it waits for slam_toolbox's first map and the robot's position on it – up to a minute on a slow computer |
| The robot does not move, T2 prints `REACHED` again and again for the same goal | TODO 3: the frontier stays a frontier (unknown space behind a wall the laser cannot see past) |
| `no frontier left` straight away | TODO 1: no cell counts as a frontier yet |
| The robot drives back and forth across the lab | TODO 2: the choice ignores the distance (k too small) |
| Launch dies: "process has died … gzserver" | `pkill -f gzserver`, wait 5 s, launch again |

Optional extras from the previous course, in this folder: [`reactive_lidar/`](reactive_lidar/) (reactive avoid /
follow / guard behaviours and a measured stopping test) and [`slam_navigation_extra/`](slam_navigation_extra/)
(slam_toolbox against Cartographer, scored; five-run navigation repeatability).
