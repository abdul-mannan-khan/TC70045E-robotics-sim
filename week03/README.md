# Week 03 – The Navigation Brick: from a Map to Autonomous Delivery

In Week 2 the robot built a map while you drove it. This week it uses a map to drive **itself**: it works out where
it is on the map (**AMCL**), plans a path to a goal (**Nav2 planner**), follows it while avoiding things that are not
on the map (**Nav2 controller + costmaps**), and recovers when it gets stuck. You then program a security patrol.

**Watch the demo video first:** `TC70045E_Week03_demo.mp4` in the Week 3 folder on Blackboard. It shows every step
below, with Gazebo (the simulated world) and RViz (what the robot knows) side by side.

| Time in class | Part |
|---|---|
| 45 min | lecture: localisation, planning, costmaps; the motors and electronics behind `cmd_vel` |
| 10 min | Step 0 – start the container |
| 90 min | Activities A1–A5 |
| 35 min | Your activity (the TODO) – a security patrol |

---

## Step 0 – Start the container (once per session)

Exactly as in Week 2 ([week02/README.md](../week02/README.md#step-0--start-the-container-once-per-session)):
start `abdulmannan617/tc70045e-ros2:humble` (own computer, Vast.ai or `docker compose up -d ros2`), open
<http://localhost:6080>, password `ubuntu`, open **Terminator** and split it into three terminals (T1, T2, T3).
Check: `ls ~/labs/week03` lists `launch  maps  rviz  scripts  README.md`.

**Before every new launch:** Ctrl+C in T1 and wait for the `$` prompt. If the launch then dies with
"process has died … gzserver", run `pkill -f gzserver`, wait 5 s, launch again.

## The bricks this week

| Brick / file | What it does |
|---|---|
| [`launch/nav.launch.py`](launch/nav.launch.py) | one launch, five bricks: robot in Gazebo, map server, AMCL, Nav2, RViz. Switches: `gui`, `rviz`, `map` |
| [`config/nav2_params.yaml`](config/nav2_params.yaml) | the Nav2 settings (costmaps, planner, controller). One change from the module default: sideways motion enabled in the velocity smoother |
| [`scripts/set_start_pose.py`](scripts/set_start_pose.py) | started by the launch: tells AMCL the start pose and repeats until AMCL confirms it |
| [`maps/lab_map.yaml`](maps/lab_map.yaml) + `.pgm` | the lab map (two rooms, made with the Week 2 explorer). Its origin (0, 0) is where the robot starts |
| [`rviz/nav.rviz`](rviz/nav.rviz) | map, laser, AMCL particles, global + local costmap, global plan (green), local plan (orange); tools **2D Pose Estimate**, **2D Goal Pose**, **Publish Point** |
| [`scripts/go_to.py`](scripts/go_to.py) | send one goal from Python and report SUCCEEDED / FAILED and the time |
| [`scripts/drop_box.py`](scripts/drop_box.py) | put a 0.4 m box into the Gazebo world (not on the map), or `--remove` it |
| [`scripts/patrol.py`](scripts/patrol.py) | **your activity** – a patrol with three TODOs |

All coordinates are in the **map** frame, in metres: x to the right on the map, y up, yaw 0° = facing +x.
The doorway between the two rooms is at about (4.0, -1.0).

---

## A1 – Start navigation and localise (15 min)

**Goal:** start the five bricks and see AMCL work out where the robot is.

| | |
|---|---|
| T1 | `ros2 launch ~/labs/week03/launch/nav.launch.py gui:=true` |
| T2 (after about 30 s) | `ros2 topic echo --once /amcl_pose --field pose.pose.position` |

**You should see:** Gazebo (the lab and the robot) and RViz: the grey map, the red laser points lying on the map's
walls, and a cloud of **blue arrows** around the robot (AMCL's guesses). T2 prints a position close to `x: 0.0, y: 0.0`
(measured: 0.02, 0.01). The launch file tells AMCL the start pose automatically and repeats it until AMCL confirms
(T1 prints `AMCL confirmed the start pose`, about 15 s after the launch).
**Check – lose the robot on purpose:** in RViz click **2D Pose Estimate** and click-drag a pose in the *other* room.
The laser points no longer match the walls. Now click **2D Pose Estimate** again on the robot's true position (look
at Gazebo): the laser lines up again. That is localisation.

## A2 – Goals by clicking (15 min)

**Goal:** send goals with the mouse and watch the two plans.

1. In RViz click **2D Goal Pose**, then click in the other room and drag to choose the direction.
2. **You should see:** a **green** line (global plan, on the map) and a short **orange** line (local plan, what the
   controller is doing now); the robot drives through the doorway in Gazebo.
3. **Read coordinates:** T2: `ros2 topic echo /clicked_point`. In RViz click **Publish Point**, then click on the
   map: T2 prints `x:` and `y:` of that point. You will need this in your activity.

## A3 – Goals from Python (15 min)

| | |
|---|---|
| T2 | `python3 ~/labs/week03/scripts/go_to.py 4.0 -1.0 0` (the doorway) |
| T2 | `python3 ~/labs/week03/scripts/go_to.py 0.0 0.0 180` (back to the start, facing the other way) |

**You should see:** `distance remaining …` lines going down, then `RESULT SUCCEEDED after … s`
(measured: doorway 14-16 s). Open the script and read it – it is 40 lines; your patrol starts from it.
**Check 1 – a goal outside the map:** `go_to.py 12.0 0.0 0`. No path exists: watch T1 – Nav2 tries its recovery
behaviours (spin, back up, wait) and then reports `FAILED` (measured: after 21 s; spin twice, back up once, wait once).
**Check 2 – a goal inside a wall:** `go_to.py 4.0 2.0 0` (the wall between the rooms). Nav2 reports `SUCCEEDED`
(measured: 18 s) – the planner accepts the nearest free cell within 0.5 m. Where is the robot really (Gazebo)?
(Measured: map (3.62, 1.74) – 0.43 m short of the goal, on the room-1 side of the wall.)
Lesson: a result code is not a measurement – check positions yourself.

## A4 – Something new appears (15 min)

**Goal:** see the difference between the **map** (what was there) and the **costmap** (what the laser sees now).

| | |
|---|---|
| T2 | `python3 ~/labs/week03/scripts/go_to.py 4.0 -1.0 0` (go to the doorway first) |
| T3 | `python3 ~/labs/week03/scripts/drop_box.py 2.0 -1.0` – an orange box appears in Gazebo |
| T2 | `python3 ~/labs/week03/scripts/go_to.py 0.0 0.0 180` |
| T3 | `python3 ~/labs/week03/scripts/drop_box.py --remove` |

**You should see:** the box is *not* on the grey map, but once the laser sees it, it appears in the costmap and the
green plan bends round it (measured: back at the start in about 14.5 s).
**Check:** after removing the box, a "ghost" may stay in the global costmap. Clear it:
`ros2 service call /global_costmap/clear_entirely_global_costmap nav2_msgs/srv/ClearEntireCostmap`.

## A5 – Tune the costmap (15 min)

**Goal:** see how one number changes the robot's behaviour.

| | |
|---|---|
| T3 | `ros2 param get /global_costmap/global_costmap inflation_layer.inflation_radius` – default **0.35** m |
| T3 | `ros2 param set /global_costmap/global_costmap inflation_layer.inflation_radius 0.15` |
| T2 | send the doorway goal again and compare the green path with A3 |
| T3 | `ros2 param set /global_costmap/global_costmap inflation_layer.inflation_radius 0.8`, then `go_to.py 0.0 0.0 0` |
| T3 | set it back: `… inflation_radius 0.35` |

**You should see:** the *shape* of the green path changes – a small radius lets it run close to walls and furniture,
a large one keeps it in the middle of free space. In this open lab the *time* hardly changes (measured: doorway
13.8 s with 0.15 m, 14.5 s with 0.8 m; back to the start 18.9 s with 0.35 m, 19.8 s with 0.8 m). The 2.6 m doorway
stays open even at 0.8 m – a narrow corridor would not. Which value would you choose for a real robot near people?

**Optional:** navigate on *your own* Week 2 map:
`ros2 launch ~/labs/week03/launch/nav.launch.py gui:=true map:=$HOME/labs/week02/my_map.yaml`.

---

## Your activity (the TODO) – a security patrol (35 min)

**What you build:** a program that sends the robot round both rooms – at least **four waypoints** – reports for every
waypoint whether it was reached and how long it took, and carries on if one waypoint cannot be reached.

1. **Copy the template** (keep the original): `cp ~/labs/week03/scripts/patrol.py ~/labs/week03/scripts/my_patrol.py`
2. **Open your copy** in VSCodium (desktop icon) or `nano ~/labs/week03/scripts/my_patrol.py`. There are three TODOs:
   * **TODO 1 – waypoints.** With `nav.launch.py` running, use **Publish Point** in RViz and
     `ros2 topic echo /clicked_point` (A2) to read at least four points: through the doorway, into room 2, round
     room 2, and back to the start. Keep 0.5 m away from walls and furniture. Fill in the `WAYPOINTS` list.
   * **TODO 2 – `visit()`.** Send the goal with `nav.goToPose(...)`, wait until `nav.isTaskComplete()`, give up with
     `nav.cancelTask()` after `TIME_LIMIT` seconds, and return `(reached, seconds)`. `go_to.py` shows each call.
   * **TODO 3 – the result line**, e.g. `RESULT 5 of 5 waypoints reached, total 93 s, mean 18.5 s per waypoint`.
3. **Run it** – T1 running `nav.launch.py gui:=true` (A1), then T2:
   `python3 ~/labs/week03/scripts/my_patrol.py 2` (two laps).
4. **Done when** – all four are true:
   * every waypoint line says `REACHED`, in both laps;
   * the robot passes through the doorway into room 2 and back (watch Gazebo);
   * the program prints your `RESULT` line and ends by itself;
   * **robustness:** drop a box on one of your waypoints (`drop_box.py x y`) – that waypoint is reported `FAILED`
     and the patrol carries on with the next one.

### Solution (compare after you have tried)

[`../solutions/week03/patrol.py`](../solutions/week03/patrol.py) – run it with
`python3 ~/labs/solutions/week03/patrol.py 1`. Measured 7 Oct 2026 in three cold starts: **5 of 5 waypoints reached** every time, total 91-95 s,
about 18.5 s per waypoint (doorway, room 2 upper, room 2 lower, room 1 upper, start). It also calls
`nav.clearAllCostmaps()` before each waypoint, so obstacles that have gone (a removed box) are forgotten.

### For your report

Record: your waypoints (a screenshot of RViz with them marked), the per-waypoint times for two laps, the effect of
the inflation radius you tried in A5, and what happened when a waypoint was blocked. Label simulated results as
simulated.

---

## Measured on the reference set-up (ROS 2 Humble, Nav2, 7 Oct 2026)

| Test | Result |
|---|---|
| AMCL start pose (automatic, confirmed by set_start_pose.py) | (0.02, 0.01) m |
| Goal: start → doorway (4.0, -1.0) | SUCCEEDED in 14-16 s (three cold starts); true position (3.86, -0.91) |
| Goal: doorway → start with a box at (2.0, -1.0) | SUCCEEDED in about 14.5 s, round the box |
| Patrol (solution), 1 lap, 5 waypoints | 5 of 5 reached, 91-95 s (three cold starts) |
| Cold start with the Gazebo window and screen recording | start pose confirmed 15 s after the launch; 0 Nav2 failures in 3 runs |

## Troubleshooting

| Problem | Fix |
|---|---|
| RViz: no blue arrows, robot not on the map | wait 20-30 s after the launch; else set it yourself with **2D Pose Estimate** |
| `go_to.py` waits for ever at "Nav2 is ready" | Nav2 is still starting (about 30 s after the launch); or the launch died - look at T1 |
| Goal FAILED at once | the goal is inside a wall or too close to one - check it with Publish Point |
| Plan refuses a goal that worked before | a ghost obstacle: clear the costmap (A4, Check) |
| Launch dies: "process has died … gzserver" | `pkill -f gzserver`, wait 5 s, launch again |

The previous Week 3 ("Making it move": motor bench, PID, driver configuration clinic) is kept in
[`making_it_move/`](making_it_move/) as an optional extra.
