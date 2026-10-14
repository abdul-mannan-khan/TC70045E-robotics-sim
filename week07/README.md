# Week 07 – D455 RGB-D SLAM and Navigation: Map with the Camera Alone, then Navigate

In Week 4 the D455 helped the LiDAR: the laser corrected the robot's position, the camera drew the map. This week the
LiDAR is switched **off**. RTAB-Map builds the map and keeps track of the robot with the camera alone – matching
features between images – and then Nav2 drives on that map, with the depth camera as its only obstacle sensor.
Many cheap robots, drones and phones have a camera but no LiDAR. You will **measure** what that costs.

**Watch the demo video first:** `TC70045E_Week07_demo.mp4` in the Week 7 folder on Blackboard. It shows every step
below, with Gazebo (the simulated world) and RViz (what the robot knows) side by side.

| Time in class | Part |
|---|---|
| 45 min | lecture: visual registration, loop closure, localisation mode, Nav2 with a depth camera |
| 10 min | Step 0 – start the container |
| 70 min | Activities A1–A3 |
| 55 min | Your activity (the TODO) – camera-only SLAM, then three goals |

---

## Step 0 – Start the container (once per session)

Exactly as in Week 2 ([week02/README.md](../week02/README.md#step-0--start-the-container-once-per-session)):
`docker start tc70045e`, open <http://localhost:6080>, **Connect**, open **Terminator** and run `update-labs`.
Split Terminator into three terminals (T1, T2, T3).
Check: `ls ~/labs/week07` lists `config  launch  README.md  rviz  scripts  visual_slam_extra`.

**Before every new launch:** Ctrl+C in T1 and wait for the `$` prompt. If the launch then dies with
"process has died … gzserver", run `pkill -f gzserver`, wait 5 s, launch again.

## The bricks this week

| Brick / file | What it does |
|---|---|
| [`launch/rgbd_nav.launch.py`](launch/rgbd_nav.launch.py) | robot + D455 + RTAB-Map, in `mode:=mapping` or `mode:=localization`; `nav:=true` adds Nav2; `drive:=true` drives the Week 4 circuit. Also `config:=`, `database:=`, `gui`, `rviz` |
| [`config/rtabmap_camera.yaml`](config/rtabmap_camera.yaml) | RTAB-Map settings. **Your activity** has three TODOs in this file |
| [`config/nav2_params.yaml`](config/nav2_params.yaml) | Week 3's Nav2 settings, with the obstacle layers fed by the D455 point cloud instead of the LiDAR |
| [`scripts/three_goals.py`](scripts/three_goals.py) | sends three Nav2 goals on the camera map and prints, for each, the result, the time and how far from the goal the robot **really** stopped |
| `../week04/scripts/drive_loop.py`, `map_check.py`, `map_metrics.py` | the Week 4 circuit and the map scores, unchanged |

The map is kept in an RTAB-Map **database**, `~/maps/w7_camera.db`: `mode:=mapping` starts a new one, and
`mode:=localization` loads it and only localises.

---

## A1 – A map from the camera alone (30 min)

**Goal:** see camera-only SLAM work – and see what it costs.

| | |
|---|---|
| T1 | `ros2 launch ~/labs/week07/launch/rgbd_nav.launch.py mode:=mapping drive:=true config:=$HOME/labs/solutions/week07/rtabmap_camera.yaml` |
| T2 (when T1 prints `loop finished`) | `ros2 run nav2_map_server map_saver_cli -f ~/maps/w7_camera --ros-args -p use_sim_time:=true` |
| T2 | `python3 ~/labs/week04/scripts/map_check.py ~/maps/w7_camera.yaml` and `python3 ~/labs/week04/scripts/map_metrics.py ~/maps/w7_camera.yaml` |

This uses the **solution** settings, so you see the goal first; in your activity you build them yourself.
`drive:=true` drives the Week 4 circuit (24 m, 210 s) and prints the SLAM error against the truth. The database is
saved as `~/maps/w7_camera.db` – you need it in A2.

**You should see:** RViz draws the map from the coloured depth points; there is no red laser. Walls appear a little
thick and wavy. At the end, e.g. `error at the end [m]   SLAM 0.007` – the loop closure at the start pulls the
graph straight – but `RMS error  SLAM 0.369`: during the drive the robot was up to about half a metre off.
Measured (two runs): room 10.25 – 10.43 × 8.35 – 8.54 m (true 10 × 8), 217 – 527 phantom cells, the low step and the
table top **SEEN**. **Check:** compare with your Week 4 table (LiDAR + D455: RMS 4 cm, 23 – 42 phantom cells).

## A2 – Localise in the camera map (20 min)

**Goal:** use the saved map: RTAB-Map recognises where the robot is from what the camera sees.

| | |
|---|---|
| T1 | Ctrl+C, then `ros2 launch ~/labs/week07/launch/rgbd_nav.launch.py mode:=localization config:=$HOME/labs/solutions/week07/rtabmap_camera.yaml` |
| T2 | `ros2 run tf2_ros tf2_echo map odom` |
| T3 | `ros2 run teleop_twist_keyboard teleop_twist_keyboard` – if nothing happens after a minute, turn slowly on the spot (`j`) |

**You should see:** the saved map in RViz. At first T2 says the frame `map` does not exist: the robot does not know
where it is yet. As soon as the camera **recognises** a stored place, RTAB-Map publishes `map → odom` and T2 prints a
translation and rotation – the robot is on the map. (On a slow laptop the camera and RTAB-Map can need a minute
before the first image is processed.) **Check:** what does the robot need to see for that to happen? (Something it
saw while mapping, from a similar direction.)

## A3 – Nav2 on the camera map (20 min)

**Goal:** navigate with the camera only: the map from RTAB-Map, the obstacles from the depth point cloud.

| | |
|---|---|
| T1 | Ctrl+C, then `ros2 launch ~/labs/week07/launch/rgbd_nav.launch.py mode:=localization nav:=true config:=$HOME/labs/solutions/week07/rtabmap_camera.yaml` |
| T2 | (after about 45 s) `python3 ~/labs/week07/scripts/three_goals.py` |

**You should see:** the robot drives to three goals; T2 prints, for each, the result, the time and how far from the
goal the robot really stopped. Measured on five camera-only maps: 3 of 3 goals reached four times (stopping
0.13 – 0.51 m from the goal), and 2 of 3 once (the goal by the crate failed on a map with 1258 phantom cells). **Check:** the local costmap in
RViz only fills in front of the robot. Why?

---

## Your activity (the TODO) – camera-only SLAM, then three goals (55 min)

**What you build:** your own camera-only RTAB-Map settings, a map, and three goals on it.

1. **Copy the settings:** `cp ~/labs/week07/config/rtabmap_camera.yaml ~/labs/week07/config/my_camera.yaml`
2. **Open your copy.** As given it is the Week 4 solution – the LiDAR still corrects the pose. Three TODOs:
   * **TODO 1 – `subscribe_scan`:** camera only – no LiDAR.
   * **TODO 2 – `Reg/Strategy`:** with no scan, ICP (`"1"`) has nothing to match. Which value registers two places by
     their **images**?
   * **TODO 3 – `Vis/MinInliers` and `RGBD/OptimizeMaxError`:** how strict is a loop closure? Fewer matched features
     and a looser error test give more loop closures – including **wrong** ones, which bend the whole map.
     Map with the given values (10 and 3.0) and with stricter ones, and compare.
3. **Map, save, score** (as in A1, with `config:=$HOME/labs/week07/config/my_camera.yaml` and
   `database:=$HOME/maps/w7_mine.db`), then **navigate** (as in A3, with the same `config:=` and `database:=`).
4. **Done when** – all three are true:
   * your map shows the low step and the table top (`map_check.py`: **SEEN**) and no laser was used;
   * `three_goals.py` reaches at least 2 of the 3 goals on your map;
   * you have a table: as given (LiDAR) / TODO 1 + 2 / all three × (SLAM RMS error, phantom cells, room size, goals
     reached).

### Solution (compare after you have tried)

[`../solutions/week07/rtabmap_camera.yaml`](../solutions/week07/rtabmap_camera.yaml): `subscribe_scan: false`,
`Reg/Strategy: "0"`, `Vis/MinInliers: "20"`, `RGBD/OptimizeMaxError: "1.0"` (and `RGBD/ProximityBySpace: "false"`).

Measured 14 Oct 2026 (simulated, Week 4 circuit, one run each unless stated):

| Settings | SLAM error at the end | SLAM RMS during the drive | phantom cells | room (true 10 × 8 m) | low step / table top |
|---|---|---|---|---|---|
| as given – LiDAR still on | 0.1 cm | 1.9 cm | 21 | 10.20 × 8.20 m | SEEN / SEEN |
| TODO 1 + 2 – camera only, loose loop closures (10, 3.0) | 0.3 cm | 47 cm | 649 | 10.55 × 8.35 m | SEEN / SEEN |
| **all three – camera only, strict (20, 1.0)**, six runs | 0.3 – 3.1 cm | 30 – 64 cm (five runs) | 217 – 1258 | 10.25 – 10.64 × 8.35 – 8.56 m | SEEN / SEEN |
| camera only, earlier settings (15 inliers, proximity links on), one of four runs | **5.8 m** | 4.1 m | 3577 | 10.96 × **13.28** m | MISSED / MISSED |

Nav2 with three goals on five of the solution maps: 3 of 3 four times and 2 of 3 once (14 of 15 goals).

What the numbers say:
* **The camera can replace the LiDAR – at a price.** The loop closure at the end makes the final error tiny, but during
  the drive the robot was 30 – 64 cm off (RMS; LiDAR: 2 cm) – and how much varies from run to run: the walls are drawn twice, slightly apart, which makes the
  room look 3 – 7 % too big and leaves hundreds of phantom cells.
* **One wrong loop closure ruins a map.** With loose settings one run matched two different places and drew the room
  13 m deep instead of 8 m. The strict settings did not do that in our runs – but they did not make the error during
  the drive reliably smaller either (30 – 64 cm against 47 cm): they guard against disasters, they cannot make plain
  walls more recognisable.
* **Navigation still works, mostly:** 14 of 15 goals reached on five camera maps. The one that failed was the goal next to
  the crate, on the noisiest map (1258 phantom cells) – the robot stopped 2 m short.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| RViz: "No map received" | RTAB-Map publishes the map after the robot has moved 0.1 m; in localisation mode after it has recognised a place – drive a little with teleop |
| T1 repeats `Did not receive data since 5 seconds` | the camera is slow to start (up to 30 s on a laptop): `ros2 topic hz /rgbd_image` |
| In localisation mode the robot is not on the map (`tf2_echo map odom`: frame does not exist) | RTAB-Map has not recognised a place yet: wait a minute, then turn the robot slowly on the spot (teleop `j` / `l`) |
| Nav2 goal fails at once: "start occupied" | the robot was drawn into an obstacle on a poor map – clear the costmaps (`ros2 service call /global_costmap/clear_entirely_global_costmap nav2_msgs/srv/ClearEntireCostmap`) and send it again |
| Launch dies: "process has died … gzserver" | `pkill -f gzserver`, wait 5 s, launch again |

Optional extra from the previous course, in this folder: [`visual_slam_extra/`](visual_slam_extra/) (ORB features,
RTAB-Map statistics, point-cloud filtering).
