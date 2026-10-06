# TC70045E Docker Lab Kit – every laboratory on your own laptop

This kit gives every student the **same ROS 2 Humble environment** on Windows, macOS (Intel or Apple silicon) and Linux,
without installing ROS. Everything runs in a container and you use it through your **web browser** – no X server, no
dual boot. It contains a **simulated lab robot** (package `tc70045e_sim`), so every laboratory in the module can be done
without the physical robot.

| You can run | Weeks |
|---|---|
| ROS 2 Humble desktop (terminal, rviz2, rqt, Gazebo) in the browser | all |
| The simulated lab robot: four-wheel mecanum base, 2D LiDAR, 9-axis IMU, D455-style RGB-D camera, wheel encoders, battery model | 1, 3–12 |
| A virtual microcontroller on a serial port, CAN on a virtual bus, circuit simulation with ngspice | 2 |
| A single-wheel motor test bench (system identification and PID) | 3 |
| IMU noise model for Allan-deviation work, magnetometer calibration | 4 |
| rosbag2 (MCAP), the EKF (robot_localization), Madgwick filter | 5, 6 |
| Depth and LiDAR characterisation in a range-test world | 7, 8 |
| SLAM Toolbox / Cartographer, AMCL and Nav2, RTAB-Map, point clouds, Octomap | 9, 10 |
| OpenCV and object detection on the simulated camera, a local language-model command layer | 11 |
| Two robots in one world (namespaces, DDS), PX4 SITL drone flown from Python with MAVSDK | 12 |

> **Status.** The image packages, the simulator and every laboratory command in the twelve lectures were run on a clean
> ROS 2 Humble container (Ubuntu 22.04) in September 2026 – see `../VERIFICATION.md` for exactly what was tested.
> Still to do once on real student hardware: `lab_checklist.md` on one Windows, one macOS and one Linux laptop
> (the browser desktop and graphics cannot be tested in a headless container).

---

## 1. Install the prerequisites (once)

| Platform | Install | Notes |
|---|---|---|
| Windows 10/11 | Docker Desktop + WSL 2 backend | In Docker Desktop: Settings → Resources → at least 4 CPUs, 8 GB RAM, 40 GB disk |
| macOS (Intel or Apple silicon) | Docker Desktop | Apple silicon works: the images are multi-architecture; Gazebo runs on the CPU and is slower |
| Linux | Docker Engine + `docker compose` plugin | Add yourself to the `docker` group, then log out and back in |

```bash
docker --version
docker compose version
```

## 2. Build and start it

Clone or download the repository, open a terminal in its `docker/` folder and run:

```bash
docker compose up -d ros2          # the first build downloads and builds ~12 GB: allow 20-40 minutes
```

Then open **http://localhost:6080** in your browser: a Linux desktop with ROS 2 Humble. Open a terminal there and run
the self-test (about three minutes):

```bash
bash ~/labs/tools/validate.sh      # every line should end in OK
```

Stop everything with `docker compose down` (your files are kept on your laptop).

## 3. What is inside

* `Dockerfile` – starts from `tiryoh/ros2-desktop-vnc:humble` and adds Gazebo + `gazebo_ros`, `realsense2_camera`,
  `depth_image_proc`, `rtabmap_ros`, `slam_toolbox`, `cartographer_ros`, `navigation2`, `robot_localization`,
  `imu_filter_madgwick`, rosbag2 with MCAP, `rqt`, `tf2-tools`, `pcl-ros`, `octomap-server`, `camera-calibration`,
  `topic-tools`, `teleop-twist-keyboard`, ngspice, socat, can-utils, OpenCV, python-can, pyserial, MAVSDK-Python, and
  builds the simulator package **`tc70045e_sim`** into `/opt/tc70045e_ws`.
* `tc70045e_sim/` – the simulated lab robot (source, launch files, worlds and configuration). Read its Python nodes:
  they are short and documented, and knowing what the simulator models – and what it leaves out – is part of the module.
* `docker-compose.yml` – services **ros2** (the desktop; port 6080 for the browser, 5901 for a VNC client) and **px4**
  (PX4 SITL, headless, for Week 12).
* Folders mounted into the container:

| On your laptop | In the container | Use |
|---|---|---|
| the repository (`..`) | `~/labs` | every week's scripts: `~/labs/weekNN/scripts/…` |
| `docker/workspace/` | `~/ws` | your own ROS 2 packages (`colcon build` here) and maps |
| `docker/bags/` | `~/bags` | your rosbag2 recordings |

## 4. The simulated lab robot

```bash
ros2 launch tc70045e_sim sim.launch.py                          # lab world, Gazebo window, camera on
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false # lightest: LiDAR, IMU and odometry only
ros2 launch tc70045e_sim sim.launch.py world:=range x:=0 y:=0   # range-test world (target wall at 6.95 m)
ros2 run teleop_twist_keyboard teleop_twist_keyboard            # drive it (Shift + J / L moves sideways)
```

