# P5 – Collision avoidance: from a robot's LiDAR safety stop to a car's radar emergency brake

| | Part A – Assessment 1 (Weeks 1–6) | Part B – Assessment 2 (Weeks 7–12) |
|---|---|---|
| You build | a **mobile robot that cannot crash**: a LiDAR safety brick that stops it before a wall, and Nav2 obstacle avoidance round an object dropped in its way. You measure how far it needs to stop at each speed and write your own **safety rule** | a **self-driving car that cannot crash**: adaptive cruise control with a forward radar – keep the speed, keep a safe time gap, brake hard when a crash is close – with the emergency brake set from **your safety rule** |
| Lectures | Week 2 (ROS 2 bricks, the safety stop), Week 3 (Nav2, costmaps, obstacles) | Week 11 (CARLA, radar, PI control, drive-by-wire) |
| Simulator | Gazebo + RViz, Nav2 | CARLA 0.9.15, Town04 |
| Container | `abdulmannan617/tc70045e-ros2:humble` – laptop, no GPU | `abdulmannan617/tc70045e-carla:latest` – NVIDIA GPU (8 GB+): Vast.ai |
| Demo videos (Blackboard) | `TC70045E_Week02_demo.mp4`, `TC70045E_Week03_demo.mp4` | `TC70045E_Week11_demo.mp4` |

**How Part B extends Part A:** in Part A you find, by measurement, how much distance the robot needs to stop at each
speed and turn it into a rule (`safety_rule.csv`). In Part B you scale the same idea up to the car – stopping
distance, reaction time, time-to-collision – set the car's emergency brake from it, and test whether it holds when
the car ahead brakes. In Assessment 2 you compare the robot's rule and the car's.

---

## Part A – the robot that cannot crash (Assessment 1)

### Start (every session)

Laptop: `docker start tc70045e`, <http://localhost:6080>, **Connect**, **Terminator**, `update-labs`, T1–T4. Once:

```bash
mkdir -p ~/work/project && cp ~/labs/projects/P5_collision_avoidance/results_partA.csv ~/labs/projects/P5_collision_avoidance/results_partB.csv ~/work/project/
```

### A1 – the safety stop (Week 2)

| | |
|---|---|
| T1 | `ros2 launch ~/labs/week02/launch/lego.launch.py gui:=true safety:=true` |
| T2 | `python3 ~/labs/week02/scripts/my_brick.py` – publishes the distance to the nearest obstacle |
| T3 | `ros2 topic echo /safety/blocked` |
| T4 | drive straight at the wall at a fixed speed: `ros2 topic pub -r 10 /cmd_vel_in geometry_msgs/msg/Twist "{linear: {x: 0.3}}"` |
| when T3 shows `data: true` and the robot has stopped | a fifth terminal: `ros2 topic echo --once /nearest_obstacle` → the distance it stopped at. Ctrl+C in T4, then restart T1 for the next run |

**Course measurement (6 Oct 2026):** at 0.3 m/s, with the default `stop_distance` 0.45 m, the robot was blocked at
0.38 m from the wall – it needed about 7 cm more than the rule allowed for. Only 0.3 m/s was measured by the course.

| To test… | Change |
|---|---|
| speed | T4: `x: 0.1`, `0.2`, `0.3` (and higher if the robot goes faster) |
| the rule's distance | after the launch: `ros2 param set /safety_stop stop_distance 0.3` (default 0.45; try 0.3 / 0.45 / 0.6) |
| how wide it looks | `ros2 param set /safety_stop half_angle_deg 20.0` (default 35°) – then drive past a corner at an angle |

### A2 – avoiding an obstacle (Week 3)

T1: `ros2 launch ~/labs/week03/launch/nav.launch.py gui:=true` (wait for `AMCL confirmed the start pose`); T2:
`python3 ~/labs/week03/scripts/go_to.py 4.0 -1.0 0` (start → doorway); T3 straight after:
`python3 ~/labs/week03/scripts/drop_box.py 2.0 -1.0` (a box in the way). **Course:** SUCCEEDED in about 14.5 s, round
the box (without the box 14–16 s). Change the safety margin with
`ros2 param set /global_costmap/global_costmap inflation_layer.inflation_radius 0.15` (default 0.35; 0.15 / 0.35 / 0.8)
and the box position (on the path, beside it, in the doorway).

### Your safety rule (required – Part B needs it)

