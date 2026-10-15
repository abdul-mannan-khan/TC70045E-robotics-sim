# P3 – Warehouse and delivery: a stock-taking robot whose list sends out a delivery drone

| | Part A – Assessment 1 (Weeks 1–6) | Part B – Assessment 2 (Weeks 7–12) |
|---|---|---|
| You build | a **mobile robot** that tours a store room, finds the parcels with its Intel RealSense D455 depth camera, puts each on the map and writes a **stock list** (colour, position) | a **delivery drone** that takes your robot's stock list, flies to each parcel's delivery point, takes a proof-of-delivery photo and returns home – but only after a **pre-flight check** says GO, and with a watchdog that lands it if its data fails |
| Lectures | Week 4 (the D455, depth), Week 6 (perception: colour, depth, camera model, TF) | Week 10 (drone with ROS 2: mission node, watchdog), Week 12 (pre-flight check, fault injection); Week 9 to meet AirSim |
| Simulator | Gazebo + RViz | AirSim + PX4 + ROS 2 (town world) |
| Container | `abdulmannan617/tc70045e-ros2:humble` – laptop, no GPU | `abdulmannan617/tc70045e-drone:latest` – NVIDIA GPU: Vast.ai |
| Demo videos (Blackboard) | `TC70045E_Week04_demo.mp4`, `TC70045E_Week06_demo.mp4` | `TC70045E_Week09_demo.mp4`, `TC70045E_Week10_demo.mp4`, `TC70045E_Week12_demo.mp4` |

**How Part B extends Part A:** the robot and the drone talk through a file – the robot's `stock.csv`. Part A
produces it; Part B's drone reads it ([`../tools/handover.py`](../tools/handover.py)) and turns each parcel into a
delivery point. In Assessment 2 you show the chain: stock-taking → stock list → pre-flight GO → delivery flight →
proof-of-delivery photos.

---

## Part A – the stock-taking robot (Assessment 1)

### Start (every session)

Laptop: `docker start tc70045e`, <http://localhost:6080>, **Connect**, **Terminator**, `update-labs`, T1–T3. Once:

```bash
mkdir -p ~/work/project && cp ~/labs/projects/P3_warehouse_and_delivery/results_partA.csv ~/labs/projects/P3_warehouse_and_delivery/results_partB.csv ~/work/project/
cp ~/labs/solutions/week06/box_finder.py ~/work/project/my_finder.py
```

### Baseline to reproduce

| | |
|---|---|
| T1 | `ros2 launch ~/labs/week06/launch/perception.launch.py tour:=true` – the robot tours the room by itself |
| T2 (straight after) | `python3 ~/labs/solutions/week06/box_finder.py --ros-args -p use_sim_time:=true` |
| when T1 prints `tour finished` | **Ctrl+C in T2** – one line per parcel: detections, position, truth, error |

**Course measurements (14 Oct 2026):** red parcel 197–198 detections, error 0.089–0.092 m; green 103–106 detections,
error 0.057–0.072 m (two runs). In RViz a red and a green cube appear on the map where the parcels stand in Gazebo.

### Where to edit, and how

Open `~/work/project/my_finder.py` in VSCodium, Ctrl+F the text in the second column; run it in T2 with
`python3 ~/work/project/my_finder.py --ros-args -p use_sim_time:=true`.

| Step | Search for | Change | Look at |
|---|---|---|---|
| 1 the stock list (**required** – Part B needs it) | the `print(` line in `summary()` that ends `p90), flush=True)` | add the two lines below this table directly under it | `~/work/project/stock.csv` has one row per parcel |
| 2 how far it trusts the camera | `MAX_RANGE = 3.5` | `2.0` / `3.5` / `5.0` m | error against detections (depth noise grows with distance²) |
| 3 ignoring specks | `MIN_AREA = 80` | `20` / `80` / `300` pixels | false and missed detections |
| 4 how strict the colour test is | `COLOURS = {` | narrow or widen the green HSV range; probe colours with `python3 ~/labs/week06/scripts/pixel_probe.py --ros-args -p use_sim_time:=true` | detections, false detections |
| 5 touring faster | T1 launch line | `turn_rate:=0.6` / `1.0` (default 0.3) | does the error grow? |

The stock-list lines for step 1 – paste them directly under that `print(` line, with 12 spaces in front of `with`
(the same as in front of `print(`); checked to run:

```python
            with open(os.path.expanduser('~/work/project/stock.csv'), 'a') as f:
                f.write('%s,%.2f,%.2f,%d\n' % (colour, mx, my, len(a)))
```

