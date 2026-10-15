# Week 12 – Hardware in the Loop: from Simulation to a Real Autopilot (A2 due)

In Weeks 9 and 10 the autopilot was a program: PX4 running inside the drone container (**software in the loop**,
SITL). This week the same mission meets real hardware. In **hardware in the loop** (HIL) a real **Pixhawk 6C**
flight controller runs PX4, a **Jetson Orin Nano Super** is its companion computer, and AirSim still simulates the
world. The lecturer demonstrates HIL; you work in SITL on the same software. Your activity is the software's
"bring-up test": a **pre-flight check** that decides whether the mission may fly. The second half of the session is
for your **A2 report**.

**Watch the demo video first:** `TC70045E_Week12_demo.mp4` in the Week 12 folder on Blackboard.

| Time in class | Part |
|---|---|
| 35 min | lecture: SITL / HIL / real flight; from wiring to an interface board; testing a new board |
| 10 min | lecturer demo: hardware in the loop |
| 7 min | Step 0 – start the drone container |
| 48 min | A1, then your activity (the TODO) and A3 |
| 8 min | break |
| 72 min | A2 report sprint |

---

## Step 0 – Start the drone container (once per session)

Exactly as in Week 9 ([week09/README.md](../week09/README.md#step-0--start-the-drone-container-once-per-session)):
`docker start tc70045e-drone` (or a rented GPU, [docs/RUN_ON_VAST.md](../docs/RUN_ON_VAST.md)), open the desktop,
`update-labs`, split the terminal into three (T1, T2, T3).
Check: `ls ~/labs/week12/scripts` lists `preflight.py`.

## Hardware in the loop (the lecturer demo)

How the Pixhawk 6C, the Jetson and the GPU computer are connected, set up and tested:
[docs/HIL_JETSON_PIXHAWK.md](../docs/HIL_JETSON_PIXHAWK.md). The mission code is the same in all three set-ups –
only its MAVLink address changes:

| Set-up | Autopilot | Mission code runs on | MAVLink address (`--url`) |
|---|---|---|---|
| SITL (your laptop / rented GPU) | PX4 program in the drone container | the drone container | `udpin://0.0.0.0:14550` |
| HIL (lecturer demo) | Pixhawk 6C | the Jetson | `serial:///dev/ttyTHS0:921600` |
| Real flight (outside this module) | Pixhawk 6C | the Jetson | `serial:///dev/ttyTHS0:921600` |

---

## The bricks this week

| Brick / file | What it does |
|---|---|
| [`scripts/preflight.py`](scripts/preflight.py) | listens to the autopilot for 10 s (`--seconds`) and checks link, sensor health, GPS and battery; prints one PASS / FAIL line per check and a verdict, **GO** (exit code 0) or **NO-GO** (exit code 1). **Your activity** has three TODOs in this file |
| [`scripts/inject_fault.py`](scripts/inject_fault.py) | makes a sensor of the **simulated** autopilot fail (`--sensor gps --type off`) and undoes it (`--type ok`) – PX4 failure injection, for A3 |
| `../week09/scripts/mission.py` | your Week 9 survey mission, unchanged |

---

## A1 – The Week 9 mission, once more in SITL (10 min)

**Goal:** check that the simulated autopilot flies before you test it.

| | |
|---|---|
| T1 | `drone-sim start --world mountains` – the valley of the Week 9 survey; then wait about a minute for PX4's first GPS fix |
| T2 | `python3 ~/labs/week09/scripts/mission.py` (your Week 9 survey: 40 m, 100 × 100 m) |

**You should see:** the same survey over the mountain valley as in Week 9. Measured with the Week 9 solution:
6 waypoints reached, worst miss 0.99 – 1.00 m, 89 s, 535 m, 6 photos, landed. This is the set-up of the lecturer's HIL demo – with the PX4 program in place of the
Pixhawk 6C.

---

## Your activity (A2, the TODO) – a pre-flight check that can say no (28 min)

**What you build:** a go / no-go check that stops the mission when something is wrong.

1. **Run it as given:** `python3 ~/labs/week12/scripts/preflight.py` (default survey: the Week 9 one, 40 m, 100 × 100 m). It says GO –
   but look at the link line: `0.0 per s (need 5)  PASS`, and the battery needs `0 %`. As given, three of the four
   checks pass anything; only the autopilot's own health flags are real.
2. **Three TODOs in `preflight.py`:**
   * **TODO 1 – GPS:** pass only with a 3D fix or better (`FIX_3D`, `FIX_DGPS`, `RTK_FLOAT`, `RTK_FIXED`) **and** at
     least `--min-sats` satellites (8). `g` is `None` if no GPS message arrived at all.
   * **TODO 2 – battery:** the survey needs its flight time (`survey_minutes(...)`) × `USE_PER_MIN`, plus the reserve
     (`--reserve`, 30 %) you want left on landing.
   * **TODO 3 – link:** position messages per second (`seen['positions']` in `--seconds`), at least `--min-rate` (5). A
     wrong baud rate or a loose cable shows here first.
3. **Test it:** `python3 ~/labs/week12/scripts/preflight.py`, then
   `python3 ~/labs/week12/scripts/preflight.py --length 1000 --width 1000`.
4. **Done when** – all three are true:
   * GO for the small survey, with a measured value on every line (link about 50 per s);
   * NO-GO for the 1 × 1 km survey, failed on the battery line;
   * your table: as given / your solution × (link, GPS, battery needed, verdict).

## A3 – Break the GPS, then try to fly (10 min)

**Goal:** show that your check keeps a drone with a faulty sensor on the ground.

| | |
|---|---|
| T2 | `python3 ~/labs/week12/scripts/inject_fault.py --sensor gps --type off` – wait about 15 s |
| T2 | `python3 ~/labs/week12/scripts/preflight.py && python3 ~/labs/week09/scripts/mission.py` |
| T2 | `python3 ~/labs/week12/scripts/inject_fault.py --sensor gps --type ok` – wait about 20 s, run `preflight.py` again |

**You should see:** NO-GO with the GPS off – the GPS line shows `NO_GPS` – and, because of `&&`, the mission never
takes off. After `--type ok`: GO again – but `drone-sim stop` and start again before the next flight: in our
test a survey started straight after the GPS came back missed three of six waypoints by 140 – 191 m, because PX4's
position estimate had not settled. The pre-flight check said GO; it can only test what it measures. **Failure injection is for the simulator only – never on a drone that is going
to fly.**

### Solution (compare after you have tried)

[`../solutions/week12/preflight.py`](../solutions/week12/preflight.py):
`rate = seen['positions'] / a.seconds`, pass if `rate >= a.min_rate` ·
`good_fix = g is not None and g.fix_type in (FIX_3D, FIX_DGPS, RTK_FLOAT, RTK_FIXED)`, pass if
`good_fix and sats >= a.min_sats` · `need = survey_minutes(a.length, a.width, a.alt, a.overlap) * USE_PER_MIN + a.reserve`.

Measured 15 Oct 2026 (simulated, PX4 SITL, *mountains* world, the Week 9 survey: 40 m, 100 × 100 m):

| Run | Link | GPS | Battery needed | Verdict |
|---|---|---|---|---|
| as given, healthy | 0.0 per s – PASS | FIX_3D, 15 satellites – PASS | 0 % – PASS | GO |
| **solution, healthy** | 50.0 per s – PASS | FIX_3D, 15 satellites – PASS | 37 % (3.0 min survey + 30 %) – PASS | **GO** |
| solution, 1 × 1 km survey | 50.0 per s – PASS | FIX_3D, 15 satellites – PASS | **195 %** (65.9 min survey + 30 %) – FAIL | **NO-GO** |
| as given, GPS off | 0.0 per s – PASS | NO_GPS, 255 satellites – **PASS** | 0 % – PASS | NO-GO (health flags only) |
| **solution, GPS off** | 0.0 per s – FAIL | NO_GPS – FAIL | 37 % – PASS | **NO-GO**, exit code 1, mission not started |
| solution, GPS back | 50.0 per s – PASS | FIX_3D, 15 satellites – PASS | 37 % – PASS | GO |

What the numbers say:
* **As given, the check would have let a broken drone fly** – but for PX4's own health flags. No position messages,
  no GPS (255 satellites means "unknown") and no battery budget all said PASS.
* **The solution fails each fault on its own line**, so the log says *why* the drone stayed on the ground.
* **The battery check is only as good as `USE_PER_MIN`.** SITL drains slowly; measure it for your own drone.
* **A check must also finish.** Our first version printed NO-GO with the GPS off and then hung (MAVSDK kept waiting);
  re-tested 15 Oct 2026, every NO-GO now ends at once with exit code 1, so `&&` keeps the mission on the ground.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `preflight.py` waits at "waiting for the autopilot" | PX4 is not running: `drone-sim status`; `drone-sim stop`, `drone-sim start --world mountains` |
| `sensors: autopilot health  FAIL  not ok: global_position_ok, home_position_ok` straight after the start | PX4 needs about a minute for its first GPS fix: wait and run again |
| `inject_fault.py`: `setting SYS_FAILURE_EN failed (TIMEOUT)` | PX4 missed the parameter request (we saw it in 2 of 5 runs). The script tries 5 times; if it still fails, run it again – a later run worked every time |
| After A3 nothing passes any more | the fault is still injected: `drone-sim stop` and start again |

Optional extra from the previous course: [`multi_robot_extra/`](multi_robot_extra/) (two robots on one network,
QoS, clock skew, fault injection).
