# TC70045E — Electronic Systems (Sensors and Actuators): robotics simulation course

[![Build and test the lab image](https://github.com/abdul-mannan-khan/TC70045E-robotics-sim/actions/workflows/docker-build.yml/badge.svg)](https://github.com/abdul-mannan-khan/TC70045E-robotics-sim/actions/workflows/docker-build.yml)

A twelve-week, **simulation-only** ROS 2 course: mobile robots in **Gazebo + RViz**, a self-driving car in
**CARLA**, drones in **AirSim + PX4**. Everything runs in ready-made containers that already contain the
simulators, ROS 2 Humble and all the course code - in a browser desktop, on your own computer or on a rented
GPU computer (Vast.ai). Nothing has to be installed or downloaded besides the container.

## Every week has the same five steps

1. **Demo video** (Blackboard) - watch the commands being typed and what happens. You can repeat it at home.
2. **Lecture** - short, figure-led: the idea and the building blocks.
3. **Container** - start the simulation in class (below).
4. **Activity** - one `TODO` in one named file in this week's folder. The week's README says which file,
   what to do and how you know you are done.
5. **Solution** - a worked, tested solution in [`solutions/weekNN/`](solutions/). Try first, then compare.

## The containers

| Image | Robots | Weeks | Needs |
|---|---|---|---|
| `abdulmannan617/tc70045e-ros2:humble` | mobile robot (Gazebo + RViz + ROS 2) | 1-9, 12 | any 64-bit computer, no GPU |
| `abdulmannan617/tc70045e-carla:latest` | self-driving car (CARLA 0.9.15 + ROS 2 bridge) | 10 | NVIDIA GPU, 8 GB+ |
| `abdulmannan617/tc70045e-drone:latest` | drone (AirSim 1.8.1 + PX4 1.14 + ROS 2) | 11 | NVIDIA GPU, 6 GB+ |

**Start (own computer):**

```bash
docker run -d --name tc70045e -p 6080:80 --shm-size 2g --security-opt seccomp=unconfined \
    -e USER=ubuntu -e RESOLUTION=1600x900 abdulmannan617/tc70045e-ros2:humble
```

Open **<http://localhost:6080>** (password `ubuntu`), open a terminal in the desktop; the course is at `~/labs`.

* Full instructions for your own computer, including the GPU images and `docker compose`:
  [docs/RUN_LOCALLY.md](docs/RUN_LOCALLY.md)
* No suitable computer, or you prefer not to run simulations on it: [docs/RUN_ON_VAST.md](docs/RUN_ON_VAST.md)
  (about $0.10-0.20 an hour)
* Drone and car, with and without ROS 2: [examples/airsim/](examples/airsim/), [examples/carla/](examples/carla/)
* Drone hardware in the loop (Jetson Orin Nano Super + Pixhawk 6C): [docs/HIL_JETSON_PIXHAWK.md](docs/HIL_JETSON_PIXHAWK.md)

## The twelve weeks

| Week | Topic | Simulator | Activity file → solution |
|---|---|---|---|
| [1](week01/) | Your robotics workstation: Linux, Docker, ROS 2 and Claude | container | `fan_controller.py` → PI control |
| [2](week02/) | ROS 2 as Lego: building robots from bricks | Gazebo + RViz | `my_brick.py` → wall follower |
| [3](week03/) | Making it move: motors, drivers and speed control | Gazebo + RViz | `motion_test.py` → diagonal + square test |
| 4 | Robot description: URDF, TF, add a sensor | Gazebo + RViz | `lab_robot.urdf.xacro` → mount a range sensor |
| 5 | IMU and odometry: noise and drift | Gazebo + RViz | `heading_filter.py` → complementary filter |
| 6 | Where am I? EKF fusion (**A1 due**) | Gazebo + RViz | `ekf.yaml` → fuse the IMU |
| 7 | Simulated D455 depth camera and simple perception | Gazebo + RViz | `box_finder.py` → find the box and its distance |
| 8 | LiDAR and reactive behaviour | Gazebo + RViz | `follow_gap.py` → obstacle avoidance |
| 9 | SLAM and Nav2: a delivery robot | Gazebo + RViz | `patrol.py` → waypoint patrol |
| 10 | Self-driving car: CARLA and ROS 2 | CARLA | `cruise_control.py` → speed controller |
| 11 | Drones: take-off, waypoints, mission | AirSim + PX4 | `mission.py` → square / survey pattern |
| 12 | Capstone: integrate and test (**A2 due**) | your choice | mission specification → solution per platform |

Weeks 1-3 are complete. Weeks 4-12 are being rebuilt in the same style, one week at a time; until a week is
released its folder still holds the previous edition's material.

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

## How much of this is actually tested

See [`VERIFICATION.md`](VERIFICATION.md). In short: the image was built with `docker build`, the simulator was
started from it, and every laboratory command in the twelve lectures was run in that container, with the
measured numbers written into the lectures. What has **not** been tested is the browser desktop and graphics on
your particular laptop, interactive tools (rviz2 clicks, teleop keyboard), and anything on physical hardware.

## Academic honesty

This repository is the starting point for your laboratory work, not your submission. Anything you copy from
here into a report must be cited like any other source, and the results you report must be the ones your own
run produced — not the numbers in these files. Label simulated evidence as simulated.
