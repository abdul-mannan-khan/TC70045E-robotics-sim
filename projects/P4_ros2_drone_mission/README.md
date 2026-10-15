# P4 – A ROS 2 drone mission: speed, accuracy and a safety watchdog

**Question:** a quadcopter controlled from ROS 2 flies a square over a town and photographs the middle at every
corner. How do the cruise speed, the "arrived" radius and the "hover still" threshold trade mission time against
waypoint accuracy and photo sharpness – and how quickly must a watchdog react when a sensor stream dies?

| | |
|---|---|
| Sensors → actuators | odometry, front camera (through ROS 2 topics) → velocity commands → PX4 autopilot → four motors |
| Simulator | AirSim (town world) + PX4 1.14 + two ROS 2 bridge nodes + RViz |
| Container | `abdulmannan617/tc70045e-drone:latest` – **needs an NVIDIA GPU**: rent one on Vast.ai |
| Starts from | [Week 10](../../week10/README.md) – demo video `TC70045E_Week10_demo.mp4` on Blackboard ([Week 9](../../week09/README.md) first, to meet AirSim) |
| You change | one line of numbers at the top of a Python file; later one or two more lines |

## What you will learn

Renting a GPU computer on Vast.ai · AirSim, PX4 and how ROS 2 bridges connect them · ROS 2 nodes, topics, services
and RViz for a flying robot · body frame and map frame · why every wait for sensor data needs a time limit
(watchdogs) · measuring accuracy and photo quality.

## 1. Start (every session)

1. Rent a GPU machine with the **drone** image – [docs/RUN_ON_VAST.md](../../docs/RUN_ON_VAST.md) (about
   $0.10–0.20 per hour, 80 GB disk). Note the instance number, price and start time.
2. Open its desktop, open a terminal, `update-labs`, split it into four (T1–T4).
3. T1: `drone-sim start --world neighborhood` (wait for `PX4 SITL is ready for take-off`)
4. T2: `python3 ~/labs/week10/scripts/03_airsim_ros2_bridge.py` · T3: `python3 ~/labs/week10/scripts/04_px4_ros2_bridge.py`
   (wait until it reports the connection) · optional: `rviz2 -d ~/labs/week10/scripts/airsim.rviz`
5. Once per machine: `mkdir -p ~/work/project && cp ~/labs/solutions/week10/mission_node.py ~/work/project/my_mission_node.py`
   and `cp ~/labs/projects/P4_ros2_drone_mission/results_template.csv ~/work/project/results.csv`.
6. **At the end:** download `~/work/project/` and `~/mission/`, then **Destroy** the machine.

## 2. The baseline you reproduce (Assessment 1)

T4: `python3 ~/labs/week10/scripts/mission_node.py` (as given), then `python3 ~/labs/solutions/week10/mission_node.py`
(solution). The node takes off to 15 m, flies the 10 m square, saves `~/mission/wp01.png` … `wp04.png`, lands and
prints `RESULT 34 s, 39.1 m flown, worst waypoint miss 0.42 m, finished 0.10 m from the start`.

**Course measurements (15 Oct 2026):** as given – waypoint 1 never reached, lands 17 m from the start; solution –
4 of 4 waypoints in 34 s, worst miss 0.42 – 0.47 m, 0.10 – 0.19 m from the start at the end (two runs).
Watchdog test (Ctrl+C in T2 while flying): without the watchdog the drone flew on stale data for a minute; with it,
it printed `WATCHDOG: no odometry for 1 s - landing now` and landed at once.

## 3. Where to edit, and how

Open `~/work/project/my_mission_node.py` in VSCodium and Ctrl+F for the text in the second column.

| To test… | Search for | Change | What to think about |
|---|---|---|---|
| cruise speed | `SPEED, TOL, STILL = 2.0, 0.5, 0.2` | first number: `1.0`, `2.0`, `3.0`, `4.0` m/s | faster = shorter mission – overshoot? |
| arrival radius | same line | second number: `0.25`, `0.5`, `1.0` m | accuracy against time |
| "still" before a photo | same line | third number: `0.1`, `0.2`, `0.5` m/s | sharper photo against waiting time |
| a bigger or different route | `WAYPOINTS = [` | e.g. a 20 m square: `[(20.0, 0.0), (20.0, 20.0), (0.0, 20.0), (0.0, 0.0)]` (x east, y north, metres) | stay over the streets at 15 m |
| watchdog delay (Assessment 2) | `return time.monotonic() - self.t_odom < 1.0` | `1.0` → `0.3`, `0.5`, `2.0`, `5.0` s; then Ctrl+C in T2 during the flight | distance flown blind, and where it lands. (The printed message still says "1 s" – it is fixed text; change it too if you like) |
| **advanced:** fly on the autopilot's estimate instead of the simulator's truth | `'/drone/odom', self.on_odom` | `'/drone/odom'` → `'/drone/px4/odom'` | a real drone has no "truth": how much worse? **Not tested by the course – agree it with the module leader first** |

Run your copy in T4: `python3 ~/work/project/my_mission_node.py`. Change one number at a time, keep the commas and
brackets, save, run. If Python reports a `SyntaxError`, the message gives the line number – compare it with the
original in `~/labs/solutions/week10/`.

**Photo sharpness**, after each run (copy the four numbers into your results):
`python3 ~/labs/projects/tools/sharpness.py ~/mission/wp*.png` – a higher number means sharper edges. Compare runs
of the same route only.

## 4. Experiments

* **Assessment 1 (Week 6):** as given once, the solution **3 times**, the watchdog test once, plus **one sweep**:
  `SPEED` 1 / 2 / 3 m/s (1 run each).
* **Assessment 2 (Week 12):** **3 runs** per configuration; at least **two factors** (e.g. `SPEED` and `STILL`), and
  the **watchdog-delay** experiment (3 values, the bridge stopped at the same point of the mission each time, e.g.
  just after the line for waypoint 2 appears in T4).

## 5. Results file and figures

Columns: `config, run, date, computer, speed_mps, tol_m, still_mps, watchdog_s, waypoints_reached, photos,
time_s, flown_m, worst_miss_m, end_from_start_m, sharpness_mean, watchdog_fired, notes`.

```bash
python3 ~/labs/projects/tools/plot_results.py ~/work/project/results.csv --metric worst_miss_m \
    --ylabel "worst waypoint miss [m]" --out ~/work/project/fig_miss.png
```

## 6. Your paper (Assessment 2)

* **Possible title:** *Speed, accuracy and data-freshness watchdogs for ROS 2 waypoint missions on a PX4 multirotor:
  a software-in-the-loop study.*
* **Contribution:** measured trade-off curves (time against miss distance and photo sharpness) and a justified choice
  of watchdog delay, with the risk of each setting explained.
* **Figures:** AirSim + RViz screenshot; miss distance against speed; sharpness against the "still" threshold; a
  sketch of the ROS 2 graph (`rqt_graph`).
* **Limits:** no wind, a simulated camera, a simulator-truth odometry topic (unless you did the advanced test).
