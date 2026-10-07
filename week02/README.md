# Week 02 – ROS 2 as Lego: Building Robots from Bricks

A robot is a box of ROS 2 **bricks** (nodes) that snap together through **studs** (topics). This week you snap
ready-made bricks together – the simulated robot in Gazebo, the RViz viewer, keyboard driving, mapping, navigation –
add a safety brick, and then write a brick of your own.

**Watch the demo video first:** `TC70045E_Week02_demo.mp4` in the Week 2 folder on Blackboard. It shows every step
below being typed, with Gazebo (the simulated world) and RViz (what the robot senses) side by side.

| Time in class | Part |
|---|---|
| 45 min | lecture: bricks, studs, launch files |
| 15 min | Step 0 – start the container |
| 90 min | Activities A1–A5 |
| 30 min | Your activity (the TODO) – a wall-follower brick |

---

## Step 0 – Start the container (once per session)

Pick **one** of the three ways. All three give the same Linux desktop in your web browser.

**A. Your own computer with Docker** (Windows, macOS or Linux – no GPU needed). In a terminal on your computer:

```bash
docker pull abdulmannan617/tc70045e-ros2:humble          # get the latest image (3.5 GB the first time)
docker run -d --name tc70045e -p 6080:80 --shm-size 2g --security-opt seccomp=unconfined \
    -v tc70045e_work:/home/ubuntu/work abdulmannan617/tc70045e-ros2:humble
```

The first time, this downloads 3.5 GB (10-20 minutes). Next time use `docker start tc70045e` instead.
Never used Docker? Follow the pictures in [docs/GETTING_STARTED.md](../docs/GETTING_STARTED.md).

**B. A rented computer on Vast.ai** (no Docker on your computer): follow [docs/RUN_ON_VAST.md](../docs/RUN_ON_VAST.md)
with the image `abdulmannan617/tc70045e-ros2:humble`.

**C. With a clone of this repository** (your edits stay on your own disk):
`git clone https://github.com/abdul-mannan-khan/TC70045E-robotics-sim.git`, then
`cd TC70045E-robotics-sim/docker && docker compose up -d ros2`.

Then:

1. Open **<http://localhost:6080>** in your browser (on Vast.ai: the address from the instance's port list) and
   click **Connect**. Password: `ubuntu` (or the one you chose on Vast.ai).
2. Double-click **Terminator** on the desktop. Split it into more terminals with **Ctrl+Shift+O** (one above the
   other) or **Ctrl+Shift+E** (side by side). Below, *T1*, *T2*, *T3* mean terminal 1, 2, 3.
