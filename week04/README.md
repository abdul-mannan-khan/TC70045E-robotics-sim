# Week 04 – Add a Sensor, Upgrade the SLAM: LiDAR + D455 Camera

In Week 2 the robot built a map with **one** sensor, a 2D LiDAR, and **slam_toolbox**. A 2D LiDAR sees one thin
horizontal slice of the world, about 14 cm above the floor. Anything below that slice (a step, a cable, a pallet) or
above it (a table top) is not in the map – and Nav2 (Week 3) will happily drive into it.

This week you add a second sensor, the **Intel RealSense D455** depth camera (simulated, same topics as the real
driver), and swap slam_toolbox for **RTAB-Map**, a SLAM system that can use the LiDAR *and* the camera. Then you
**measure** whether the map got better: same robot, same route, three maps, scored against the true world.

**Watch the demo video first:** `TC70045E_Week04_demo.mp4` in the Week 4 folder on Blackboard. It shows every step
below, with Gazebo (the simulated world) and RViz (what the robot knows) side by side.

| Time in class | Part |
|---|---|
| 45 min | lecture: how a stereo depth camera measures depth, the D455, how RTAB-Map uses two sensors |
| 10 min | Step 0 – start the container |
| 90 min | Activities A1–A4 |
| 35 min | Your activity (the TODO) – add the D455 to RTAB-Map and score the maps |

---

## Step 0 – Start the container (once per session)

