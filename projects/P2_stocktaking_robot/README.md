# P2 – Mobile robot: a warehouse stock-taking robot with a depth camera

**The job:** a mobile robot drives round a store room, looks at the shelves with its Intel RealSense D455 depth camera,
recognises parcels by their colour and puts each one on the map – where it is, to a few centimetres. You make the
robot find the parcels, put them on the map accurately, and measure how far you can trust its stock list.

| | |
|---|---|
| Robot | the course's mobile robot with a simulated **Intel RealSense D455** (colour + depth), LiDAR, two drive motors |
| Simulator | Gazebo (the room and two coloured parcels) + RViz (map, camera image, the parcels found) |
| Container | `abdulmannan617/tc70045e-ros2:humble` – **no GPU needed**, your laptop is enough |
| Starts from | [Week 6](../../week06/README.md) – demo video `TC70045E_Week06_demo.mp4` on Blackboard |
| You change | colour ranges and a few numbers in one Python file; the robot's tour |

**What you will be able to show at the end:** the robot touring the room by itself, the camera picture with the
parcels picked out, and a red and a green cube appearing on the map in RViz exactly where the parcels stand in Gazebo –
with a table of how accurate that is.

## What you will learn

Docker and the browser desktop · ROS 2 topics and RViz · how a depth camera works and how its error grows with
distance · colour segmentation (HSV) · the camera model (from a pixel to a point in 3-D) · coordinate frames and TF
(from the camera to the map) · measuring accuracy against the truth.

## 1. Start (every session)

On your laptop: `docker start tc70045e`, open <http://localhost:6080>, **Connect**, **Terminator**, `update-labs`,
split it into T1, T2, T3. Once:

```bash
mkdir -p ~/work/project && cp ~/labs/projects/P2_stocktaking_robot/results_template.csv ~/work/project/results.csv
cp ~/labs/solutions/week06/box_finder.py ~/work/project/my_finder.py
cp ~/labs/week06/scripts/tour.py ~/work/project/my_tour.py
```

## 2. The baseline you reproduce (Assessment 1)

| | |
|---|---|
| T1 | `ros2 launch ~/labs/week06/launch/perception.launch.py tour:=true` – the robot drives its tour by itself |
| T2 (straight after) | `python3 ~/labs/solutions/week06/box_finder.py --ros-args -p use_sim_time:=true` |
| when T1 prints `tour finished` | press **Ctrl+C in T2**: it prints one line per parcel – detections, where it put it, the truth, the error |

**Course measurements (14 Oct 2026):** red parcel 197–198 detections, error 0.089–0.092 m; green parcel 103–106
detections, error 0.057–0.072 m (two runs). The camera picture is 424 × 240 pixels.

## 3. Where to edit, and how

Open `~/work/project/my_finder.py` in VSCodium and Ctrl+F for the text in the second column. Run your copy in T2 with
`python3 ~/work/project/my_finder.py --ros-args -p use_sim_time:=true`.

| To test… | Search for | Change | What to look at |
|---|---|---|---|
| how strict the colour test is | `COLOURS = {` | widen or narrow the HSV ranges (low, high) of `'green'`; find good values with `python3 ~/labs/week06/scripts/pixel_probe.py --ros-args -p use_sim_time:=true` (Week 6 A3) | false detections against missed ones |
| how far it trusts the camera | `MAX_RANGE = 3.5` | `2.0`, `3.5`, `5.0` m | the depth error grows with distance squared: error against number of detections |
| ignoring small specks | `MIN_AREA = 80` | `20`, `80`, `300` pixels | noise against far-away parcels |
| driving faster while looking | T1 launch line | `turn_rate:=0.6` or `1.0` (default 0.3) | blurred and late frames: does the error grow? |
| **a different tour** | `~/work/project/my_tour.py`, `TOUR = [` | change the stops or the `('look', 10.0)` times; run it in T3 instead of `tour:=true`: `python3 ~/work/project/my_tour.py --ros-args -p use_sim_time:=true` | seeing the parcels from farther, nearer, or at an angle |

Python rules: keep the brackets, commas and the spaces at the start of each line. Compare with the original in
`~/labs/solutions/week06/` if it stops working.

**Assessment 2 – your own feature (choose one, or agree another with the module leader):**
* a **stock list file**: at the end, write each parcel's colour, position and number of detections to
  `~/work/project/stock.csv`;
* a **confidence check**: report a parcel only if it was seen in at least N frames, and measure the best N;
* a **third parcel colour**: add a colour range (e.g. blue) and a parcel of that colour (ask the module leader how to
  add one to the world) – does it find it, and does it confuse it with anything?

## 4. Experiments

* **Assessment 1 (Week 6):** the course solution, **3 runs**; one change of your own (e.g. `MAX_RANGE` at three
  values), 1 run each.
* **Assessment 2 (Week 12):** **3 runs** per configuration; at least **two factors** (e.g. `MAX_RANGE` and
  `turn_rate`) and **your own feature**.

## 5. Results file and figures

Columns: `config, run, date, computer, max_range_m, min_area_px, turn_rate, red_detections, red_error_m,
green_detections, green_error_m, false_detections, notes`.

```bash
python3 ~/labs/projects/tools/plot_results.py ~/work/project/results.csv --metric green_error_m \
    --ylabel "green parcel position error [m]" --out ~/work/project/fig_error.png
```

## 6. Your paper (Assessment 2)

* **Possible title:** *Colour-and-depth parcel localisation for a stock-taking mobile robot with an Intel RealSense
  D455: a simulation study.*
* **Story:** the job, how the camera and the software find a parcel and place it on the map, how accurate it is, what
  makes it worse, and what a real warehouse would add (lighting, similar colours, labels, QR codes).
* **Figures:** RViz with the parcels on the map; the camera picture with the mask; error against `MAX_RANGE`.
* **Limits:** two parcels, perfect simulated lighting, a simulated depth noise model.