3. Get this week's files: `update-labs` (it keeps your own changes). Then check: `ls ~/labs/week02` must list
   `launch  rviz  scripts  README.md …`. Nothing there? See *No week folders* in
   [GETTING_STARTED.md](../docs/GETTING_STARTED.md#troubleshooting).

> With way A or B, files you change live inside the container. `docker stop`/`docker start` keeps them;
> `docker rm` deletes them (Week 1). Copy your work out (or use way C) before you delete the container.

---

## The bricks in this folder

| Brick / file | What it does | Studs: in → out |
|---|---|---|
| [`launch/lego.launch.py`](launch/lego.launch.py) | starts the robot plus one brick per switch: `gui` (Gazebo window), `rviz`, `slam`, `nav`, `safety`, `wander` | – |
| [`rviz/lego.rviz`](rviz/lego.rviz) | the RViz view: map, robot, laser, Nav2 plan, *2D Goal Pose* tool | – |
| [`scripts/safety_stop.py`](scripts/safety_stop.py) | blocks motion towards an obstacle closer than `stop_distance` (0.45 m) | `/cmd_vel_in` + `/scan` → `/cmd_vel`, `/safety/blocked` |
| [`scripts/wander.py`](scripts/wander.py) | drives forward and turns away from walls | `/scan` → `cmd_vel` |
| [`scripts/my_brick.py`](scripts/my_brick.py) | template for your own brick: nearest obstacle + alarm | `/scan` → `/nearest_obstacle`, `/alarm` |

**Always add `gui:=true`** to see the Gazebo window. Without it the simulation still runs; you only see RViz.

**Before every new launch:** stop the previous one with **Ctrl+C** in its terminal and wait until the prompt `$`
returns. If a launch then dies with "process has died … gzserver", run `pkill -f gzserver`, wait 5 s, try again.

---

## A1 – The robot brick (10 min)

**Goal:** see the robot on its own and list the studs it offers.

| | |
|---|---|
| T1 | `ros2 launch tc70045e_sim sim.launch.py gui:=true camera:=false` |
| T2 | `ros2 topic list -t` |
| T2 | `ros2 topic hz /scan` (press Ctrl+C after a few lines) |

**You should see:** the Gazebo window with the lab (two rooms, a crate, a pillar) and the robot in the middle; in T2
topics such as `/scan [sensor_msgs/msg/LaserScan]`, `/cmd_vel [geometry_msgs/msg/Twist]`, `/odom_raw`, `/imu/data_raw`;
`/scan` at about **5.5 Hz**.
**Check:** which topic would you publish to make the robot move? (Answer: `/cmd_vel`.) Stop T1 with Ctrl+C.

## A2 – Snap on driving and viewing (15 min)

**Goal:** add the RViz viewer brick and the keyboard brick.

| | |
|---|---|
| T1 | `ros2 launch ~/labs/week02/launch/lego.launch.py gui:=true` |
| T2 | `ros2 run teleop_twist_keyboard teleop_twist_keyboard` |

**You should see:** Gazebo and RViz; in RViz the robot and the red laser points. Click into T2 and drive: `i` forward,
`,` back, `j` / `l` turn, `k` stop, `x` slower. The keyboard brick sends a command **once per key press** – the robot
keeps the last command until you press `k`.
**Check:** drive towards a wall in Gazebo and watch the laser points in RViz come closer. Stop T2 and T1.

## A3 – Snap on the mapping brick (15 min)

**Goal:** build a map while you drive.

| | |
|---|---|
| T1 | `ros2 launch ~/labs/week02/launch/lego.launch.py gui:=true slam:=true` |
| T2 | `ros2 run teleop_twist_keyboard teleop_twist_keyboard` – press `x` five times (0.3 m/s), then drive slowly through both rooms |
| T3 | `ros2 run nav2_map_server map_saver_cli -f ~/labs/week02/my_map --ros-args -p use_sim_time:=true` |

**You should see:** the grey map grow in RViz as you drive; T3 ends with `Map saved successfully` and
`~/labs/week02/my_map.pgm` + `my_map.yaml` exist (`ls ~/labs/week02`).
**Check:** open `~/labs/week02/my_map.pgm` with an image viewer (right-click it in the file manager → Open With): white = free, black = walls, grey = unknown.

## A4 – Make a brick: the safety stop (20 min)

**Goal:** put a brick *between* the keyboard and the robot. The keyboard now publishes to `/cmd_vel_in`, the safety
brick checks the laser and forwards only safe commands to `/cmd_vel`.

| | |
|---|---|
| T1 | `ros2 launch ~/labs/week02/launch/lego.launch.py gui:=true slam:=true safety:=true` |
| T2 | `ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_in` |
| T3 | `ros2 topic echo /safety/blocked` |

**You should see:** drive straight at a wall (`i`): the robot stops by itself and T3 shows `data: true`; turning away
(`j` or `l`) is still allowed. T1 logs `BLOCKED - obstacle ahead`.
**Check:** `rqt_graph` (in a new terminal) shows `teleop → /cmd_vel_in → safety_stop → /cmd_vel → robot`.

## A5 – Build challenge: choose one (30 min)

| Option | Start it (T1) | Then | Prove it works |
|---|---|---|---|
| **A explorer** | `ros2 launch ~/labs/week02/launch/lego.launch.py gui:=true slam:=true wander:=true safety:=true` | nobody drives – wait 2-3 minutes | both rooms appear on the map; save it as in A3 |
| **B delivery robot** | `ros2 launch ~/labs/week02/launch/lego.launch.py gui:=true slam:=true nav:=true` | in RViz click **2D Goal Pose**, then click and drag a goal in the other room | the robot plans a green path and drives there |
| **C your own brick** | `ros2 launch ~/labs/week02/launch/lego.launch.py gui:=true slam:=true safety:=true` | T2: `python3 ~/labs/week02/scripts/my_brick.py`; T3: `ros2 topic echo /nearest_obstacle` | the distance changes as you drive (keyboard in T4 as in A4); then do **Your activity** below |

---

## Your activity (the TODO) – a wall-follower brick (30 min)

**What you build:** turn `my_brick.py` into a brick that drives the robot along the wall on its **right**, about
0.5 m away, all the way round both rooms – through the safety brick, so it can never crash.

1. **Copy the template** (keep the original):
   ```bash
   cp ~/labs/week02/scripts/my_brick.py ~/labs/week02/scripts/wall_brick.py
   ```
2. **Open your copy:** double-click **VSCodium** on the desktop and open `~/labs/week02/scripts/wall_brick.py`
   (or `nano ~/labs/week02/scripts/wall_brick.py`). Find the comment `TODO (Week 2, Activity 5 option C)`.
3. **Change the brick** – three small additions:
   * an output stud: `from geometry_msgs.msg import Twist` and, in `__init__`,
     `self.cmd_pub = self.create_publisher(Twist, '/cmd_vel_in', 10)`
   * in `on_scan`: the distance to the wall on the right = the smallest range for angles around **-90°**
     (angle of ray `i` is `scan.angle_min + i * scan.angle_increment`, in radians), and the distance straight ahead
     (angles around 0°)
   * a command: if something is closer than about 0.7 m straight ahead, turn left on the spot
     (`linear.x = 0`, `angular.z = 0.6`); otherwise drive forward (`linear.x = 0.2`) and steer
     `angular.z = k * (0.5 - right_distance)` with `k` about 1.5 (positive `angular.z` turns left). Publish it.
4. **Run it** (three terminals):

   | | |
   |---|---|
   | T1 | `ros2 launch ~/labs/week02/launch/lego.launch.py gui:=true slam:=true safety:=true` |
   | T2 | `python3 ~/labs/week02/scripts/wall_brick.py` |
   | T3 | `ros2 topic echo /safety/blocked` |

5. **Done when** – all three are true:
   * the robot follows the walls of **both** rooms for 2 minutes (watch Gazebo; the map in RViz fills in);
   * T3 shows only `data: false` – the safety brick never had to stop it;
   * Ctrl+C in T2 stops the robot (it does not keep driving).
6. **Improve it** (if time): it cuts corners or hits the safety stop? The LiDAR updates only 5.5 times a second –
   look *diagonally ahead-right* as well (angles around -45°) so a corner is seen before the robot reaches it.

### Solution (compare after you have tried)

[`../solutions/week02/wall_follower.py`](../solutions/week02/wall_follower.py) – run it instead of your brick:
`python3 ~/labs/solutions/week02/wall_follower.py`.
Measured 6 Oct 2026 (120 s, safety brick on): **23.7 m** driven along the walls, closest laser range **0.48 m**,
**0** safety stops; Ctrl+C stops the robot (last command 0.0 m/s). It uses the right *and* the diagonal sector, a
gain of 1.5, and stops cleanly on Ctrl+C by handling the signal itself (see its `main()`).

### For your report

Record: your control law and gains, a screenshot of the map after 2 minutes, how often `/safety/blocked` was true,
and one change you made and its effect. Simulated results must be labelled as simulated.

---

## Measured on the reference set-up (ROS 2 Humble, 6 Oct 2026)

| Test | Result |
|---|---|
| Explorer (A5-A), 150 s | 29.6 m driven, both rooms mapped (map 202 × 162 cells at 0.05 m), closest laser range 0.37 m |
| Delivery (A5-B), goal (2.5, 1.0) m | SUCCEEDED; 0.23 m from the goal, inside Nav2's 0.25 m tolerance |
| Safety brick (A4), 0.3 m/s straight at a wall | blocked at 0.38 m with `stop_distance` 0.45 m |
| `/scan` rate | 5.49 Hz |

## Troubleshooting

| Problem | Fix |
|---|---|
| Browser shows nothing at localhost:6080 | wait 20 s after `docker run`; check `docker ps` lists `tc70045e` |
| Launch dies: "process has died … gzserver" | an old simulator is still closing: `pkill -f gzserver`, wait 5 s, launch again |
| The robot does not move with the keyboard | click into the teleop terminal first; with `safety:=true` use the `-r cmd_vel:=cmd_vel_in` version |
| The robot keeps moving after I stop pressing | the keyboard brick repeats the last command – press `k` |
| No Gazebo window | add `gui:=true` to the launch command |
| Gazebo is slow | normal on a laptop without a GPU; everything still works, just more slowly |

`commands.md` lists the lecture's commands in order. The previous Week 2 lab (buck ripple, I²C, UART bridge, CAN,
SBUS) is kept in [`electronics_lab/`](electronics_lab/) as an optional extra.
