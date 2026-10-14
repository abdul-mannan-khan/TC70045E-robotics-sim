# Week 09 – Drones without ROS 2: AirSim + PX4, a Survey Flight with Photographs

Weeks 1–8 were a ground robot. From this week the robot is a **quadcopter**. Two programs simulate it: **AirSim**
(the world, the physics, the cameras) and **PX4**, the same autopilot software that runs on a real Pixhawk flight
controller. PX4 keeps the drone in the air; your Python script only tells it **where to go**, over **MAVLink**.
This week there is no ROS 2 at all – plain Python – and you write a survey mission: a lawn-mower pattern over a
field, with a photograph at every waypoint. Next week the same drone becomes a ROS 2 robot; in Week 12 the same
mission flies a real Pixhawk.

**Watch the demo video first:** `TC70045E_Week09_demo.mp4` in the Week 9 folder on Blackboard. It shows every step
below, with the AirSim window (the simulated world) and the terminals side by side.

| Time in class | Part |
|---|---|
| 45 min | lecture: autopilot and links, NED, survey planning; ESCs and motors; testing PWM and UART/MAVLink |
| 10 min | Step 0 – start the drone container |
| 45 min | Activities A1–A3 |
| 70 min | Your activity (the TODO) – finish `mission.py` |

---

## Step 0 – Start the drone container (once per session)

The drone simulator needs an **NVIDIA GPU** (6 GB or more). It is a different container from Weeks 1–8:

* **Your own computer has one** (Linux, NVIDIA driver installed): the first time,
  ```bash
  docker run -d --name tc70045e-drone --gpus all -p 6081:80 --shm-size 4g --security-opt seccomp=unconfined \
      -e USER=ubuntu -e RESOLUTION=1600x900 abdulmannan617/tc70045e-drone:latest
  ```
  (10.7 GB download), afterwards `docker start tc70045e-drone`. Browser: <http://localhost:6081>.
* **No NVIDIA GPU:** rent one for about $0.10–0.20 an hour – [docs/RUN_ON_VAST.md](../docs/RUN_ON_VAST.md). Still
  *Loading* after 30 minutes? Destroy it and rent a different machine. **Destroy** it when you finish.

In the desktop open a terminal, run `update-labs`, and split it into three (T1, T2, T3).
Check: `ls ~/labs/week09/scripts` lists `01_hello_airsim.py  02_fly_square_mavsdk.py  mission.py`.

**Start the simulator (T1):**

```bash
drone-sim start --world blocks        # blocks: light; also neighborhood (a town), mountains (fly higher there)
drone-sim status                      # AirSim running, PX4 running, API port answering, GPU visible
```

`drone-sim start` prints `PX4 SITL is ready for take-off` when it is ready (about a minute). **Before every new
start:** `drone-sim stop`. A script that hangs at "waiting for the autopilot": `drone-sim stop`, `drone-sim start` again.

## The scripts this week

| Script | Link | What it does |
|---|---|---|
| [`scripts/01_hello_airsim.py`](scripts/01_hello_airsim.py) | AirSim API (TCP 41451) | prints position, attitude, IMU and GPS; saves (and with `--show` shows) the front camera |
| [`scripts/02_fly_square_mavsdk.py`](scripts/02_fly_square_mavsdk.py) | MAVLink (UDP 14550) | arm, take off, a square of position set-points, land |
| [`scripts/mission.py`](scripts/mission.py) | both | **your activity**: plan a lawn-mower survey, fly it, one photo per waypoint (`~/survey/`), fly home in time. Three TODOs |

Frames: AirSim and PX4 use **NED** – x north, y east, z **down**, from the take-off point. 20 m up is `z = -20`.

---

## A1 – Hello AirSim: read the sensors (15 min)

**Goal:** talk to the simulator directly, through the AirSim API – no autopilot involved.

| | |
|---|---|
| T1 | `drone-sim start --world blocks` – wait for `PX4 SITL is ready for take-off` |
| T2 | `python3 ~/labs/week09/scripts/01_hello_airsim.py --show` |

**You should see:** `Connected!`, then the drone's position, attitude, IMU and GPS, and the front camera picture
(saved as `~/airsim_front.png`). Measured on the ground: `position NED x -0.00 y 0.00 z -0.07 m`,
`IMU accel 0.05 0.01 -9.87 m/s^2`, `GPS lat 47.641468 lon -122.140165`, a 640 × 480 colour picture. **Check:** why is
the IMU's z about −9.87 m/s² when the drone is standing still? (It measures the push of the ground against gravity –
and z points **down** in NED.)

## A2 – Fly a square through the autopilot (15 min)

**Goal:** fly over MAVLink: your script sends position set-points, PX4 does the flying.

| | |
|---|---|
| T2 | `python3 ~/labs/week09/scripts/02_fly_square_mavsdk.py --side 5 --alt 5` |

**You should see:** in T2 `connected`, `taking off to 5.0 m`, `airborne at 4.5 m`, four `-> corner …` lines,
`square done - landing`, `landed`; in the AirSim window the drone flies a 5 m square at 5 m. **Check:** the script
asks for a corner at `north 5.0 m, east 0.0 m` – what z does it send for 5 m up? (−5: NED.)

