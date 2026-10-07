# What has been tested, and what has not

## AY26-27 simulation course - containers tested on Vast.ai GPU machines, 6-7 October 2026

| Image | Test | Result |
|---|---|---|
| `tc70045e-ros2:humble` | `tools/validate.sh` (local build, 6 Oct) | **42 of 42 pass** |
| `tc70045e-ros2:humble` | Week 2 wall follower (solution), 120 s, safety brick on | 23.7 m along the walls, closest laser range 0.48 m, 0 safety stops; Ctrl+C stops the robot |
| `tc70045e-ros2:humble` | Week 3 acceptance test (solution) | square PASS (0.00 m from start), diagonal PASS (0.70 m / 0.70 m) |
| `tc70045e-ros2:humble` | **Week 3 (Nav2, 7 Oct)**: `nav.launch.py` (Gazebo + map + AMCL + Nav2 + RViz), automatic start pose, `go_to.py`, `drop_box.py`, patrol solution; A3 checks and A5 inflation radius | start pose (0.01, 0.01); doorway SUCCEEDED 14.6 s; detour round a dropped box 18.6 s; patrol 5 of 5 in 117 s; goal outside the map FAILED after recoveries (21 s); goal in a wall SUCCEEDED within the 0.5 m planner tolerance; inflation 0.15 / 0.8 m changes paths (0.8 m: 23.9 s), doorway stays open |
| `tc70045e-drone` | AirSim Blocks, Neighborhood, Mountains start (`drone-sim start`), window in the browser desktop via VirtualGL | all three start; PX4 1.14.3 "Ready for takeoff" |
| `tc70045e-drone` | **without ROS 2**: AirSim API (state, IMU, GPS, camera); MAVSDK square | square flown and landed in Blocks (5 m), Mountains (30 m) and Neighborhood (15 m) |
| `tc70045e-drone` | **with ROS 2**: sensor bridge (pose, IMU, GPS, camera about 9 Hz), control bridge (take-off/land services, `/drone/cmd_vel`), square from a ROS 2 node | finished 0.07-0.14 m from the start (Blocks, Neighborhood, Mountains); response to a velocity step 0.6 s |
| `tc70045e-drone` | **HIL path** (`drone-sim start --mode hil`) | relay listens on 4570, AirSim opens `/dev/ttyPX4` and waits for HIL messages; **not tested with a real Pixhawk 6C / Jetson** |
| `tc70045e-carla` | **without ROS 2**: CARLA 0.9.15 Town04, autopilot + chase camera; cruise control (PI + pure pursuit), 60 s | mean 50.1 km/h, max error 0.1 km/h over the last 10 s |
| `tc70045e-carla` | **with ROS 2**: official bridge (43 topics; camera, LiDAR, odometry, speedometer about 5 Hz in synchronous mode), cruise control as a ROS 2 node | 40.0 km/h held |
| `tc70045e-companion` | builds for linux/arm64 and linux/amd64 | builds; **not run on a Jetson yet** |

Problems found and fixed during these tests (all in the images now): AirSim needs write access to its folder; PX4
1.14 renamed `COM_OBL_ACT`; AirSim aborted when nothing listened on its QGroundControl port; MAVSDK now uses UDP
14550 (AirSim itself uses 14540); a restarted simulator must wait for TCP 4560 to be released; metric depth pictures
take about 5 s in AirSim 1.8.1 (so the ROS 2 bridge publishes colour only); speech synthesis during a recording
disturbed the simulation (narration is now prepared first); PX4 magnetometer strength checks disabled and the
simulated battery kept full for long demos. CARLA: `localhost` resolves to IPv6 and times out - use 127.0.0.1;
the bridge needed three fixes for Humble/NumPy 1.26 (town reload, `world.tick()`, `np.bool`); Town03 did not start
on an RTX 3060 - Town04 is the tested town; the cruise-control example starts in a middle lane (an outer lane
becomes an exit ramp).

## Previous edition (before the AY26-27 rebuild)

Last full run: **21 September 2026.** The lab image was built with a real `docker build` from `docker/Dockerfile`
(Docker 29 in WSL 2, Ubuntu 22.04 base, ROS 2 Humble), and every laboratory in the twelve lectures was run
inside a container from that image, in lecture order, as a student would run it. The measured numbers in the
lectures and the tutor notes come from those runs. Earlier runs (19–20 September) on a rented Linux server
covered the package list, the drone laboratory and the first version of the simulator.

## Tested, and passing

