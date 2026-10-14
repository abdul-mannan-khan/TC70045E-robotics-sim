# Week 06 – See and Understand with the D455: from Pixels to the Map (Assessment 1 due)

In Week 4 the D455 depth camera improved the **map**. This week it does what a camera is really for: it
**recognises** things. Two painted boxes stand in the lab, one red and one green. Your brick, `box_finder.py`, finds
each box in the colour image, measures how far away it is in the depth image, turns that pixel into a 3-D point, and
puts it on the SLAM map – where you can check it against the true position.

**Watch the demo video first:** `TC70045E_Week06_demo.mp4` in the Week 6 folder on Blackboard. It shows every step
below, with Gazebo (the simulated world) and RViz (what the robot knows) side by side.

**Assessment 1 is due this week.** The last 35 minutes of the session are protected for finishing and submitting it.

| Time in class | Part |
|---|---|
| 40 min | lecture: the pinhole camera, colour in HSV, from a pixel to the map |
| 10 min | Step 0 – start the container |
| 45 min | Activities A1–A3 |
| 50 min | Your activity (the TODO) – finish `box_finder.py` |
| 35 min | Assessment 1: finish and submit |

---

## Step 0 – Start the container (once per session)

Exactly as in Week 2 ([week02/README.md](../week02/README.md#step-0--start-the-container-once-per-session)):
`docker start tc70045e`, open <http://localhost:6080>, **Connect**, open **Terminator** and run `update-labs`.
Split Terminator into three terminals (T1, T2, T3).
Check: `ls ~/labs/week06` lists `depth_sensing  edge_ai  launch  README.md  rviz  scripts`.

**Before every new launch:** Ctrl+C in T1 and wait for the `$` prompt. If the launch then dies with
"process has died … gzserver", run `pkill -f gzserver`, wait 5 s, launch again.

## The bricks this week

| Brick / file | What it does |
|---|---|
| [`launch/perception.launch.py`](launch/perception.launch.py) | robot in Gazebo with the D455 (424 × 240) + slam_toolbox + RViz. Switches: `tour`, `turn_rate`, `gui`, `rviz` |
| [`scripts/tour.py`](scripts/tour.py) | drives past the red box, stops with it 25° right of the image centre and looks for 10 s, then does the same at the green box (about 130 s) |
| [`scripts/pixel_probe.py`](scripts/pixel_probe.py) | prints the colour (BGR and HSV) and the depth at one pixel – by default the image centre |
| [`scripts/box_finder.py`](scripts/box_finder.py) | **your brick**: colour → mask → blob → depth → 3-D point → map. Three TODOs |
| [`rviz/perception.rviz`](rviz/perception.rviz) | map, robot, laser, depth cloud, colour image, the mask image, and the boxes found (`/boxes`) |

Where the boxes really are (map frame, i.e. relative to where the robot starts): **red (1.50, −2.40)**,
**green (7.20, −0.40)** – 0.3 m cubes. `box_finder.py` prints its error against these when you stop it.

---

## A1 – The camera, as a sensor (15 min)

**Goal:** know what the camera publishes and its numbers.

| | |
|---|---|
| T1 | `ros2 launch ~/labs/week06/launch/perception.launch.py` |
| T2 | `ros2 topic hz /camera/color/image_raw` (Ctrl+C after 10 s) |
| T2 | `ros2 topic echo --once /camera/color/camera_info --field k` |

**You should see:** Gazebo and RViz, the camera image bottom left in RViz. The rate is set to 15 Hz; on a computer without a GPU it is lower
(the scripts work from about 3 Hz). `k` is the camera matrix K = [fx, 0, cx, 0, fy, cy, 0, 0, 1]; measured:
`[223.41, 0, 212.5, 0, 223.41, 120.5, 0, 0, 1]` – fx = fy = 223.4 px, the centre at (212.5, 120.5).
**Check:** the image is 424 pixels wide and the D455's colour view is 87° wide. Work out fx from those two numbers
(fx = (width / 2) / tan(87° / 2)) and compare with `k[0]`.

## A2 – Depth at a pixel (15 min)

**Goal:** read the depth image at one pixel and compare it with a distance you know.

| | |
|---|---|
| T2 | `python3 ~/labs/week06/scripts/pixel_probe.py --ros-args -p use_sim_time:=true` |
| T3 | `ros2 run teleop_twist_keyboard teleop_twist_keyboard` – turn the robot until it faces a wall |

**You should see:** one line per second: pixel, colour, and the depth in millimetres averaged over 5 × 5 pixels.
Drive towards a wall and back: the depth follows. Pixels with no depth are 0 (too close – under about 0.5 m – or no
stereo match). **Check:** why is the depth image in millimetres and 16-bit integers, not metres? (Lecture: the real
D455 driver does it this way; 1 mm steps, 65 m maximum, half the bytes of a float.)

## A3 – The colours of the boxes (15 min)

**Goal:** measure the boxes' colour in HSV – the numbers you need for TODO 1.

| | |
|---|---|
| T1 | Ctrl+C, then `ros2 launch ~/labs/week06/launch/perception.launch.py tour:=true` |
| T2 | `python3 ~/labs/week06/scripts/pixel_probe.py --ros-args -p use_sim_time:=true -p u:=317` |

The tour stops twice for 10 s with a box **25° to the right of the image centre** – at pixel column
u = cx + fx · tan 25° = 212.5 + 223.4 × 0.466 ≈ 317. That is when the probed pixel is on the box.

**You should see** (measured): on the red box `HSV (0, 255, 178)` on the lit face and `(0, 255, 153)` on the
shaded one; on the green box `HSV (60, 255, 153)`. Brick walls measured `HSV (17, 40, 101)`, `(153, 67, 141)`,
`(162, 55, 126)`; the grey walls `HSV (0, 0, 72)`. Low saturation (S) is what separates them from the boxes. Also note the HSV of a brick wall and of a
wooden crate as the robot drives past: your mask must keep the box and reject those.

---

## Your activity (the TODO) – finish box_finder.py (50 min)

**What you build:** a perception brick that puts both boxes on the map, within 0.25 m of where they really are.

1. **Copy it** (keep the original): `cp ~/labs/week06/scripts/box_finder.py ~/labs/week06/scripts/my_box_finder.py`
2. **Open your copy** in VSCodium or `nano`. Three TODOs:
   * **TODO 1 – `COLOURS['green']`:** an HSV range (low, high) that keeps the green box and nothing else. The red
     ranges above it are a worked example (red wraps round H = 0, so it needs two). Use your A3 numbers.
   * **TODO 2 – back-projection:** `X` and `Y` from the pixel (u, v), the depth Z and the camera matrix (fx, fy, cx,
     cy). The lecture's pinhole slide has the formula. As given, every box lands on the camera's optical axis.
   * **TODO 3 – into the map:** the point is still in `camera_color_optical_frame` (X right, Y down, Z forward from
     the camera). The code already asks TF for the camera's pose in the map (`tr`); apply it to the point with
     `do_transform_point(p, tr)` (imported at the top). As given, the camera coordinates are used as if they were
     map coordinates.
3. **Run it**, one TODO at a time:
   * T1: `ros2 launch ~/labs/week06/launch/perception.launch.py tour:=true`
   * T2 (straight after): `python3 ~/labs/week06/scripts/my_box_finder.py --ros-args -p use_sim_time:=true`
   * when T1 prints `tour finished`, press **Ctrl+C in T2**: it prints one line per box with its error.
4. **Done when** – all three are true:
   * RViz shows a red and a green cube (the `/boxes` markers) on the map, where the boxes are in Gazebo;
   * the summary shows both boxes with an **error below 0.25 m**;
   * you have a table: one row per step (as given, + TODO 1, + TODO 2, + TODO 3) × (red error, green error,
     detections).

### Solution (compare after you have tried)

[`../solutions/week06/box_finder.py`](../solutions/week06/box_finder.py) – run it with
`python3 ~/labs/solutions/week06/box_finder.py --ros-args -p use_sim_time:=true`.

Measured 14 Oct 2026 (simulated; one tour each; error = the median position against the true box):

| Stage | Red: detections, error | Green: detections, error |
|---|---|---|
| as given | 198, 2.83 m – at (0.00, 0.00), the map origin | 0 – not found |
| + TODO 1 (green range) | 199, 2.83 m – at the origin | 104, 7.21 m – at the origin |
| + TODO 2 (back-projection) | 197, 2.49 m | 110, 6.36 m |
| **+ TODO 3 (into the map): solution**, two runs | 197 – 198, **0.089 – 0.092 m** | 103 – 106, **0.057 – 0.072 m** |

What the numbers say:
* **Until TODO 3, every number is meaningless.** A point in the camera's optical frame (Z forward, 1.5 m) is not a
  point on the map: before TODO 2 every box sits at the origin; after it, near the origin – and the error barely moves.
  Check frames before you trust coordinates.
* **The solution is repeatable** (two runs within 2 cm of each other) and within 10 cm with a 424 × 240 camera
  from 1.5 m. The red box is always about 9 cm short in x: one cause is that `BOX_HALF` is added along the camera
  axis, but the box is seen 25° off the axis. Can you find the others?
* The column "90 % of detections within" in the summary shows the worst detections: 0.11 – 0.24 m, from frames
  taken while the robot was still turning towards a box – the median ignores them.
* **TF timing (lecture slide 5):** the solution asks for the latest transform. That is fine while the robot stands
  still, as it does when it looks at a box. While it turns it is not: in a recording with the robot turning once on
  the spot at the end of the tour, those frames moved the green box 0.31 m. The time-correct call is in the solution
  as a comment – on our 1-core test computer it often waited for odometry that was still on its way, so try it on
  yours (extension: add `('spin', 360.0)` back to the tour in `tour.py`).

### For your report

Your table, an RViz screenshot with both boxes marked on the map, your HSV ranges and how you chose them, and one
paragraph: where does the remaining error come from? Label all results as simulated.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `box_finder.py` prints nothing | the camera is slow to start (up to 30 s on a laptop): `ros2 topic hz /camera/color/image_raw` |
| `no TF map <- camera: ... does not exist` at the start | SLAM has not published the map yet – it stops after a few seconds |
| now and then `Lookup would require extrapolation into the future` | the map transform is a little behind the camera; that image is skipped. Harmless if detections keep coming |
| the green box is found in the wrong place, far away | your range also keeps something else green-ish: look at the mask image in RViz |
| no summary after Ctrl+C | press Ctrl+C once and wait 2 s |

Optional extras from the previous course, in this folder: [`depth_sensing/`](depth_sensing/) (the depth error
against range, measured, and plane fitting) and [`edge_ai/`](edge_ai/) (a colour tracker that drives to the red box,
YOLO object detection on the CPU, and a language-model command interface).
