# Week 11 – Self-Driving Car: CARLA, Radar and Adaptive Cruise Control

The third kind of robot in the module: a car. **CARLA** simulates the town, the traffic, the car's physics and its
sensors. First you drive a car with a cruise control – throttle and brake from a PI controller – through the CARLA
API and then through ROS 2. Then you build **adaptive cruise control** (ACC): a forward **radar** measures the gap to
the car ahead and how fast it is closing, and your controller keeps the speed, keeps a safe gap and brakes hard if a
collision is near.

**Watch the demo video first:** `TC70045E_Week11_demo.mp4` in the Week 11 folder on Blackboard.

| Time in class | Part |
|---|---|
| 45 min | lecture: the car as a robot, FMCW radar, the three ACC rules, throttle-, brake- and steer-by-wire |
| 10 min | Step 0 – start the CARLA container |
| 55 min | Activities A1–A3 |
| 70 min | Your activity (the TODO) – finish `acc.py` |

---

## Step 0 – Start the CARLA container (once per session)

CARLA needs an **NVIDIA GPU with 8 GB or more**. It is a third container:

* **Your own computer has one** (Linux, NVIDIA driver installed): the first time,
  ```bash
  docker run -d --name tc70045e-carla --gpus all -p 6082:80 --shm-size 4g --security-opt seccomp=unconfined \
      -e USER=ubuntu -e RESOLUTION=1600x900 abdulmannan617/tc70045e-carla:latest
  ```
  afterwards `docker start tc70045e-carla`. Browser: <http://localhost:6082>.
* **No NVIDIA GPU:** rent one – [docs/RUN_ON_VAST.md](../docs/RUN_ON_VAST.md) (image `abdulmannan617/tc70045e-carla:latest`,
  80 GB disk; 12 GB of GPU memory is comfortable). **Destroy** it when you finish.

In the desktop open a terminal, run `update-labs`, and split it into three (T1, T2, T3).
Check: `ls ~/labs/week11/scripts` lists `01_hello_carla.py  02_cruise_control_api.py  03_cruise_control_ros2.py  acc.py  carla.rviz`.

**Start the simulator (T1):** `carla-sim start --town Town04`, then `carla-sim status`. The CARLA server has no
window: you watch through your script's camera window (`--show`) or RViz. Always connect to `127.0.0.1`, never
`localhost`.

## The scripts this week

| Script | What it does |
|---|---|
| [`scripts/01_hello_carla.py`](scripts/01_hello_carla.py) | a car driving itself, seen through a chase camera |
| [`scripts/02_cruise_control_api.py`](scripts/02_cruise_control_api.py) | a PI cruise control through the CARLA API (no ROS 2); writes `~/cruise_api.csv` |
| [`scripts/03_cruise_control_ros2.py`](scripts/03_cruise_control_ros2.py) | the same controller as a ROS 2 node, through the CARLA ROS 2 bridge |
| [`scripts/acc.py`](scripts/acc.py) | **your activity**: radar, a lead car that slows from 50 to 25 km/h and back, three TODOs; writes `~/acc.csv` |
| [`scripts/carla.rviz`](scripts/carla.rviz) | RViz: camera, LiDAR, odometry from the bridge |

---

## A1 – Hello CARLA (15 min)

**Goal:** a car in the simulator, driving itself, and a camera to watch it.

| | |
|---|---|
| T1 | `carla-sim start --town Town04` – wait for `CARLA is up` |
| T2 | `python3 ~/labs/week11/scripts/01_hello_carla.py` |

**You should see:** `spawned vehicle.tesla.model3 on Town04 - autopilot on`, a chase-camera window, and the speed every
second (measured: about 29 km/h on CARLA's autopilot; with `--headless` there is no window and a picture is saved
as `~/carla_chase.png`). **Check:** the script
runs CARLA in *synchronous mode* (one world step of 0.05 s per `tick()`) – why does that make every run the same?

## A2 – Your cruise control through the CARLA API (20 min)

**Goal:** close the loop yourself: speed in, throttle and brake out, no ROS 2.

| | |
|---|---|
| T2 | `python3 ~/labs/week11/scripts/02_cruise_control_api.py --target 50 --show` |
| T2 | `python3 ~/labs/week11/scripts/02_cruise_control_api.py --target 50 --ki 0` – the P term alone |

**You should see:** the speed climb to 50 km/h and stay there, then
`RESULT last 10 s: mean 50.0 km/h, max error 0.1 km/h (target 50)` (measured). With `--ki 0`: `mean 46.8 km/h,
max error 3.4 km/h` – a steady error. **Check:** why does the P term alone stop short of 50? (Holding a speed needs
some throttle, and a P controller only gives throttle while there is an error.)

## A3 – The same controller as a ROS 2 node (20 min)

**Goal:** run the cruise control as an ordinary ROS 2 node, through the official CARLA ROS 2 bridge.

