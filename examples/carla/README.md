# Self-driving car simulation: CARLA, with and without ROS 2

Container: `abdulmannan617/tc70045e-carla:latest` (NVIDIA GPU with 8 GB or more; see
[docs/RUN_LOCALLY.md](../../docs/RUN_LOCALLY.md) or [docs/RUN_ON_VAST.md](../../docs/RUN_ON_VAST.md)).
Open a terminal in its desktop and start the simulator:

```bash
carla-sim start --town Town03           # towns: Town01-05, Town10HD (Town04 has long motorways)
carla-sim status
carla-sim stop
```

The CARLA server has **no window** in the container: it renders on the GPU off-screen, and you look through a
client - a pygame window from your Python script, or RViz through the ROS 2 bridge.

## The two pipelines

```
WITHOUT ROS 2 - the CARLA Python API
  01_hello_carla.py        ──(CARLA API, TCP 2000)──▶ CARLA server ──camera images──▶ pygame window
  02_cruise_control_api.py ──speed in, throttle/brake/steer out──▶ CARLA     (synchronous, 20 Hz)

WITH ROS 2 - the official CARLA ROS bridge (carla_ros_bridge, built for ROS 2 Humble in the image)
  CARLA ◀──(CARLA API)──▶ carla_ros_bridge ◀──ROS 2 topics──▶ RViz, your nodes
                          /carla/ego_vehicle/rgb_front/image   /carla/ego_vehicle/lidar   /carla/ego_vehicle/odometry
                          /carla/ego_vehicle/speedometer       /carla/ego_vehicle/vehicle_control_cmd  (your commands)
  03_cruise_control_ros2.py is an ordinary ROS 2 node on those topics.
```

| Step | Run | You should see |
|---|---|---|
| 1 | `python3 ~/labs/examples/carla/01_hello_carla.py` | a car driving itself in a chase-camera window, its speed printed |
| 2 | `carla-sim start --town Town04`, then `python3 ~/labs/examples/carla/02_cruise_control_api.py --target 50` | the car accelerates to 50 km/h and holds it; `RESULT last 10 s: mean …` |
| 3 | `ros2 launch carla_ros_bridge carla_ros_bridge_with_example_ego_vehicle.launch.py town:=Town04` | the bridge spawns `ego_vehicle`; `ros2 topic list | grep carla` shows its sensors |
| 4 | with 3 running: `python3 ~/labs/examples/carla/03_cruise_control_ros2.py --ros-args -p target_kmh:=50.0` | `speed … km/h (target 50)` converging; view `/carla/ego_vehicle/rgb_front/image` in RViz |

The CARLA Python API and the ROS 2 bridge must match the server version (0.9.15). The image has both.
