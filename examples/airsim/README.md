# Drone simulation: AirSim + PX4, with and without ROS 2

Container: `abdulmannan617/tc70045e-drone:latest` (NVIDIA GPU; see [docs/RUN_LOCALLY.md](../../docs/RUN_LOCALLY.md)
or [docs/RUN_ON_VAST.md](../../docs/RUN_ON_VAST.md)). Open a terminal in its desktop and start the simulator:

```bash
drone-sim start --world blocks          # worlds: blocks (light), neighborhood (town), mountains (open terrain)
drone-sim status                        # AirSim running, PX4 running, API port answering, GPU visible
drone-sim stop
```

`drone-sim start` starts two programs: **AirSim** (the world, physics, cameras and sensors) and **PX4** (the
autopilot that keeps the drone stable and executes your commands). Add `--headless` if nobody needs to watch the
simulator window; camera images still work.

## The two pipelines

```
WITHOUT ROS 2 - plain Python
  01_hello_airsim.py     ──(AirSim API, TCP 41451)──────────────────────────────▶ AirSim   (state, camera images)
  02_fly_square_mavsdk.py──(MAVSDK / MAVLink, UDP 14540)──▶ PX4 ──(HIL messages)──▶ AirSim   (flying)

WITH ROS 2 - two bridge nodes turn the same two links into ROS 2 topics
  AirSim ──(API)──▶ 03_airsim_ros2_bridge.py ──▶ /drone/front/image_raw /drone/front/depth /drone/odom /drone/imu
                                                 /drone/gps/fix /tf                       ──▶ RViz, your nodes
  your node ──/drone/cmd_vel, /drone/takeoff, /drone/land──▶ 04_px4_ros2_bridge.py ──(MAVSDK)──▶ PX4 ──▶ AirSim
  05_fly_square_ros2.py is such a node: it only uses ROS 2 topics and services.
```

| Step | Run | You should see |
|---|---|---|
| 1 | `python3 ~/labs/examples/airsim/01_hello_airsim.py --show` | position/attitude/IMU/GPS printed, a live front camera window; `~/airsim_front.png`, `~/airsim_depth.png` |
| 2 | `python3 ~/labs/examples/airsim/02_fly_square_mavsdk.py --side 5 --alt 5` | take-off, a 5 m square, landing (watch the simulator window) |
| 3 | `python3 ~/labs/examples/airsim/03_airsim_ros2_bridge.py` and `rviz2 -d ~/labs/examples/airsim/airsim.rviz` | camera image, depth and the drone's path in RViz; `ros2 topic hz /drone/front/image_raw` about 10 Hz |
| 4 | `python3 ~/labs/examples/airsim/04_px4_ros2_bridge.py`, then `ros2 service call /drone/takeoff std_srvs/srv/Trigger` | the drone climbs to 5 m and holds; `ros2 topic pub -r 10 /drone/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.0}}"` flies forward |
| 5 | with 3 and 4 running: `python3 ~/labs/examples/airsim/05_fly_square_ros2.py` | a square flown from ROS 2, then `RESULT finished … m from the start` |

Frames: AirSim and PX4 use **NED** (x north, y east, z down). The ROS 2 topics use the ROS convention **ENU**
(x east, y north, z up) for `map` and **FLU** (x forward, y left, z up) for `base_link`. The bridges convert.

## Real hardware in the loop

The same scripts fly a real **Pixhawk 6C** autopilot with a **Jetson Orin Nano Super** companion computer while
AirSim simulates the world: [docs/HIL_JETSON_PIXHAWK.md](../../docs/HIL_JETSON_PIXHAWK.md).
