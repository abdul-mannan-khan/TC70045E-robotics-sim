# Release checklist for the TC70045E Docker Lab Kit (tutor: do this ONCE on real laptops before term)

The image, the simulated lab robot and every laboratory command were run on a headless ROS 2 Humble container on a
Linux server (see `../VERIFICATION.md`). What a server cannot test is the **browser desktop, the graphics and the speed
of a student laptop**. Work through this list on one Windows, one macOS and one Linux laptop, and correct `README.md`,
`Dockerfile` or `docker-compose.yml` wherever reality differs.

## A. Build and desktop
- [ ] `docker compose build ros2` completes. Build time and final image size: ______
- [ ] Every apt package in the `Dockerfile` installed (Apple silicon is the likely problem; note any that is missing): ______
- [ ] `docker compose up -d ros2`, then http://localhost:6080 shows the desktop.
- [ ] In a container terminal: `ls ~/labs` shows the repository; files created in `~/ws` appear in `docker/workspace/`.
- [ ] `bash ~/labs/tools/validate.sh` ends with "no failures". Time taken: ______

## B. The simulated lab robot with graphics (all weeks)
- [ ] `ros2 launch tc70045e_sim sim.launch.py` opens Gazebo in the browser desktop; the robot sits on the black floor line.
      Real-time factor shown by Gazebo: ______   Camera rate (`ros2 topic hz /camera/color/image_raw`): ______ Hz
- [ ] `ros2 run teleop_twist_keyboard teleop_twist_keyboard` drives it forwards, sideways (Shift + J / L) and round.
- [ ] rviz2 shows `/scan`, the camera image and the TF tree (fixed frame `odom`, `use_sim_time` on).
- [ ] Week 9: SLAM Toolbox builds a map in rviz2, `map_saver_cli` writes it into `docker/workspace/maps/`, and Nav2
      reaches a goal set with "Nav2 Goal" in rviz2.
- [ ] Week 10: RTAB-Map runs with the simulated camera (command in the Week 10 lecture). Loop closures seen: ______

## C. Optional: a real Intel RealSense D455 (Linux laptop only)
- [ ] `docker compose -f docker-compose.yml -f docker-compose.linux-usb.yml up -d ros2`; `rs-enumerate-devices` lists the camera.
- [ ] `ros2 launch realsense2_camera rs_launch.py camera_namespace:=/ …` (README section 5) publishes the same topic
      names as the simulated camera; the Week 7 depth script runs unchanged on it.
- [ ] Confirm that USB pass-through does **not** work on Windows/macOS Docker Desktop (the README says so).

## D. Drone simulation (Week 12)
- [ ] `docker compose up -d px4` starts PX4 SITL. `docker compose logs px4` shows "Ready for takeoff".
- [ ] The Week 12 connection snippet reports `connected` and a battery voltage on `udpin://0.0.0.0:14540`.
- [ ] `px4_square.py` arms, takes off, flies the square and lands.
- [ ] Optional: QGroundControl on the host connects on UDP 14550.

## E. Performance and housekeeping
- [ ] Minimum laptop that gave a usable experience (CPU, RAM, GPU): ______
- [ ] Total disk used after a full build: ______
- [ ] Students without enough disk/RAM: agreed fallback (laboratory PCs): ______