Exactly as in Week 2 ([week02/README.md](../week02/README.md#step-0--start-the-container-once-per-session)):
start `abdulmannan617/tc70045e-ros2:humble` (own computer, Vast.ai or `docker compose up -d ros2`), open
<http://localhost:6080>, password `ubuntu`, open **Terminator** and split it into three terminals (T1, T2, T3).
Check: `ls ~/labs/week04` lists `config  inertial_sensing  launch  README.md  rviz  scripts`.
Make a folder for your maps once: `mkdir -p ~/maps`.

**Before every new launch:** Ctrl+C in T1 and wait for the `$` prompt. If the launch then dies with
"process has died … gzserver", run `pkill -f gzserver`, wait 5 s, launch again.

## The bricks this week

| Brick / file | What it does |
|---|---|
| [`launch/slam.launch.py`](launch/slam.launch.py) | robot in Gazebo + D455 camera + one SLAM brick + RViz. Switches: `slam:=toolbox` or `slam:=rtabmap`, `config:=…`, `drive`, `camera`, `gui`, `rviz` |
| [`config/rtabmap.yaml`](config/rtabmap.yaml) | RTAB-Map settings. As given: **LiDAR only**. **Your activity** has three TODOs in this file |
| [`rviz/slam.rviz`](rviz/slam.rviz) | map, laser (red), D455 depth cloud (coloured points), D455 colour image, robot |
| [`scripts/drive_loop.py`](scripts/drive_loop.py) | drives the same 24 m circuit every time (both rooms, round the crate and the pillar) and prints the SLAM position error against the truth |
| [`scripts/map_check.py`](scripts/map_check.py) | scores a saved map against the true world: which objects are in the map, which are missing, how many phantom obstacles |
| [`scripts/map_metrics.py`](scripts/map_metrics.py) | room size and scale error of a saved map (from Week 9 of the old course) |

The camera is the robot's D455 brick: `/camera/color/image_raw` and `/camera/aligned_depth_to_color/image_raw`,
424 × 240 pixels (half the real D455's 848 × 480, so it runs on a laptop), depth noise modelled like a real stereo
camera (it grows with distance squared).

Two objects in the lab are there to test the sensors (look at them in Gazebo):

| Object | Where (map frame) | Height | Can the LiDAR see it? |
|---|---|---|---|
| yellow **low step** | (2.4, 3.0) | 0 – 8 cm | no – it is under the laser slice |
| wooden **table** | (6.0, -1.6) | top at 73 – 77 cm, four thin legs | only the four legs |

---

## A1 – Look at the new sensor (15 min)

**Goal:** see what the D455 measures and how it differs from the LiDAR.

| | |
|---|---|
| T1 | `ros2 launch ~/labs/week04/launch/slam.launch.py slam:=toolbox` |
| T2 | `ros2 topic hz /camera/aligned_depth_to_color/image_raw` (Ctrl+C after 10 s) |
| T2 | `ros2 topic echo --once /camera/color/camera_info --field k` |

**You should see:** Gazebo and RViz. In RViz the red laser points are one flat ring; the coloured **depth cloud** is a
3D surface in front of the robot – walls, floor, the side of furniture. The colour image is in the bottom-left panel.
T2 prints the depth rate (measured: about 4 Hz on a 1-core cloud instance that renders without a GPU;
faster on a laptop) and the camera matrix `k`: the focal length fx = k[0] (measured: 223.4 px).
**Check:** drive the robot (T3: `ros2 run teleop_twist_keyboard teleop_twist_keyboard`) until the yellow low step is
in front of it. The depth cloud shows the step; the laser does not. Now look at a wall 1 m away and 4 m away: the
depth points on the far wall are visibly noisier – that is the stereo error σ_Z ∝ Z² from the lecture.

## A2 – Week 2 again: a LiDAR-only map with slam_toolbox (20 min)

**Goal:** a baseline map to compare with.

| | |
|---|---|
| T1 | Ctrl+C, then `ros2 launch ~/labs/week04/launch/slam.launch.py slam:=toolbox drive:=true` |
| T2 (when T1 prints `loop finished`) | `ros2 run nav2_map_server map_saver_cli -f ~/maps/w4_toolbox --ros-args -p use_sim_time:=true` |
| T2 | `python3 ~/labs/week04/scripts/map_check.py ~/maps/w4_toolbox.yaml` |

`drive:=true` starts `drive_loop.py` 20 s after the launch: the robot drives the same 24 m circuit every time
(210 s) and then prints its score. **Do not drive the robot yourself** while it runs.

**You should see:** in T1 at the end, e.g. `error at the end [m]   SLAM 0.025   odometry 1.317` – SLAM is far
better than wheel odometry alone. `map_check.py` prints one line per object; the **low step** and the **table top**
are `MISSED` (measured: 0 % and 5 % of their outline), while the table's thin legs are `SEEN`. Everything the laser
slice cuts is `SEEN`, and there are 0 phantom cells.

## A3 – RTAB-Map with the LiDAR only (20 min)

**Goal:** a second SLAM system, same sensor – so you can see what changes when you add the camera in your activity.

| | |
|---|---|
| T1 | Ctrl+C, then `ros2 launch ~/labs/week04/launch/slam.launch.py slam:=rtabmap drive:=true` |
| T2 (after `loop finished`) | `ros2 run nav2_map_server map_saver_cli -f ~/maps/w4_lidar --ros-args -p use_sim_time:=true` |
| T2 | `python3 ~/labs/week04/scripts/map_check.py ~/maps/w4_toolbox.yaml ~/maps/w4_lidar.yaml` |

Open [`config/rtabmap.yaml`](config/rtabmap.yaml) while it drives and read the comments: RTAB-Map takes wheel odometry
(`/odom_raw`), corrects it with the laser scan (ICP, `Reg/Strategy 1`), and adds a **node** to its graph every 0.1 m.

**You should see:** a map very like slam_toolbox's, and the same two `MISSED` objects – the *algorithm* changed, the
*sensor* did not. Measured: end error 0.010 m, RMS 0.046 m during the loop; room 10.00 × 8.05 m (true 10 × 8).

## A4 – Read the RTAB-Map graph (15 min)

**Goal:** see what a graph-based SLAM stores. With A3 still running (or launched again):

| | |
|---|---|
| T2 | `ros2 topic echo --once /rtabmap/info --field loop_closure_id` |
| T2 | `ros2 topic list \| grep rtabmap` |

RTAB-Map keeps a graph: one node per place (pose + scan, and with the camera also an image), linked by odometry and
by **loop closures** – "I have been here before". `loop_closure_id` is 0 while no loop closes. With the LiDAR only,
RTAB-Map can close loops by *proximity* (scan matching near a known place); with the camera it can also *recognise*
a place from its picture (visual words), even after a long drift.

---

## Your activity (the TODO) – add the D455 to RTAB-Map and prove it helps (35 min)

**What you build:** an RTAB-Map configuration that uses the LiDAR **and** the D455, a third map, and a comparison
table that shows – with numbers – what the camera added and what it cost.

1. **Copy the settings** (keep the original): `cp ~/labs/week04/config/rtabmap.yaml ~/labs/week04/config/my_rtabmap.yaml`
2. **Open your copy** in VSCodium (desktop icon) or `nano ~/labs/week04/config/my_rtabmap.yaml`. Three TODOs:
   * **TODO 1 – `subscribe_rgbd`:** `true` – RTAB-Map receives the D455 colour image (for visual loop closures)
     and its depth image (for 3D obstacles). The launch file's `rgbd_sync` brick pairs each colour image with the
     depth image taken at the same moment and publishes the pair on `/rgbd_image`.
   * **TODO 2 – `Grid/Sensor`:** which sensor draws the map: `"0"` LiDAR, `"1"` depth camera, `"2"` both. Choose,
     run, score – and if the step is still `MISSED`, think about what the LiDAR beam does as it passes *over* the
     step: it reports "nothing here" for those cells several times a second. Try the other value. (The LiDAR keeps
     correcting the robot's pose whichever value you choose – `Reg/Strategy 1` uses the scan.)
   * **TODO 3 – `Grid/MaxGroundHeight`:** the depth camera sees the **floor** too. Points lower than this height are
     treated as floor, higher ones as obstacles. `"0.0"` switches the test off. The step is 8 cm high and the
     depth noise at 2 m is about 1.5 cm – pick a value (the comment suggests one) and be ready to justify it.
3. **Run it:**
   `ros2 launch ~/labs/week04/launch/slam.launch.py slam:=rtabmap drive:=true config:=$HOME/labs/week04/config/my_rtabmap.yaml`
   – then save the map as `~/maps/w4_lidar_d455` (as in A3).
4. **Score all three maps:**
   `python3 ~/labs/week04/scripts/map_check.py ~/maps/w4_toolbox.yaml ~/maps/w4_lidar.yaml ~/maps/w4_lidar_d455.yaml`
   and for each map `python3 ~/labs/week04/scripts/map_metrics.py ~/maps/<name>.yaml`.
5. **Done when** – all four are true:
   * RViz shows the low step and the table top as black (occupied) cells in the map;
   * `map_check.py` reports `low_step` and `table_top` as `SEEN` in your map and `MISSED` in the two LiDAR-only maps;
   * your map has fewer than about 50 phantom cells (if you have hundreds or thousands, TODO 3 is wrong – the floor
     became an obstacle. Try it on purpose with `"0.0"` and look at RViz);
   * you have a table: three maps × (end error, low step, table top, phantom cells, room size, CPU of the SLAM node –
     `top` in T3, line `rtabmap` or `async_slam_tool`).

### Solution (compare after you have tried)

[`../solutions/week04/rtabmap.yaml`](../solutions/week04/rtabmap.yaml) – run it with
`ros2 launch ~/labs/week04/launch/slam.launch.py slam:=rtabmap drive:=true config:=$HOME/labs/solutions/week04/rtabmap.yaml`.

Measured 7 Oct 2026 (simulated):

| Map | End error / RMS | low step | table top | phantom cells | room width × depth | CPU, memory (SLAM) |
|---|---|---|---|---|---|---|
| slam_toolbox, LiDAR | 0.025 / 0.020 m | MISSED | MISSED | 0 | 10.00 × 8.05 m | 6 %, 48 MB |
| RTAB-Map, LiDAR | 0.010 / 0.046 m | MISSED | MISSED | 0 | 10.00 × 8.05 m | 51 %, 358 MB |
| RTAB-Map, LiDAR + D455, both draw (`Grid/Sensor "2"`) | 0.007 / 0.040 m | MISSED | MISSED | 1 | 10.15 × 8.21 m | 53 %, 518 MB |
| **RTAB-Map, LiDAR + D455, camera draws (`"1"`, solution)** | 0.002-0.005 / 0.041-0.045 m | **SEEN** | **SEEN** | 23-42 (two runs) | 10.15 × 8.20 m | 53 % + 4 % rgbd_sync, 518 MB |

CPU is % of one core of the 1-core test instance. What the numbers say: the camera did not make the *pose* better
(LiDAR SLAM is already within centimetres); it made the *map* better – it is the only sensor that sees the step and
the table top. The price: ten times the CPU and memory of slam_toolbox, walls slightly thicker (depth noise grows
with distance squared, so the room measures 1.5–2.5 % too big), and gaps where the camera's 87° view never pointed.
And "use both sensors" (`"2"`) was *worse* than either alone for the step – fusing sensors needs thought.

### For your report

Your three-map table, a screenshot of RViz with the step and table in the map, your TODO 3 value and why, and one
paragraph: was the camera worth its CPU cost for *this* robot in *this* lab? Label all results as simulated.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| RViz: "No map received" | SLAM needs a few seconds after Gazebo; with RTAB-Map the map appears after the robot moves 0.1 m |
| Depth cloud empty in RViz | `ros2 topic hz /camera/aligned_depth_to_color/image_raw` – if nothing, the launch was started with `camera:=false` |
| `map_saver_cli` times out | the SLAM brick is not running (look at T1), or add `--ros-args -p use_sim_time:=true` |
| The whole map is black (occupied) near the robot | TODO 3: the floor is being drawn as an obstacle |
| T1 repeats `Did not receive data since 5 seconds` | the camera is not publishing: `ros2 topic hz /rgbd_image`. On a slow computer the first images take up to 30 s |
| Launch dies: "process has died … gzserver" | `pkill -f gzserver`, wait 5 s, launch again |

The previous Week 4 ("Inertial sensing and measurement": IMU Allan deviation, magnetometer calibration, aliasing) is
kept in [`inertial_sensing/`](inertial_sensing/) as an optional extra.
