# What has been tested, and what has not

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
