# P2 – Search and rescue: a robot maps the building, a drone searches the land around it

| | Part A – Assessment 1 (Weeks 1–6) | Part B – Assessment 2 (Weeks 7–12) |
|---|---|---|
| You build | a **mobile robot** that maps a damaged building for a rescue team – with its LiDAR and its D455 depth camera – and finds the hazards (a low step, a table top) a LiDAR alone misses; the map is measured | a **search drone** that photographs the land around the building in a planned search pattern. **Its search area is sized from your robot's map**, and a pre-flight check decides whether the battery allows it. Optional: the robot maps the building *by itself* (Week 8 exploration) |
| Lectures | Week 2 (SLAM), Week 4 (LiDAR + D455, RTAB-Map, scoring maps) | Week 9 (drones without ROS 2: AirSim, PX4, survey), Week 12 (pre-flight GO / NO-GO); Week 8 optional |
| Simulator | Gazebo + RViz, slam_toolbox, RTAB-Map | AirSim + PX4, mountain valley |
| Container | `abdulmannan617/tc70045e-ros2:humble` – laptop, no GPU | `abdulmannan617/tc70045e-drone:latest` – NVIDIA GPU: Vast.ai |
| Demo videos (Blackboard) | `TC70045E_Week02_demo.mp4`, `TC70045E_Week04_demo.mp4` | `TC70045E_Week09_demo.mp4`, `TC70045E_Week12_demo.mp4` (`TC70045E_Week08_demo.mp4` optional) |

**How Part B extends Part A:** the robot's map tells the rescue team how big the building is. Part B scales that
footprint up to the search area outside (× 10: a 10 × 8 m building → a 100 × 80 m search area), checks the battery
for it, and flies it. In Assessment 2 you show the chain: robot map → measured size → planned search → GO / NO-GO →
flight → photos.

---

## Part A – the mapping robot (Assessment 1)

### Start (every session)

Laptop: `docker start tc70045e`, <http://localhost:6080>, **Connect**, **Terminator**, `update-labs`, T1–T3. Once:

```bash
mkdir -p ~/work/project ~/maps && cp ~/labs/projects/P2_search_and_rescue/results_partA.csv ~/labs/projects/P2_search_and_rescue/results_partB.csv ~/work/project/
cp ~/labs/solutions/week04/rtabmap.yaml ~/work/project/my_rtabmap.yaml
```

### Baseline to reproduce

The robot drives a fixed 24 m loop through both rooms by itself (`drive:=true`); after `loop finished` you save and
score the map. Each map: `ros2 run nav2_map_server map_saver_cli -f ~/maps/<name> --ros-args -p use_sim_time:=true`,
then `python3 ~/labs/week04/scripts/map_check.py ~/maps/<name>.yaml` (hazards SEEN / MISSED, phantom cells) and
`python3 ~/labs/week04/scripts/map_metrics.py ~/maps/<name>.yaml` (building width × depth).

| `config` | T1 |
|---|---|
| `LiDAR, slam_toolbox` | `ros2 launch ~/labs/week04/launch/slam.launch.py slam:=toolbox drive:=true` |
| `LiDAR, RTAB-Map` | `ros2 launch ~/labs/week04/launch/slam.launch.py slam:=rtabmap drive:=true` |
| `LiDAR + D455 (solution)` | `ros2 launch ~/labs/week04/launch/slam.launch.py slam:=rtabmap drive:=true config:=$HOME/labs/solutions/week04/rtabmap.yaml` |

**Course measurements (7 Oct 2026):** LiDAR maps 10.00 × 8.05 m, low step and table top MISSED; LiDAR + D455 10.15 ×
8.20 m, both hazards SEEN, 23–42 phantom cells, ten times the CPU of slam_toolbox.

### Where to edit, and how

| To test… | Where | Change | Look at |
|---|---|---|---|
| which sensor draws the map | `~/work/project/my_rtabmap.yaml`, Ctrl+F `Grid/Sensor` | `"0"` LiDAR, `"1"` camera, `"2"` both | hazards SEEN, phantom cells |
| what counts as floor | same file, `Grid/MaxGroundHeight` | e.g. `"0.02"`, `"0.04"`, `"0.06"` (the step is 8 cm, depth noise ~1.5 cm at 2 m) | step SEEN? phantoms? |
| your own drive (Week 2) | `ros2 launch ~/labs/week02/launch/lego.launch.py gui:=true slam:=true` + keyboard in T2 | drive through both rooms yourself, save, score | a person-driven map against the automatic loop |

