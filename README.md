# TC70045E — Electronic Systems (Sensors and Actuators): laboratory code

[![Build and test the lab image](https://github.com/abdul-mannan-khan/TC70045E-robotics-sim/actions/workflows/docker-build.yml/badge.svg)](https://github.com/abdul-mannan-khan/TC70045E-robotics-sim/actions/workflows/docker-build.yml)

*(The badge turns green once this repository is pushed to GitHub: the workflow builds the image from
scratch, starts the simulated robot and runs the kit self-test, so a broken upstream package is caught before a
laboratory.)*

Everything you need to do **every laboratory of this module on your own laptop**, in a browser, with no ROS
installation: a ROS 2 Humble container, a **simulated lab robot** (a four-wheel mecanum base with a 2D LiDAR, a
9-axis IMU, wheel encoders, a battery model and an Intel RealSense D455-style depth camera), and one folder per
teaching week with the scripts the lecture uses.

## Start here (once – about 30 minutes, mostly waiting for the download)

1. Install **Docker Desktop** (Windows/macOS) or Docker Engine (Linux) and start it.
2. Clone or download this repository.
3. Build and start the environment:

```bash
cd docker
docker compose up -d ros2          # first build: 20-40 minutes and about 15 GB of disk
```

4. Open **<http://localhost:6080>** in your browser: a Linux desktop with ROS 2 Humble, `rviz2`, `rqt`, Gazebo and
   a terminal. This repository is at `~/labs` inside it.
5. Check the kit, then launch the robot:

```bash
bash ~/labs/tools/validate.sh                                   # every line should end in OK (about 3 minutes)
ros2 launch tc70045e_sim sim.launch.py                          # the simulated lab robot in the laboratory world
ros2 launch tc70045e_sim sim.launch.py camera_width:=424 camera_height:=240   # faster camera on a laptop without a GPU
```

Windows users can double-click `docker/start_windows.ps1`; macOS and Linux users can run `docker/start_mac_linux.sh`.
The kit is described in detail in [`docker/README.md`](docker/README.md).

## What is in each week

| Week | Topic | What you run in the container |
|---|---|---|
| [1](week01/) | Your robotics workstation: Linux, Docker, ROS 2 and Claude | turtlesim, a three-node sensor-controller-actuator loop, rosbag2, what survives `docker rm` |
| [2](week02/) | ROS 2 as Lego: building robots from bricks | lego.launch.py (sim, rviz2, slam_toolbox, Nav2), your own safety brick, explorer / delivery robot / own-brick challenge |
| [3](week03/) | Making it move: integrating motors, drivers and encoders | motor bench bring-up, PID knobs, wheel patterns, integration clinic (fix a driver config), acceptance test |
| [4](week04/) | Inertial sensing and measurement | IMU noise and Allan deviation, magnetometer calibration, aliasing |
| [5](week05/) | ROS 2 for sensor and actuator systems | custom-message sensor monitor, QoS experiments, rosbag2 (MCAP) |
| [6](week06/) | Odometry, IMU fusion and the EKF | odometry calibration, Madgwick, robot_localization against ground truth |
| [7](week07/) | RealSense D455 depth sensing | depth-accuracy experiment, plane fit, camera bandwidth and latency |
| [8](week08/) | LiDAR sensing and reactive behaviour | LaserScan probe, avoid/follow/guard, stopping-distance test |
| [9](week09/) | LiDAR SLAM and navigation | slam_toolbox, Cartographer, AMCL and Nav2, five-run repeatability |
| [10](week10/) | Visual and RGB-D SLAM | ORB features, point clouds, Octomap, RTAB-Map benchmark |
| [11](week11/) | Edge AI perception and language-model interfaces | line follower, colour tracker, YOLO11 on CPU (ONNX, INT8), local LLM command layer |
| [12](week12/) | Multi-robot integration and the UAV outlook | two robots (namespaces, DDS, QoS, clocks), fault isolation, PX4 + MAVSDK |

Each week folder has a `README.md` (what is there and how to run it), `commands.md` (every command and code
block from the lecture, in order) and `scripts/` or `params/` for the code worth keeping in a file.

## The simulated robot and the real one

The simulator (`docker/tc70045e_sim/`) is a model, and knowing what it leaves out is part of the evaluation. It
publishes the same kinds of topics a real mecanum robot and a real D455 do (`/scan`, `/imu/data_raw`,
`/odom_raw`, `/camera/...`), so the code you write here runs unchanged on hardware. It also publishes
`/ground_truth/odom` – the exact pose – which a real robot does not have: use it only to *evaluate* your
estimates. Each lecture has an optional "On a physical robot" box for the laboratory hardware.

A real RealSense D455 can be passed into the container on **Linux** only (see `docker/README.md`).

## Tools

| File | What it does |
|---|---|
| [`tools/validate.sh`](tools/validate.sh) | kit self-test: packages, the simulator's topics and rates, EKF, SLAM and Nav2 start |
| [`tools/extract_commands.py`](tools/extract_commands.py) | regenerates every `weekNN/commands.md` from the lectures and syntax-checks them |
| [`tools/cloud_filter.py`](tools/cloud_filter.py), [`tools/fake_cloud.py`](tools/fake_cloud.py) | point-cloud pass-through + voxel filter, and a synthetic cloud to test it (Week 10) |
| [`tools/px4_square.py`](tools/px4_square.py), [`tools/px4_checks.py`](tools/px4_checks.py) | Week 12: fly a square offboard, and measure telemetry rates |

## How much of this is actually tested

See [`VERIFICATION.md`](VERIFICATION.md). In short: the image was built with `docker build`, the simulator was
started from it, and every laboratory command in the twelve lectures was run in that container, with the
measured numbers written into the lectures. What has **not** been tested is the browser desktop and graphics on
your particular laptop, interactive tools (rviz2 clicks, teleop keyboard), and anything on physical hardware.

## Academic honesty

This repository is the starting point for your laboratory work, not your submission. Anything you copy from
here into a report must be cited like any other source, and the results you report must be the ones your own
run produced — not the numbers in these files. Label simulated evidence as simulated.