| Topic | What it is | Rate |
|---|---|---|
| `/scan` | 2D LiDAR, 720 rays (0.5°), 0.15–12 m | 5.5 Hz |
| `/imu/data_raw`, `/imu/mag` | 9-axis MEMS IMU (with bias and noise), magnetometer (with hard/soft iron) | 100 Hz, 50 Hz |
| `/wheel_speeds`, `/vel_raw`, `/odom_raw` | wheel encoders (2464 counts/rev) and wheel odometry, with realistic calibration errors | 25 Hz |
| `/camera/color/image_raw`, `/camera/aligned_depth_to_color/image_raw` (+ `camera_info`) | D455-style RGB-D camera, 848 × 480, depth noise σZ = Z²·σd/(f·b) | nominal 15 Hz (5–8 Hz with software graphics) |
| `/battery`, `/voltage`, `/power/current` | 3S battery and power model | 10 Hz |
| `/ground_truth/odom` | the simulator's exact pose – for evaluating your estimates only | 50 Hz |
| `/cmd_vel` | drive command: vx, vy and wz (holonomic). The robot keeps the last command – send a zero Twist to stop | – |

Other tools in the package: `ros2 run tc70045e_sim motor_bench` (Week 3), `virtual_mcu` (Week 2),
`imu_noise_model` (Week 4). Configurations for the EKF, SLAM Toolbox, Cartographer and Nav2 are in
`$(ros2 pkg prefix tc70045e_sim)/share/tc70045e_sim/config/`.

## 5. A real Intel RealSense D455 (optional, Linux only)

USB pass-through into a container works only on **Linux**. With a D455 plugged in, start the kit with the override file
and run the real driver – it publishes the same topic names as the simulated camera:

```bash
docker compose -f docker-compose.yml -f docker-compose.linux-usb.yml up -d ros2
ros2 launch realsense2_camera rs_launch.py camera_namespace:=/ enable_gyro:=true enable_accel:=true \
  align_depth.enable:=true pointcloud.enable:=true \
  depth_module.depth_profile:=848x480x30 rgb_camera.color_profile:=1280x720x30
```

The device is deliberately NOT in the main compose file: on Windows and macOS a `/dev/bus/usb` entry makes
`docker compose up` fail before the container starts.

## 6. Drone simulation (Week 12)

```bash
docker compose up -d px4                     # PX4 SITL + Gazebo, headless
docker compose logs px4 | tail               # wait for "Ready for takeoff!"

# in the ros2 desktop terminal - MAVSDK, not MAVROS (see the note below):
python3 - <<'PY'
import asyncio
from mavsdk import System

async def main():
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")   # udp:// is deprecated
    async for s in drone.core.connection_state():
        if s.is_connected:
            print("connected"); break
    async for b in drone.telemetry.battery():
        print("battery %.2f V" % b.voltage_v); break

asyncio.run(main())
PY
```

Then run `~/labs/week12/scripts/px4_square.py`: arm, take off, fly a 2 m square in offboard mode, land.

> **Why MAVSDK and not MAVROS?** There is no `ros-humble-mavros` binary package - verified against packages.ros.org
> (jammy lists only Iron and Rolling), and installing it would break the image build. MAVSDK-Python installs with pip,
> does not depend on the ROS release, and speaks MAVLink to PX4 directly. The kit pins `mavsdk<4`, because release 4.0
> moved the documented gRPC API to a separate package, `mavsdk-grpc`. If you want autopilot data as ROS 2 *topics*,
> the supported modern route is uXRCE-DDS, not MAVROS.
>
> Run the MAVSDK code **in the ros2 container**, not in the px4 one. The PX4 image is built on Ubuntu 24.04, where
> `pip3 install` refuses to touch the system Python (PEP 668, "externally-managed-environment") - verified.

Use QGroundControl on your laptop (connect to UDP 14550) if you prefer a GUI to code.

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Browser shows nothing on :6080 | Container still starting, or port in use | `docker compose logs -f ros2`; change the port mapping to `6081:80` |
| `spawn_entity: Service /spawn_entity unavailable` | Gazebo took longer than 30 s to start (slow laptop), or an old Gazebo is still running | Close other Gazebo windows (`pkill -f gzserver`) and launch again |
| Gazebo is very slow, camera below 5 Hz | No GPU in the container (normal on Windows/macOS) | Use `gui:=false`, and `camera:=false` in weeks that do not need the camera |
| The robot keeps driving after you stop your script | The simulator holds the last `/cmd_vel` | `ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"` – and always send a zero Twist on exit |
| Nothing in rviz2 or "No transform" | The node was started without simulated time | Add `use_sim_time:=true` (launch) or `-p use_sim_time:=true` (run) |
| SLAM or navigation jumps and warns about TF | Two nodes publish `odom → base_footprint` | With an EKF, start the simulator with `odom_tf:=false` |
| `ImportError: numpy.core.multiarray failed to import` from `cv_bridge` | Something installed NumPy 2.x over the system NumPy | `pip3 install "numpy<2"` and restart the node |
| `realsense2_camera` finds no device | USB pass-through (Windows/macOS) | Use the simulated camera, or a Linux machine |
| Camera topics appear as `/camera/camera/...` with a real D455 | RealSense driver 4.55+ nests the node in a namespace | Add `camera_namespace:=/` to `rs_launch.py`, as above |
| `ros2 run pcl_ros filter_voxel_grid_node` – "executable not found" | Humble's `pcl_ros` ships no filter nodes | Use the NumPy filter node from Week 10 |
| Out of disk space | Images and bags are large | `docker system prune -a`, and keep bags in `docker/bags/` |
| Permission errors on files in `workspace/` | Container user id differs from yours | `sudo chown -R $(id -u):$(id -g) workspace` on Linux |

## 8. Academic use

State in your report which environment produced each result: **simulation (this kit)** or **physical robot / real D455**.
Results from simulation are acceptable evidence when you say so and discuss how the hardware would differ – the simulator
is a model, and knowing what it leaves out is part of the evaluation.