Run your settings with `… slam:=rtabmap drive:=true config:=$HOME/work/project/my_rtabmap.yaml`. YAML: keep the
quotes, the indentation and the colon.

**Hand-over output (required):** write the measured building size of your best map into
`~/work/project/building.csv` – two lines: `width_m,depth_m` and e.g. `10.15,8.20`.

### Part A experiments (minimum)

The three baseline maps, 1 run each, and the solution 3 runs · one factor from the table at three values · your
`building.csv`.

---

## Part B – the search drone (Assessment 2)

### Start (every session)

1. Rent a GPU machine with the **drone** image ([docs/RUN_ON_VAST.md](../../docs/RUN_ON_VAST.md)); note instance,
   price, times. Desktop → terminal → `update-labs`, T1–T3. Copy `building.csv` and `results_partB.csv` into
   `~/work/project/`. Once: `cp ~/labs/solutions/week09/mission.py ~/work/project/my_search.py`
2. T1: `drone-sim start --world mountains` (wait for `PX4 SITL is ready for take-off`).
3. **At the end:** download `~/work/project/` and `~/survey/`, then **Destroy** the machine.

### Baseline to reproduce

`python3 ~/labs/solutions/week12/preflight.py` → GO; then
`python3 ~/labs/solutions/week09/mission.py --alt 40 --length 100 --width 100` →
`plan: footprint 80.0 m, row spacing 64.0 m, 6 waypoints` … `RESULT complete: 89 s, 535 m flown, 6 photos, worst waypoint miss 0.99 m, landed`.
**Course (15 Oct 2026):** 6 waypoints, 535 m, 89 s, every waypoint within 1.0 m (3 runs); pre-flight GO for this
search (battery needed 37 %), NO-GO for a 1 × 1 km search (195 %). **Fly at 40 m or higher** in this valley.

### The hand-over, and what to change

1. **From the map to the search area:** width × 10 and depth × 10, e.g. 10.15 × 8.20 m → `--length 102 --width 82`.
2. **Ask before you fly:** `python3 ~/labs/solutions/week12/preflight.py --alt 40 --length 102 --width 82` – GO or NO-GO,
   and the predicted flight minutes. Then fly with `&&` so a NO-GO keeps the drone on the ground:
   `python3 ~/labs/solutions/week12/preflight.py --alt 40 --length 102 --width 82 && python3 ~/work/project/my_search.py --alt 40 --length 102 --width 82`

| Then test… | Change | Look at |
|---|---|---|
| flight height | `--alt 40` / `50` / `60` (both commands) | photos, time, detail per photo |
| photo overlap | `--overlap 0.2` / `0.4` / `0.6` | time against coverage |
| a bigger search area | scale × 10 / × 15 / × 20 | when does the pre-flight check say NO-GO? |
| ground detail (your code) | in `my_search.py`, Ctrl+F `footprint =`, add below it: `print('ground sampling distance %.1f cm per pixel' % (100 * footprint / 640))` | cm per pixel at each height |
| predicted against real time | compare preflight's minutes with the RESULT seconds | is the battery model right? |

Search areas other than the course's 100 × 100 m were not flown by the course: start at × 10, and watch the drone.

**Optional extension (Week 8):** let the robot map the building by itself –
`ros2 launch ~/labs/week08/launch/explore.launch.py` and `python3 ~/labs/solutions/week08/explorer.py --ros-args -p use_sim_time:=true`
– and hand *that* map's size to the drone.

### Part B experiments (minimum)

The course search 3 runs · the hand-over chain (your map → size → pre-flight → search) 3 runs · two factors at ≥ 3
values (3 runs each) · predicted against measured flight time.

---

## Results and figures

`results_partA.csv`: `config, run, date, computer, slam, grid_sensor, max_ground_height_m, low_step,
table_top, phantom_cells, width_m, depth_m, end_error_m, notes` · `results_partB.csv`: `config, run, date, computer,
length_m, width_m, alt_m, overlap, preflight_verdict, predicted_min, waypoints, photos, time_s, flown_m, worst_miss_m,
gsd_cm_per_px, notes`.

**Paper idea:** *From indoor mapping to outdoor search: a ground robot and a survey drone for search and rescue in
simulation.* Figures: the map with the hazards; the search pattern over the valley; photos at two heights; flight
time against overlap; predicted against measured time.
