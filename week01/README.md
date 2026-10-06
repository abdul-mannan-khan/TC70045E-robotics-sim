# Week 01 – Your Robotics Workstation: Linux, Docker, ROS 2 and Claude

Part A (2 h) installs Linux (WSL 2 on Windows), Docker, the ROS 2 Humble container and Claude Code.
Part B (1 h) uses them: turtlesim, then a three-node sensor → controller → actuator loop.

## Start the container (from the repository folder on your laptop)

```bash
docker pull tiryoh/ros2-desktop-vnc:humble          # once; several GB
# macOS / Linux / WSL:
docker run -d --name ros2lab -p 6080:80 --shm-size=1g -v "$PWD":/home/ubuntu/labs tiryoh/ros2-desktop-vnc:humble
# Windows PowerShell:
docker run -d --name ros2lab -p 6080:80 --shm-size=1g -v "${PWD}:/home/ubuntu/labs" tiryoh/ros2-desktop-vnc:humble
```

Open http://localhost:6080, click *Connect*, open *Terminator*. This repository is at `~/labs`.

## Scripts

| What | File | Run it (inside the container) | Expected (ROS 2 Humble, 5 Oct 2026) |
|---|---|---|---|
| Room + temperature sensor (plant and sensor) | [`scripts/room_sensor.py`](scripts/room_sensor.py) | `python3 ~/labs/week01/scripts/room_sensor.py` | `/room/temperature` (sensor_msgs/Temperature) at 5.000 Hz, 0.1 °C resolution, frame `room_sensor_link` |
| P controller | [`scripts/fan_controller.py`](scripts/fan_controller.py) | `python3 ~/labs/week01/scripts/fan_controller.py` | logs `T = … C (setpoint 26.0) duty = … %` every 2 s; parameters `setpoint`, `kp`, `window` |
| Fan + motor driver (actuator) | [`scripts/fan_driver.py`](scripts/fan_driver.py) | `python3 ~/labs/week01/scripts/fan_driver.py` | `/fan/speed` at 10 Hz; stalls below 20 % duty; service `/fan/stop` (std_srvs/SetBool) |
| All three at once | [`scripts/thermal_loop.launch.py`](scripts/thermal_loop.launch.py) | `ros2 launch ~/labs/week01/scripts/thermal_loop.launch.py` (`setpoint:=24.0` optional) | settles at **27.6 °C** for setpoint 26.0 (duty ≈ 32 %), **26.4 °C** for 24.0 (duty ≈ 48 %) – the P-control steady-state error |

## Activity commands

```bash
ros2 run turtlesim turtlesim_node            # Activity 1 (+ turtle_teleop_key in a second terminal)
ros2 topic hz /turtle1/pose                  # about 62.5 Hz
rqt_graph

ros2 launch ~/labs/week01/scripts/thermal_loop.launch.py      # Activity 2
ros2 param set /fan_controller setpoint 24.0
ros2 service call /fan/stop std_srvs/srv/SetBool "{data: true}"
ros2 bag record -o ~/labs/week01/loop /room/temperature /fan/duty /fan/speed

echo hello > /tmp/note.txt; echo hello > ~/labs/week01/my_note.txt        # Activity 3, then docker rm -f ros2lab
```

`commands.md` lists every command of the lecture in order. The previous Week 1 lab (power budget, latency, graph
audit of the simulated lab robot) is kept in [`architecture_lab/`](architecture_lab/) as an optional extra.

## Your activity (the TODO)

| | |
|---|---|
| File you edit | [`scripts/fan_controller.py`](scripts/fan_controller.py) - look for `TODO (Week 1 activity)` |
| Task | The P controller leaves the room about 1.6 °C too warm. Add **integral action** (PI) so it reaches the setpoint. |
| Run | three terminals: `room_sensor.py`, `fan_driver.py`, your `fan_controller.py` (or the launch file) |
| Done when | the log shows `T = …` within 0.1 °C of the setpoint, and stays there after `ros2 param set /fan_controller setpoint 24.0` |

## Solution

[`../solutions/week01/fan_controller_pi.py`](../solutions/week01/fan_controller_pi.py) - run it instead of
`fan_controller.py`. Verified 6 Oct 2026: the room settles at **26.04 °C for a 26.0 °C setpoint** (P only: 27.6 °C).