## A3 – The survey as given (17 min)

**Goal:** run `mission.py` before you change it, and see what is wrong.

| | |
|---|---|
| T2 | `python3 ~/labs/week09/scripts/mission.py --alt 40 --length 100 --width 100` |
| T3 | `ls ~/survey` – one photo per waypoint |

**You should see:** `plan: footprint 10.0 m, row spacing 10.0 m, 22 waypoints`, 22 photos – but every waypoint after
the first `MISSED`, and the RESULT line: `complete: 39 s, 5 m flown, 22 photos, worst waypoint miss 136.86 m`
(measured). Open the photos: they all show the take-off point. **Check:** which two things are wrong? (The plan:
10 m strips from 40 m up; and the drone never waits to arrive.) Fly at 40 m: the *blocks* world has no obstacle
avoidance, and at 20 m our test drone hit a block on the third row.

---

## Your activity (the TODO) – finish mission.py (70 min)

**What you build:** a survey that is planned from the camera geometry, flown waypoint by waypoint, and stopped in
time to fly home.

1. **Open** `~/labs/week09/scripts/mission.py`. Three TODOs:
   * **TODO 1 – the plan (`plan()`):** how wide is the strip of ground the down camera sees from `alt` metres with a
     `CAMERA_FOV_DEG` (90°) lens? And how far apart must the rows be so that neighbouring strips overlap by
     `overlap` (0.2 = 20 %)? Lecture: strip = 2 h tan(FOV/2), spacing = strip × (1 − overlap).
   * **TODO 2 – arrival (`goto()`):** as given it "arrives" at once. Use `d` (the horizontal distance to the
     waypoint), `tol` and the timeout.
   * **TODO 3 – battery reserve (the waypoint loop):** if the survey has taken longer than `a.max_time` seconds,
     stop and fly home.
2. **Run** after each TODO, as in A3, and keep the RESULT line:
   `python3 ~/labs/week09/scripts/mission.py --alt 40 --length 100 --width 100`
3. **Test the reserve** with a small limit, e.g. `--max-time 20`.
4. **Done when** – all three are true:
   * at 40 m the plan prints `footprint 80.0 m, row spacing 64.0 m, 6 waypoints`;
   * every waypoint is `reached` (within 1 m) and the six photos show different parts of the field;
   * a low `--max-time` prints `time limit … reached`, the RESULT says `ABORTED (time limit)`, and the drone lands
     at the start.

### Solution (compare after you have tried)

[`../solutions/week09/mission.py`](../solutions/week09/mission.py):
`footprint = 2.0 * alt * math.tan(math.radians(CAMERA_FOV_DEG / 2.0))`, `spacing = footprint * (1.0 - overlap)`;
`if d < tol or time.monotonic() - t0 > timeout:`; `if time.monotonic() - start > a.max_time:`.

Measured 14 Oct 2026 (simulated, *blocks* world, 40 m, 100 × 100 m field):

| Code | waypoints | flown | photos | worst waypoint miss | time |
|---|---|---|---|---|---|
| as given | 22 | 5 m | 22 | 136.86 m | 39 s |
| TODO 1 – the plan | 6 | 0 m | 6 | 141.27 m | 38 s |
| TODO 1 + 2 – arrival | 6 | 535 m | 6 | 0.98 m | 89 s |
| **solution**, four runs | 6 | 535 m | 6 | 0.98 – 1.00 m | 89 s |

What the numbers say:
* **TODO 1 cuts 22 waypoints to 6:** from 40 m a 90° camera sees an 80 m strip, so rows 64 m apart still overlap by
  20 %. Wrong geometry means four times the flying for the same field.
* **TODO 2 makes the drone actually fly the plan:** without it the photos are all taken within a few metres of the
  start; with it every waypoint is reached within 1 m and the six photos cover the field.
* **TODO 3 did not fire with `--max-time 40` or `90`** in our runs: the drone had already started the last row, and the
  89 s include flying home and landing. Use a smaller limit to see it stop the survey.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `waiting for the autopilot on udpin://0.0.0.0:14550` for more than a minute | PX4 is not running or not ready: `drone-sim status`; if needed `drone-sim stop`, `drone-sim start --world blocks` |
| `offboard failed: …` | the drone was not airborne yet or PX4 rejected the mode: land (`drone-sim stop` / `start`) and run again |
| `drone-sim start`: "waiting for the previous simulation to release port 4560" | normal after a stop: it waits up to 90 s |
| The simulator window is black / very slow | no GPU in the container: `nvidia-smi` must list the GPU (`--gpus all`) |
| The photos are all the same | TODO 2: the drone "arrives" at once, so every photo is taken just after take-off |

Hardware: the same `mission.py` flies a real Pixhawk 6C with AirSim simulating the world – Week 12 and
[docs/HIL_JETSON_PIXHAWK.md](../docs/HIL_JETSON_PIXHAWK.md).