Add `import os` under `import math` at the top, and before each run start the file with its header:
`echo "name,x,y,detections" > ~/work/project/stock.csv`.

### Part A experiments (minimum)

The course finder 3 runs · your stock list from 3 runs (do the positions agree?) · one factor of steps 2–5 at three
values.

---

## Part B – the delivery drone (Assessment 2)

### Start (every session)

1. Rent a GPU machine with the **drone** image ([docs/RUN_ON_VAST.md](../../docs/RUN_ON_VAST.md)); note instance,
   price, times. Desktop → terminal → `update-labs`. Copy `stock.csv` and `results_partB.csv` into `~/work/project/`.
   Once: `cp ~/labs/solutions/week10/mission_node.py ~/work/project/my_delivery.py`
2. T1: `drone-sim start --world neighborhood` · T2: `python3 ~/labs/week10/scripts/03_airsim_ros2_bridge.py` · T3:
   `python3 ~/labs/week10/scripts/04_px4_ros2_bridge.py` · optional RViz: `rviz2 -d ~/labs/week10/scripts/airsim.rviz`
3. **At the end:** download `~/work/project/` and `~/mission/`, then **Destroy** the machine.

### Baseline to reproduce

T4: `python3 ~/labs/solutions/week12/preflight.py --alt 15 --length 30 --width 30` → `VERDICT GO`; then
`python3 ~/labs/solutions/week10/mission_node.py` → `RESULT 34 s, 39.1 m flown, worst waypoint miss 0.42 m, …`.
**Course (15 Oct 2026):** pre-flight GO (link 50 per s, GPS 3D fix, 15 satellites); mission 4 of 4 waypoints in
34 s, worst miss 0.42–0.47 m. Fault test (Week 12): `python3 ~/labs/week12/scripts/inject_fault.py --sensor gps --type off`
→ pre-flight NO-GO, the mission never starts (`--type ok` to restore, then `drone-sim stop` and `start` before flying).

### The hand-over, and what to change

1. **Check it without flying:** `python3 ~/labs/projects/tools/handover.py ~/work/project/stock.csv --scale 3` – each
   parcel's store-room position × 3 becomes a delivery point in metres from take-off (all within 30 m).
2. **Use it:** in `~/work/project/my_delivery.py`, Ctrl+F `WAYPOINTS = [` and replace that line with:
   ```python
   import os, sys
   sys.path.insert(0, os.path.expanduser('~/labs/projects/tools'))
   from handover import load_points
   WAYPOINTS = load_points('~/work/project/stock.csv', scale=3.0) + [(0.0, 0.0)]
   ```
3. **Deliver, but only on GO:**
   `python3 ~/labs/solutions/week12/preflight.py --alt 15 --length 30 --width 30 && python3 ~/work/project/my_delivery.py`

| Then test… | Search for / where | Change |
|---|---|---|
| speed against delivery accuracy | `SPEED, TOL, STILL = 2.0, 0.5, 0.2` | first number `1.0` / `2.0` / `3.0` m/s |
| proof-of-delivery photo quality | same line | `STILL` `0.1` / `0.2` / `0.5`; `python3 ~/labs/projects/tools/sharpness.py ~/mission/wp*.png` |
| a failure before take-off | T4, before the delivery | `inject_fault.py --sensor gps --type off` – does your chain stay on the ground? |
| a failure in flight | T2 during the flight | Ctrl+C on the AirSim bridge – the watchdog must land the drone |

Routes from your own stock list were not flown by the course: start with one parcel, watch AirSim, stay over the
streets at 15 m. **Failure injection only in the simulator – never on a drone that is going to fly.**

### Part B experiments (minimum)

The course mission and pre-flight 3 runs · the whole chain (stock-taking → stock list → GO → delivery) 3 times · two
factors at ≥ 3 values, 3 runs each · one failure before take-off and one in flight.

---

## Results and figures

`results_partA.csv`: `config, run, date, computer, max_range_m, min_area_px, turn_rate, red_detections, red_error_m,
green_detections, green_error_m, false_detections, notes` · `results_partB.csv`: `config, run, date, computer,
parcels, preflight_verdict, fault, waypoints_reached, photos, time_s, flown_m, worst_miss_m, end_from_start_m,
speed_mps, still_mps, sharpness_mean, watchdog_fired, notes`.

**Paper idea:** *From stock-taking to delivery: a depth-camera robot and a ROS 2 delivery drone with pre-flight
safety checks, in simulation.* Figures: parcels on the map in RViz; the stock list; the delivery route over the town;
a proof-of-delivery photo; error against camera range; the GO / NO-GO table.
