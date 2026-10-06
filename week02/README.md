# Week 02 – ROS 2 as Lego: Building Robots from Bricks

A robot is a box of ROS 2 bricks. This week you snap ready-made bricks together (simulator, teleop, rviz2,
slam_toolbox, Nav2), write one of your own, and build a robot of your choice. Everything runs in the module
container on the simulated lab robot:

**Run this week** - in the mobile-robot container (Gazebo + RViz, no GPU needed):

```bash
docker run -d --name tc70045e -p 6080:80 --shm-size 2g --security-opt seccomp=unconfined \
    -e USER=ubuntu -e RESOLUTION=1600x900 abdulmannan617/tc70045e-ros2:humble
```

then open <http://localhost:6080> (password `ubuntu`) and a terminal there. No Docker on your computer, or you
prefer not to run it there: rent one on Vast.ai with the same image ([docs/RUN_ON_VAST.md](../docs/RUN_ON_VAST.md)).
With a clone of this repository: `cd docker && docker compose up -d ros2` ([docs/RUN_LOCALLY.md](../docs/RUN_LOCALLY.md)).

**Watch the demo video first** (`TC70045E_Week02_demo.mp4` on Blackboard) - it shows every step below.

## The files

| Brick / file | What it does | In → out |
|---|---|---|
| [`launch/lego.launch.py`](launch/lego.launch.py) | one switch per brick: `gui`, `rviz`, `slam`, `nav`, `safety`, `wander` | – |
| [`rviz/lego.rviz`](rviz/lego.rviz) | rviz2 view: map, robot, laser, Nav2 plan, *2D Goal Pose* tool | – |
| [`scripts/safety_stop.py`](scripts/safety_stop.py) | blocks motion towards an obstacle closer than `stop_distance` (0.45 m) | `/cmd_vel_in` + `/scan` → `/cmd_vel`, `/safety/blocked` |
| [`scripts/wander.py`](scripts/wander.py) | drives forward, turns away from walls (`speed`, `turn_rate`, `turn_distance`, `clear_distance`) | `/scan` → `cmd_vel` |
| [`scripts/my_brick.py`](scripts/my_brick.py) | template for your own brick: nearest obstacle + alarm | `/scan` → `/nearest_obstacle`, `/alarm` |

## Activities

```bash
# A1 the robot brick
ros2 launch tc70045e_sim sim.launch.py camera:=false
ros2 topic list -t ; ros2 topic hz /scan                       # 5.49 Hz

# A2 + driving + viewing
ros2 launch ~/labs/week02/launch/lego.launch.py
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# A3 + mapping
ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true
ros2 run nav2_map_server map_saver_cli -f ~/labs/week02/my_map --ros-args -p use_sim_time:=true

# A4 + your safety brick (teleop remapped into it)
ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true safety:=true
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_in

# A5 build challenge
ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true wander:=true safety:=true    # A explorer
ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true nav:=true                    # B delivery (2D Goal Pose)
python3 ~/labs/week02/scripts/my_brick.py                                               # C your own brick
```

## Measured on the reference laptop (ROS 2 Humble, software graphics, 6 Oct 2026)

| Test | Result |
|---|---|
| Explorer (A), 150 s | 29.6 m driven, both rooms mapped (map 202 × 162 cells at 0.05 m), closest laser range 0.37 m |
| Delivery (B), goal (2.5, 1.0) m in the map | SUCCEEDED; robot moved (2.30, 0.86) m – 0.23 m from the goal, inside Nav2's 0.25 m tolerance |
| Safety brick (A4), 0.3 m/s straight at a wall | blocked at 0.38 m with `stop_distance` 0.45 m (LiDAR at 5.5 Hz: ~5 cm travel between scans) |
| Gazebo real-time factor with the GUI | 0.95 |

**Stop all bricks before relaunching** (`Ctrl+C`; if Gazebo reports "process has died", run `pkill -f gzserver`).

`commands.md` lists the lecture's commands in order. The previous Week 2 lab (buck ripple, I²C, UART bridge, CAN,
SBUS) is kept in [`electronics_lab/`](electronics_lab/) as an optional extra.

## Your activity (the TODO)

| | |
|---|---|
| File you edit | [`scripts/my_brick.py`](scripts/my_brick.py) (a copy of it) - look for `TODO (Week 2, Activity 5 option C)` |
| Task | turn the brick into a **right-hand wall follower** that drives through the safety brick (`/cmd_vel_in`) |
| Run | `ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true safety:=true`, then your brick |
| Done when | the robot follows the walls of both rooms and `/safety/blocked` never turns true |

## Solution

[`../solutions/week02/wall_follower.py`](../solutions/week02/wall_follower.py). Verified 6 Oct 2026 (120 s, safety
brick on): **23.7 m** driven along the walls, closest laser range **0.48 m**, **0** safety stops; Ctrl+C stops the
robot (last command 0.0 m/s). It looks at the wall on the right *and* diagonally ahead-right, because the LiDAR
updates only 5.5 times a second - a corner must be seen before the robot reaches it.
