# P3 – Plan a drone photo survey: height, overlap and accuracy

**Question:** a quadcopter photographs a 100 × 100 m patch of a mountain valley in a lawn-mower pattern. How do the
flight height, the overlap between photo strips and the "arrived" tolerance change the number of photos, the flight
time, the distance flown and the ground detail in each photo – and does a simple flight-time model predict the real
flight?

| | |
|---|---|
| Sensors → actuators | GPS, IMU, barometer (inside the PX4 autopilot), a downward camera → four motors |
| Simulator | AirSim (mountain valley world) + PX4 1.14 autopilot (software in the loop), no ROS 2 |
| Container | `abdulmannan617/tc70045e-drone:latest` – **needs an NVIDIA GPU**: rent one on Vast.ai |
| Starts from | [Week 9](../../week09/README.md) (and [Week 12](../../week12/README.md) for the flight-time model) – demo videos `TC70045E_Week09_demo.mp4`, `TC70045E_Week12_demo.mp4` on Blackboard |
| You change | numbers on the command line; later two or three lines of Python |

## What you will learn

Renting a GPU computer on Vast.ai and using it safely · the AirSim simulator and the PX4 autopilot · how a script
commands a drone over MAVLink · NED coordinates · camera geometry (footprint, overlap, ground sampling distance) ·
measuring a mission.

## 1. Start (every session)

1. Rent a GPU machine with the **drone** image – [docs/RUN_ON_VAST.md](../../docs/RUN_ON_VAST.md) (about
   $0.10–0.20 per hour, 80 GB disk). Write the instance number, price and start time in your notes.
2. Open its desktop in your browser, open a terminal, run `update-labs`, split it into T1, T2, T3.
3. T1: `drone-sim start --world mountains` – wait for `PX4 SITL is ready for take-off` (about a minute).
4. Once per machine: `mkdir -p ~/work/project && cp ~/labs/solutions/week09/mission.py ~/work/project/my_mission.py`
   and `cp ~/labs/projects/P3_drone_survey/results_template.csv ~/work/project/results.csv`.
5. **At the end:** download `~/work/project/` and `~/survey/` (Firefox → OneDrive, or `git push`), then **Destroy**.

## 2. The baseline you reproduce (Assessment 1)

```bash
python3 ~/labs/week09/scripts/mission.py --alt 40 --length 100 --width 100          # as given  -> config "as given"
python3 ~/labs/solutions/week09/mission.py --alt 40 --length 100 --width 100        # solution  -> config "solution 40 m"
ls ~/survey                                                                          # one photo per waypoint
```

The script prints `plan: footprint 80.0 m, row spacing 64.0 m, 6 waypoints`, one line per waypoint and
`RESULT complete: 89 s, 535 m flown, 6 photos, worst waypoint miss 0.99 m, landed`. **Course measurements
(15 Oct 2026):** as given 22 waypoints, every one missed (worst 119.6 m); solution 6 waypoints, 535 m, 89 s, worst miss
0.98 – 1.00 m in three runs.

**Safety rule of this world:** fly at **40 m or higher**. The valley has ridges; below 40 m the survey has crashed
(it has no obstacle avoidance). Before every new flight: `drone-sim stop`, then `drone-sim start --world mountains`
if a flight ended badly.

## 3. Where to edit, and how

| To test… | Where | Change | What to think about |
|---|---|---|---|
| flight height | command line | `--alt 40`, `50`, `60` | footprint grows with height: fewer photos, less detail per pixel |
| strip overlap | command line | `--overlap 0.1`, `0.2` (default), `0.4`, `0.6` | photogrammetry needs about 0.6 – cost in time? |
| arrival tolerance | command line | `--tol 0.5`, `1` (default), `2`, `5` m | accuracy against time |
| battery reserve | command line | `--max-time 30`, `60` | when does the reserve fire, where does the drone land? |
| **ground detail** (Assessment 2) | `my_mission.py`, function `plan()` | after the line that starts `footprint =`, add `print('ground sampling distance %.1f cm per pixel' % (100 * footprint / 640))` | the camera is 640 pixels wide: cm on the ground per pixel |
| **predicted vs real time** (Assessment 2) | T2, before the flight | `python3 ~/labs/solutions/week12/preflight.py --alt 40 --length 100 --width 100` prints the predicted survey minutes | compare the prediction with your measured RESULT time, for every height and overlap |

Run your copy with `python3 ~/work/project/my_mission.py --alt … --overlap …`. To add the print line: open
`my_mission.py` in VSCodium, Ctrl+F `footprint =`, put the cursor at the end of that line, press Enter (VSCodium keeps
the indentation), type the line, save.

## 4. Experiments

* **Assessment 1 (Week 6):** "as given" once and the solution at 40 m **3 times**, plus **one sweep**: height
  40 / 50 / 60 m (1 run each). Keep one photo of each height for your report.
* **Assessment 2 (Week 12):** **3 runs** per configuration; height × overlap (at least 3 × 2 configurations), the
  tolerance sweep, and the predicted-vs-measured flight time.

## 5. Results file and figures

Columns: `config, run, date, computer, alt_m, overlap, tol_m, waypoints, photos, time_s, flown_m, worst_miss_m,
footprint_m, gsd_cm_per_px, predicted_min, aborted, notes`.

```bash
python3 ~/labs/projects/tools/plot_results.py ~/work/project/results.csv --metric time_s \
    --ylabel "survey flight time [s]" --out ~/work/project/fig_time.png
```

## 6. Your paper (Assessment 2)

* **Possible title:** *Flight height and image overlap in small-UAV photographic surveys: a software-in-the-loop study
  with PX4 and AirSim.*
* **Contribution:** measured curves of time, distance and ground detail against height and overlap; how well a simple
  flight-time model predicts the real flight; a recommendation for this field.
* **Figures:** AirSim screenshot over the valley; one photo per height side by side; flight time against overlap for
  each height; predicted against measured time.
* **Limits:** simulated camera and physics, no wind, flat-field assumption in the footprint formula (the valley is not
  flat – discuss what that does to real overlap).
