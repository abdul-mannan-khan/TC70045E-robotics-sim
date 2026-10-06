# TC70045E lab repository – notes for Claude

This is the student repository for TC70045E Electronic Systems (Sensors and Actuators), a Level 7 module.

## Environment
- Code runs **inside a Docker container** with ROS 2 **Humble** on Ubuntu 22.04, not on the host.
  This repository is mounted in the container at `~/labs` (`/home/ubuntu/labs`).
- Commands for the student to run start with `ros2`, `python3 ~/labs/...` or `colcon`. Say clearly that they
  are to be run in the container terminal (browser desktop at http://localhost:6080).
- Weeks 2–12 use the module image built from `docker/` (`docker compose up -d ros2`) with the simulated lab
  robot `tc70045e_sim`. Week 1 uses the base image `tiryoh/ros2-desktop-vnc:humble`.

## How to help
- Explain before changing. Prefer small, readable Python (rclpy) in the style of the existing scripts.
- Only use topic, parameter, service and package names that exist in this repository or in ROS 2 Humble;
  if unsure, tell the student the command to check (`ros2 topic list -t`, `ros2 param list`, `ros2 pkg list`).
- Never invent measurements. Results in reports must come from the student's own runs.
- Remind the student to record AI use (tool, date, prompt, what was verified) for the AI-use declaration.