From your A1 runs: the distance the robot travelled after the brick said "blocked" (`stop_distance` − the distance it
stopped at) for each speed. Write `~/work/project/safety_rule.csv` with a header `speed_mps,stop_needed_m` and one
line per speed, then fit a rule – `stop_needed = reaction_time × speed + speed² / (2 × deceleration)` – and give your
reaction time and deceleration in the report.

### Part A experiments (minimum)

The safety stop at three speeds, 3 runs each · `stop_distance` at three values · the obstacle test 3 runs, and one
inflation radius change · your `safety_rule.csv` and fitted rule.

---

## Part B – the car that cannot crash (Assessment 2)

### Start (every session)

1. Rent a GPU machine with the **CARLA** image ([docs/RUN_ON_VAST.md](../../docs/RUN_ON_VAST.md)); note instance,
   price, times. Desktop → terminal → `update-labs`, T1, T2. Copy `safety_rule.csv` and `results_partB.csv` into
   `~/work/project/`. Once: `cp ~/labs/solutions/week11/acc.py ~/work/project/my_acc.py`
2. T1: `carla-sim start --town Town04` – wait for `CARLA is up`.
3. After every run: `cp ~/acc.csv ~/work/project/<config>_run<N>.csv`. **At the end:** download `~/work/project/`,
   then **Destroy** the machine.

### Baseline to reproduce

T2: `python3 ~/labs/week11/scripts/acc.py --show` (as given), then `python3 ~/labs/solutions/week11/acc.py --show`.
The car ahead drives 50 km/h, slows to 25 km/h at 25 s and speeds up again at 45 s. Each run ends with
`RESULT smallest true gap 18.2 m, smallest time gap 2.04 s, smallest radar TTC 2.2 s, speed before the slow-down 50.3 km/h …`.
**Course (15 Oct 2026):** as given – collision at 34 s; solution – 18.2 m, 2.04 s, TTC 2.2 s (two runs); with
`--time-gap 1.0` – 10.5 m, 1.14 s, TTC 1.8 s. After about 60 s a roadside object can fool the radar (a false
target) – note it when you see it.

### The hand-over: your rule in the car, and what to change

In `~/work/project/my_acc.py` (VSCodium, Ctrl+F):

| Your rule says… | Search for | Change |
|---|---|---|
| when to brake hard | `if ttc < 1.5 or gap < 5.0:` | the time-to-collision threshold `1.5` → the value your rule gives at 50 km/h (time = stop distance ÷ closing speed); try also 1.0 / 2.0 / 2.5 |
| the standstill distance | the same line, and `wanted = a.time_gap * kmh / 3.6 + 5.0` | `5.0` → your value (in both places) |
| how far behind to follow | command line | `--time-gap 1.0` / `1.5` / `2.0` / `2.5` / `3.0` (the Highway Code's two-second rule is 2.0) |
| a harder test | Ctrl+F `return 25.0 if 25.0 <= t < 45.0 else 50.0` | first `25.0` → `10.0`: the car ahead brakes much harder |
| how hard the gap rule pulls | `kmh + 1.5 * (gap - wanted)` | `1.5` → `0.5` / `1.0` / `3.0` |

Run with `python3 ~/work/project/my_acc.py --show --time-gap …` (no `--show` on a slow machine). Change one number at a
time; if Python reports an error it names the line – compare with `~/labs/solutions/week11/acc.py`.

### Part B experiments (minimum)

The course ACC 3 runs · your rule in the car 3 runs · the time-gap sweep (5 values, 3 runs each) · the harder test
with and without your rule.

---

## Results and figures

`results_partA.csv`: `config, run, date, computer, speed_mps, stop_distance_m, stopped_at_m, travelled_after_block_m,
inflation_m, box, go_to_result, go_to_s, notes` · `results_partB.csv`: `config, run, date, computer, time_gap_s,
ttc_brake_s, standstill_m, gap_gain, lead_slowdown_kmh, smallest_gap_m, smallest_time_gap_s, smallest_ttc_s,
speed_before_kmh, collision, false_target_seen, log_file, notes`.
`python3 ~/labs/projects/tools/plot_timeseries.py ~/work/project/rule_run1.csv ~/work/project/given_run1.csv --columns speed_kmh,true_gap_m,brake --labels "my rule,course" --out ~/work/project/fig_run.png`

**Paper idea:** *From a LiDAR safety stop to radar emergency braking: a measured stopping rule for a mobile robot,
applied to adaptive cruise control in CARLA.* Figures: the robot stopping at the wall; stop distance against speed
with your fitted rule; the car's speed and gap with your rule and the course's; smallest gap against time gap.