| | |
|---|---|
| T2 | `ros2 launch carla_ros_bridge carla_ros_bridge_with_example_ego_vehicle.launch.py host:=127.0.0.1 timeout:=60 town:=Town04 synchronous_mode:=true spawn_point_ego_vehicle:="-365.9,-33.6,0.8,0,0,0.4"` |
| T3 | `rviz2 -d ~/labs/week11/scripts/carla.rviz`, then `ros2 topic list \| grep ego_vehicle` |
| T3 | `python3 ~/labs/week11/scripts/03_cruise_control_ros2.py --ros-args -p target_kmh:=50.0` |

**You should see:** a manual-control window and 31 topics under `/carla/ego_vehicle` (camera, LiDAR, radar, GNSS, IMU,
odometry, speedometer, `vehicle_control_cmd` …); the node logs its speed every second – measured: 0 → 55 km/h peak
→ 50.0 km/h. Stop the bridge with Ctrl+C before the next part. **Check:** the spawn point says `-33.6`, the API scripts
`33.6` – why? (CARLA's y axis points the other way from ROS; the bridge flips it.)

---

## Your activity (the TODO) – finish acc.py (70 min)

**What you build:** adaptive cruise control – keep the set speed, keep a safe time gap to the car ahead, and brake
hard if a collision is near. The lead car drives 50 km/h, slows to 25 km/h at t = 25 s and speeds up again at 45 s.

1. **Run it as given:** `python3 ~/labs/week11/scripts/acc.py --show`. A plain P speed controller that ignores the
   radar: it runs into the car ahead.
2. **Open [`scripts/acc.py`](scripts/acc.py).** Three TODOs:
   * **TODO 1 – PI speed loop:** add the I term: `integral += err * DT`, clamped to [−50, 50] (anti-windup), and
     `u = kp * err + ki * integral`.
   * **TODO 2 – gap rule:** the wanted gap is `time_gap × own speed (m/s) + 5 m`. When the radar gap is smaller (plus
     a margin), lower `target` below the set speed – e.g. own speed + a gain × (gap − wanted) – so the gap opens again.
   * **TODO 3 – safety:** time-to-collision `ttc` below 1.5 s, **or** a radar gap below the 5 m standstill distance:
     full brake (throttle 0, brake 1) whatever TODO 1 and 2 say, and reset the integral. Why the gap too? Close behind
     a car at the same speed the TTC is "infinite" – and the speed loop would accelerate into it again.
3. **Run it after each TODO** and keep the `RESULT` line and `~/acc.csv`.
4. **Done when** – all three are true:
   * no collision: the smallest gap is well above 0 m, the smallest time gap close to your `--time-gap` (2 s);
   * about 50 km/h before the slow-down (the I term);
   * a plot from `~/acc.csv` – own speed, lead speed and gap against time – for the given version and for yours.

### Solution (compare after you have tried)

[`../solutions/week11/acc.py`](../solutions/week11/acc.py): TODO 1 as above; TODO 2
`wanted = a.time_gap * kmh / 3.6 + 5.0`, `if gap < wanted + 20.0: target = min(target, max(0.0, kmh + 1.5 * (gap - wanted)))`;
TODO 3 `if ttc < 1.5 or gap < 5.0: throttle, brake, integral = 0.0, 1.0, 0.0`.

Measured 15 Oct 2026 (simulated, CARLA 0.9.15, Town04, 70 s):

| acc.py | speed before the slow-down | smallest gap | smallest time gap | smallest radar TTC |
|---|---|---|---|---|
| as given (P only) | 46.6 km/h | **−0.8 m – collision** at 34 s | – | 0.0 s |
| + TODO 1 (PI) | 50.4 km/h | **−0.9 m – collision** | – | 0.1 s |
| + TODO 1 and 3 (no gap rule) | 50.4 km/h | 2.7 m | 0.35 s | 1.0 s |
| + TODO 1 and 2 | 50.3 km/h | 18.2 m | 2.05 s | 2.2 s |
| **all three (solution)**, two runs | 50.3 km/h | **18.2 m** | **2.04 s** | 2.2 s |
| solution, `--time-gap 1.0` | 50.4 km/h | 10.5 m | 1.14 s | 1.8 s |

What the numbers say:
* **The I term makes the speed right, not the car safe:** with TODO 1 alone it holds 50 km/h – and still hits the car
  ahead.
* **The gap rule keeps the distance; the brake is the safety net.** With TODO 2 the brake was never needed (smallest
  TTC 2.2 s); without TODO 2 the brake alone avoided the crash with only 2.7 m to spare. Our first version of TODO 3
  (TTC only) still crashed: it released the brake as soon as both cars had the same speed, 1 m apart.
* **A radar sees more than cars.** Our first radar filter took the road surface 20 m ahead for a car, and the ACC
  crawled at 27 km/h; it now keeps only reflections at least 0.3 m above the road. After about 60 s the road bends and a
  roadside object inside the beam slows the car briefly – a false target, exactly the weakness of radar in the lecture.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `time-out of 30000ms while waiting for the simulator` | CARLA is still starting (up to a minute): `carla-sim status`; connect to `127.0.0.1`, not `localhost` |
| After a script crashed, the next one hangs at the start | the crashed script may have left CARLA in synchronous mode (waiting for ticks): `carla-sim stop`, `carla-sim start --town Town04` |
| `--show` window black | the first frames take a few seconds; no GPU in the container: `nvidia-smi` must list it |
