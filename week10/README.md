# Week 10 – Drones with ROS 2: the Drone as a ROS 2 Robot

Last week you flew the drone in plain Python. This week two small **bridge nodes** turn it into a ROS 2 robot like
the one in Weeks 1–8: one bridge publishes AirSim's camera, odometry, IMU, GPS and TF as ROS 2 topics; the other
takes ordinary ROS 2 commands (`/drone/cmd_vel`, `/drone/takeoff`, `/drone/land`) and passes them to the PX4
autopilot. Then you write a mission as an ordinary ROS 2 node: fly a square, face the middle, take a sharp photo at
each corner – and land on its own if its data stops.

**Watch the demo video first:** `TC70045E_Week10_demo.mp4` in the Week 10 folder on Blackboard. It shows every step
below, with the AirSim window and RViz side by side.

| Time in class | Part |
|---|---|
| 45 min | lecture: bridges, the four frames (NED/FRD, ENU/FLU), map error → body command, fresh data |
| 10 min | Step 0 – start the drone container |
| 55 min | Activities A1–A3 |
| 70 min | Your activity (the TODO) – finish `mission_node.py` |

---

## Step 0 – Start the drone container (once per session)

Exactly as in Week 9 ([week09/README.md](../week09/README.md#step-0--start-the-drone-container-once-per-session)):
`docker start tc70045e-drone` (or a rented GPU, [docs/RUN_ON_VAST.md](../docs/RUN_ON_VAST.md)), open the desktop,
`update-labs`, split the terminal into three (T1, T2, T3) – this week you need a fourth (T4) too.

> **Drone and CARLA images:** they have no `update-labs` yet. The first time on a new machine, paste this line instead – it installs `update-labs` from GitHub and runs it:
> ```bash
> command -v update-labs >/dev/null || curl -fsSL https://raw.githubusercontent.com/abdul-mannan-khan/TC70045E-robotics-sim/main/docker/update-labs | sudo tee /usr/local/bin/update-labs >/dev/null && sudo chmod 755 /usr/local/bin/update-labs; update-labs
> ```

Check: `ls ~/labs/week10/scripts` lists `03_airsim_ros2_bridge.py  04_px4_ros2_bridge.py  05_fly_square_ros2.py  airsim.rviz  mission_node.py`.

## The bricks this week

| Brick | What it does |
|---|---|
| `drone-sim start --world neighborhood` | AirSim + PX4 in the town world, as in Week 9 A1 and A2 |
| [`scripts/03_airsim_ros2_bridge.py`](scripts/03_airsim_ros2_bridge.py) | AirSim → ROS 2: `/drone/front/image_raw`, `/drone/odom` (the simulator's truth), `/drone/imu`, `/drone/gps/fix`, TF `map → base_link`. Converts NED → ENU |
| [`scripts/04_px4_ros2_bridge.py`](scripts/04_px4_ros2_bridge.py) | ROS 2 → PX4: services `/drone/takeoff`, `/drone/land`, topic `/drone/cmd_vel` (body frame: x forward, y left); publishes `/drone/px4/odom` (the autopilot's own estimate) |
| [`scripts/05_fly_square_ros2.py`](scripts/05_fly_square_ros2.py) | a square flown with ROS 2 only |
| [`scripts/mission_node.py`](scripts/mission_node.py) | **your activity**: waypoints, a photo at each, a watchdog. Three TODOs |
| [`scripts/airsim.rviz`](scripts/airsim.rviz) | RViz: the camera image, the drone's path, TF |

---

## A1 – The drone as ROS 2 topics (15 min)

**Goal:** start the simulator and both bridges, and see the drone in RViz before it flies.

| | |
|---|---|
| T1 | `drone-sim start --world neighborhood` (wait until `drone-sim status` reports AirSim and PX4 running) |
| T2 | `python3 ~/labs/week10/scripts/03_airsim_ros2_bridge.py` – AirSim → ROS 2 |
| T3 | `python3 ~/labs/week10/scripts/04_px4_ros2_bridge.py` – ROS 2 → PX4 (wait until it reports the connection) |
| T4 | `rviz2 -d ~/labs/week10/scripts/airsim.rviz`, then in a fifth tab `ros2 topic list` and `ros2 topic hz /drone/front/image_raw` |

**You should see:** the front camera image and the `map → base_link` TF in RViz; `ros2 topic list` shows
`/drone/odom`, `/drone/imu`, `/drone/gps/fix`, `/drone/px4/odom`, `/drone/cmd_vel`; the camera runs at about 9 Hz.
**Check:** which of these topics would exist on a real drone, and which only in simulation?

## A2 – Fly from ROS 2 (20 min)

**Goal:** take off, drive and land with ordinary ROS 2 services and one topic – no MAVSDK, no AirSim API.

| | |
|---|---|
| T4 | `ros2 service call /drone/takeoff std_srvs/srv/Trigger` |
| T4 | `ros2 topic pub -r 10 /drone/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.0}}"` – a few seconds, then Ctrl+C |
| T4 | `ros2 service call /drone/land std_srvs/srv/Trigger` |
| T4 | `python3 ~/labs/week10/scripts/05_fly_square_ros2.py --side 5` |

**You should see:** the drone climbs to 15 m – above the houses, the trees and the power lines (the PX4 bridge's
`altitude` parameter) – flies forward while the command is published and holds still within
0.5 s of Ctrl+C (the PX4 bridge stops it when commands stop). `05_fly_square_ros2.py` flies a 5 m square and prints
`RESULT finished … m (horizontal) from the start of the square`. **Check:** `cmd_vel` x is "forward". Turn the drone
(`angular: {z: 0.5}`) and publish x again – which way does it fly now?

## A3 – Truth against estimate (20 min)

**Goal:** compare the simulator's truth with the autopilot's own estimate – the only one a real drone has.

| | |
|---|---|
| T4 | `ros2 topic echo /drone/odom --field pose.pose.position` – the truth (simulation only) |
| T5 | `ros2 topic echo /drone/px4/odom --field pose.pose.position` – PX4's EKF2 estimate (IMU + GPS + barometer) |

Fly the square again (A2) while both are printed. **You should see:** two positions that agree closely but not
exactly. **Check:** note the difference at the corners of the square – this is how far off a real drone could be
without knowing it (Week 12).

---

## Your activity (the TODO) – finish mission_node.py (70 min)

**What you build:** a mission node that flies a 10 m square, takes a sharp photo of the middle at each corner, and
lands on its own when its data stops.

1. **Start** T1–T3 as in A1 (and RViz in T4 if you like).
2. **Run it as given:** `python3 ~/labs/week10/scripts/mission_node.py`. It takes off – and does not reach waypoint 1.
3. **Open [`scripts/mission_node.py`](scripts/mission_node.py).** Three TODOs:
   * **TODO 1 – `go_to()`:** the error `(ex, ey)` is in the map frame (x east, y north); `/drone/cmd_vel` is in the
     body frame (x forward, y left). Rotate the error by −yaw (the lecture formula). As given it is right only while
     the drone faces east.
   * **TODO 2 – `photo()`:** as given it saves whatever image arrived last – maybe from before the drone stopped
     turning. Hover until the speed is below `STILL` (0.2 m/s, at most 10 s), throw the old image away and wait for the
     **next** one – but at most 2 s: no new image means the camera bridge has died, so return `None` and the mission
     lands.
   * **TODO 3 – `odom_ok()`:** the watchdog. Return `False` when the last `/drone/odom` message (`self.t_odom`) is more
     than 1 s old – a bridge has died and you are flying blind; the mission then stops and lands.
4. **Run it after each TODO** and keep the `RESULT` line. Photos are saved in `~/mission/wp01.png` … `wp04.png`.
5. **Test the watchdog:** start the mission again and, while it flies, press Ctrl+C in T2 (the AirSim bridge).
6. **Done when** – all three are true:
   * four waypoints reached, worst miss under 0.5 m, four sharp photos of the middle of the square;
   * Ctrl+C on the AirSim bridge in flight makes the mission print `WATCHDOG` and land;
   * you have a table: as given / + TODO 1 / all three × (waypoints, photos, worst miss, distance from the start at the end).

### Solution (compare after you have tried)

[`../solutions/week10/mission_node.py`](../solutions/week10/mission_node.py): TODO 1
`cmd.linear.x = (c*ex + s*ey)*k`, `cmd.linear.y = (-s*ex + c*ey)*k` with `c, s = cos(yaw), sin(yaw)`; TODO 2 hover while
`self.vel > STILL`, set `self.img = None`, spin until a new image or 2 s; TODO 3
`return time.monotonic() - self.t_odom < 1.0`.

Measured 15 Oct 2026 (simulated, *neighborhood* world, take-off to 15 m):

| Mission node | waypoints | photos | worst miss | at the end |
|---|---|---|---|---|
| as given | 0 of 4 – waypoint 1 not reached in 60 s (11.7 m away) | 0 | – | landed 17.2 m from the start |
| + TODO 1 | 4 of 4 in 33 s, 39.0 m flown | 4, at 0.16 – 0.17 m/s | 0.49 m | 0.13 m from the start |
| **all three (solution)**, two runs | 4 of 4 in 34 s, 39.1 m flown | 4, at 0.16 – 0.18 m/s | 0.42 – 0.47 m | 0.10 – 0.19 m from the start |
| AirSim bridge stopped in flight, TODOs 1 + 2 (no watchdog) | 3, then flies on stale odometry until the 60 s waypoint timeout | 3 | 0.31 m | lands after 86 s, 2.8 m from the start |
| AirSim bridge stopped in flight, solution | 3, then `WATCHDOG: no odometry for 1 s - landing now` | 3 | 0.48 m | lands at once (30 s), 1.4 m from the start |

What the numbers say:
* **One rotation decides everything:** without TODO 1 the drone never reaches the first waypoint; with it every
  waypoint is reached within 0.5 m.
* **Fresh data or land:** with the AirSim bridge stopped, the node without a watchdog kept steering on the last
  position it had received – for a whole minute, until the waypoint timeout. The watchdog landed it after 1 s.
  Every wait for sensor data needs a time limit: the photo wait (TODO 2) has one too, 2 s for a new image.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ros2 service call /drone/takeoff …` waits for ever | the PX4 bridge (T3) is not running, or still waiting for PX4: look at T3 |
| RViz shows no image | the AirSim bridge (T2) is not running; `ros2 topic hz /drone/front/image_raw` should show about 9 Hz |
| The drone flies off in the wrong direction once it has turned | TODO 1: the map-frame error is sent unrotated |
| The photos are blurred or point at the sky | TODO 2: the photo is taken while the drone is still moving or turning |
| The bridge stopped but the drone keeps flying (and drifting) | TODO 3: the watchdog never fires |
| The mission freezes after a waypoint (no photo, no landing) | TODO 2: the wait for a new image has no time limit - the camera bridge has stopped |
| Anything hangs | Ctrl+C everywhere, `drone-sim stop`, then start again from T1 |