| Layer | What was checked | Result |
|---|---|---|
| Image build | `docker build` of the final `docker/Dockerfile` on a clean `tiryoh/ros2-desktop-vnc:humble` (22 Sept 2026), then `docker compose up -d ros2` | builds (14.5 GB) with no pip conflicts; the simulator compiles in the image; the browser desktop answers on :6080; numpy 1.26.4, setuptools 79, torch 2.14+cpu, ultralytics 8.4, onnxruntime 1.23, cv_bridge imports; Week 5 packages build with `colcon build --symlink-install` |
| Kit self-test | `tools/validate.sh` in the container started by `docker compose` | **42 of 42 checks pass**: /scan 5.5 Hz, IMU 99.9 Hz, odometry 25 Hz, ground truth 49.9 Hz, camera 11.6 Hz at 424 × 240, sideways motion, EKF, SLAM map, Nav2 |
| Every code block in the 12 lectures | 253 blocks extracted by `tools/extract_commands.py`; shell parsed with `bash -n`, Python with `ast.parse` | 155 checkable blocks, **0 failures** |
| Week 1 | graph audit, battery model at 60× time scale (125 min predicted vs model within 1 %), latency step test | pass |
| Week 2 | ngspice buck and I²C netlists, virtual serial microcontroller + host bridge, bit-error injection, CAN and SBUS scripts | pass |
| Week 3 | motor-bench identification, PI/PID with anti-windup and load step, mecanum kinematics against ground truth | pass |
| Week 4 | static IMU capture, Allan deviation (recovers the noise model's N within 1 %), magnetometer calibration (heading error 15.9° → 0.9° RMS), aliasing demo | pass |
| Week 5 | custom-message monitor node built with colcon, QoS incompatibility demonstrations, MCAP recording and replay | pass |
| Week 6 | odometry calibration (square error 4.6 % → 0.9 %), Madgwick sweep, robot_localization EKF against ground truth | pass |
| Week 7 | depth-accuracy experiment at five ranges (recovers σd = 0.080 px), plane fits, bandwidth/latency, bag record/replay | pass |
| Week 8 | LaserScan probe, avoid/follow/guard, stop test at 0.2/0.3/0.5 m/s (12/12 runs clean) | pass |
| Week 9 | slam_toolbox and Cartographer mapping scored against ground truth, AMCL + Nav2, five-run repeatability | pass |
| Week 10 | ORB features, point-cloud chain and Octomap, RTAB-Map with loop closures | pass |
| Week 11 | line follower, colour tracker, YOLO11 on CPU (PyTorch, ONNX, INT8), Ollama + qwen2.5:0.5b command layer with interlocks | pass |
| Week 12 | two robots (namespaces, DDS domains, discovery, QoS age, clock skew), fault-injection drill | pass |
| Week 12 drone | connect → arm → take off → offboard 2 m square → land on PX4 SITL 1.17 (19 Sept, separate machine) | flies |

## Corrections that came out of testing (already applied)

1. **MAVROS has no Humble binary package** – Week 12 uses MAVSDK-Python (`mavsdk<4`, `udpin://0.0.0.0:14540`).
2. **NumPy 2 breaks `cv_bridge`** – the image pins `numpy<2`, including in the Week 11 PyTorch line.
3. **RealSense driver 4.58** needs `camera_namespace:=/` and the `depth_module.depth_profile` / `rgb_camera.color_profile` arguments.
4. **`pcl_ros` on Humble has no filter nodes** – Week 10 uses a NumPy node.
5. **The base image has no `ubuntu` user at build time** – environment defaults go to `/etc/profile.d`.
6. **A ROS 2 parameter list may not mix `0` and `0.05`** – every number in `config/ekf.yaml` is a float.
7. **Nav2 on a holonomic base:** the stock `min_y_velocity_threshold` (0.5) was set to 0.001; the stock velocity
   smoother still removes sideways commands, which Week 9 teaches deliberately (see the comment in `nav2_params.yaml`).
8. **RTAB-Map with wheel odometry** needs `Reg/Force3DoF true`, because the odometry reports z/roll/pitch as unmeasured.
9. **One BLAS thread per process** (`OPENBLAS_NUM_THREADS=1`) – on many-core machines numpy otherwise starts dozens of
   threads per process and delays `/cmd_vel`.
10. **PyTorch pulls setuptools 84, which breaks colcon** – the Week 11 pip line pins `setuptools<80`.
11. **Nodes that must send a final zero Twist** on Ctrl-C use `SignalHandlerOptions.NO`; the simulator keeps the last command.

## Machine-dependent numbers (be aware)

The camera is rendered in software when there is no GPU. On the module's test laptop (i5-1240P, 16 threads, WSL 2)
the simulated D455 ran at about 2.5–6.5 Hz at 848 × 480 and about 9–17 Hz at 424 × 240 (`camera_width:=424
camera_height:=240`), and a busy laptop slows the whole simulation below real time. `ros2 topic hz` measures wall
time, so its rates fall with the real-time factor; the simulated sensors keep their rates in simulated time.

## Not tested — treat as unverified

* The **browser desktop and graphics** on your particular laptop (Windows/macOS Docker Desktop): `docker/lab_checklist.md`.
* **Interactive tools**: rviz2 clicks, `rqt_graph`, `rqt_image_view`, `teleop_twist_keyboard` (needs a real terminal),
  `rtabmap-databaseViewer`.
* **KiCad** (runs natively on your laptop, outside the container).
* The **Ollama compose service** (`docker compose up -d ollama`): the Week 11 command layer was tested with Ollama
  installed inside the container, which the lecture gives as the fallback.
* **Lossy-link experiments with `tc netem`**: the container has no NET_ADMIN capability.
* Anything on **physical hardware**: a real mecanum robot, a real D455 (Linux USB pass-through), bench instruments.

When a command in a lecture disagrees with what your machine does, believe your machine — then tell your tutor so
this file can be corrected.
