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

Every week adds a brick to the robot of the week before. Each lecture also has one short theory section that links
the simulation to real hardware and to the module's learning outcomes.

| Week | Lecture | Simulator | Activity file → solution | Theory section |
|---|---|---|---|---|
| [1](week01/) | Your robotics workstation: Linux, Docker, ROS 2 and Claude | container | `go_to_goal.py` → drive the turtle to clicked goals | – |
| [2](week02/) | ROS 2 as Lego: building a robot from bricks | Gazebo + RViz | `my_brick.py` → wall follower | – |
| [3](week03/) | The navigation brick: from a map to autonomous delivery (Nav2) | Gazebo + RViz | `patrol.py` → security patrol through both rooms | the motors, drivers and encoders behind `cmd_vel`; the electronics of a mobile robot |
| 4 | Add a sensor, upgrade the SLAM: LiDAR + Intel RealSense D455 | Gazebo + RViz | SLAM launch → RTAB-Map with LiDAR + RGB-D, scored against the true map | how stereo depth works; the D455's interfaces |
| 5 | Fuse for better localisation: IMU + odometry → EKF feeding SLAM | Gazebo + RViz | `ekf.yaml` → fuse the IMU, less drift | inside a MEMS IMU: front end, ADC, noise, filtering |
| 6 | See and understand with the D455: depth perception (**A1 due**) | Gazebo + RViz | `box_finder.py` → find the boxes and mark them on the map | – |
| 7 | D455 RGB-D SLAM and navigation, camera only | Gazebo + RViz | camera-only map, then navigate to three goals | – |
| 8 | Autonomous exploration | Gazebo + RViz | `explorer.py` → frontier exploration of an unknown building | – |
| 9 | Drones without ROS 2: AirSim + PX4 (mountains and town) | AirSim + PX4 | `mission.py` → survey pattern | testing with an oscilloscope and a logic analyser (PWM, UART/MAVLink); motors and ESCs |
| 10 | Drones with ROS 2: the drone as a ROS 2 robot | AirSim + PX4 + ROS 2 | `mission_node.py` → waypoint mission with camera snapshots | – |
| 11 | Self-driving car: CARLA without, then with ROS 2 | CARLA | `cruise_control.py` → speed controller (API and ROS 2) | steer-, throttle- and brake-by-wire actuators |
| 12 | Drone hardware in the loop: AirSim + Jetson Orin Nano Super + Pixhawk 6C (**A2 due**) | AirSim (HIL) | the Week 9 mission on a real autopilot (lecturer demo; students in SITL) | from wiring to a PCB: an interface board; testing a board |

Weeks 1-3 are released. Weeks 4-12 are built one week at a time in the same style; until a week is released its
folder still holds the previous edition's material. The demo videos for the drone and car simulators (with and
without ROS 2) are already on Blackboard; the examples are in [examples/](examples/).

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
