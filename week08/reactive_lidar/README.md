# Week 08 LiDAR Sensing and Reactive Behaviour

Scripts for this week's laboratory. Everything runs in the module's ROS 2 Humble container on your laptop, against the
simulated lab robot (`tc70045e_sim`). Its 2D LiDAR publishes `/scan` (sensor_msgs/LaserScan, 720 rays, 0.5 deg,
5.5 Hz, 0.15-12 m, 10 mm noise, frame `laser_link`, angle 0 = forward = index 360). The scripts also run on a real
robot's `/scan`, except those that need `/ground_truth/odom` (`move_to.py`, `stop_test.py`).

Start the environment first - nothing here needs ROS 2 installed on your own machine:

```bash
cd ../docker && docker compose up -d ros2     # then open http://localhost:6080 in your browser
```

In a terminal on that desktop, start the range world (robot at the origin, LiDAR 6.93 m from a flat wall):

```bash
ros2 launch tc70045e_sim sim.launch.py world:=range x:=0 y:=0 gui:=false camera:=false
```

| Script | What it does | Run it with | Expected output (measured 2026-09-21) |
|---|---|---|---|
| [`scripts/scan_probe.py`](scripts/scan_probe.py) | index-to-angle mapping; valid beams, dropout and perpendicular distance in a (wrapped) sector; then the temporal noise of the centre beam | `python3 ~/labs/week08/scripts/scan_probe.py` (`--centre 180 --half 5` for the rear) | `N = 720 beams ... angle 0 at index 360`; `CENTRE BEAM index 360 (0.0 deg): 30 scans  mean 6.9287 m  sd 0.0118 m` |
| [`scripts/move_to.py`](scripts/move_to.py) | drives the robot to (x, y) using `/ground_truth/odom`, then stops | `python3 ~/labs/week08/scripts/move_to.py 5.93 0.0` | `reached x=5.926 y=0.000 (target 5.930 0.000) ... robot stopped` |
| [`scripts/reactive.py`](scripts/reactive.py) | reactive behaviours `--mode avoid / follow / guard`, `--v`, `--d`, `--delay` (emulated sensor latency); Ctrl-C publishes a zero Twist | `python3 reactive.py --mode follow --d 0.8` | `[follow] nearest front 0.81 m @ -3 deg ...`; settles 0.82 m from the wall |
| [`scripts/stop_test.py`](scripts/stop_test.py) | Activity C: drives at the wall at `--v`, brakes at `--a` when the front LiDAR range < `--d`, reports the real clearance from ground truth | `python3 stop_test.py --v 0.3 --d 0.6 --a 1.0 --runs 3` | `v 0.30 ... read 0.599 m (true 0.617 ...) | after decision 0.055 m | clearance 0.431 m` |

`move_to.py` must stay in the same folder as `stop_test.py` (it is imported). Other commands from the lecture:

```bash
ros2 topic hz /scan                 # about 5.47 Hz
ros2 topic delay -s /scan           # -s = simulated time; about 0 s in simulation
ros2 topic echo --once /scan --field scan_time     # 0.0 in simulation: the Gazebo plugin does not fill it
```

Honest limits: the simulated LiDAR has no rotation (all rays at one instant, so `scan_time`, `time_increment` and the
latency are zero), no reflectance, incidence-angle or glass effects, no intensities, and range noise independent of
range. Label every result from it as simulated.

The simulated base has no command timeout. Every script stops the robot on exit; if one is killed, stop the robot with
`ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"`.
