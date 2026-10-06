# Week 01 (previous edition) – Robot System Architecture, Safety and Toolchain

> **Note.** This was Week 1 before October 2026. It is kept as an optional extra lab (power budget,
> latency, graph audit on the simulated lab robot). The current Week 1 is described in `../README.md`.

Everything this week runs in the module's ROS 2 Humble container against the simulated lab robot
(`tc70045e_sim`). Nothing needs ROS 2 on your own machine.

```bash
cd ../docker && docker compose up -d ros2     # then open http://localhost:6080 and a terminal in that desktop
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false   # terminal 1: the lab robot (wait ~30 s)
```

| What | Where | Run it (inside the container) | Expected output (ROS 2 Humble, 21 Sep 2026) |
|---|---|---|---|
| Sensor inventory (Lab A) | [`scripts/topic_audit.py`](scripts/topic_audit.py) | `python3 ~/labs/week01/scripts/topic_audit.py` | one row per sensor topic: `/scan` 5.5 Hz (simulated time) `laser_link`, `/imu/data_raw` 99.8 Hz `imu_link`, `/imu/mag` 50 Hz, `/wheel_speeds` `/vel_raw` `/odom_raw` 25 Hz, `/ground_truth/odom` 50 Hz `world`, `/battery` `/voltage` `/power/current` 10 Hz |
| Duty cycle for the energy test (Lab B) | [`scripts/drive_pattern.py`](scripts/drive_pattern.py) | `python3 ~/labs/week01/scripts/drive_pattern.py` (Ctrl-C to stop; `--cycles N` for N laps) | a 0.9 m square + one turn per 19.3 s lap; sends a zero `Twist` when it ends. Two laps return to within 6 mm of the start |
| Endurance logger (Lab B) | [`scripts/energy_log.py`](scripts/energy_log.py) | see below | stops itself at 9.6 V: mean 2.57 A, 28.6 W, 5.36 Ah, 59.6 Wh, **125 min** from 93 % SoC; writes `energy_log.csv` here |
| Plot of the endurance run | [`scripts/plot_energy.py`](scripts/plot_energy.py) | `python3 ~/labs/week01/scripts/plot_energy.py` | `energy_log.png` (voltage, current, SoC against battery time). A matplotlib `Axes3D` warning is harmless |
| Command-to-measurement latency (Lab C) | [`scripts/step_latency.py`](scripts/step_latency.py) | `python3 ~/labs/week01/scripts/step_latency.py --trials 10` | random step phase; lightly loaded laptop: cmd→ground truth 4–19 ms (mean 12.5), cmd→`/vel_raw` 15–45 ms (mean 30.5); heavy load adds jitter (up to ~100 ms) |

## Lab B – the accelerated endurance test

```bash
# terminal 1: restart the simulator so the robot is at its spawn point
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false
# terminal 2: accelerate the launched battery model 60x (the node accepts this at run time)
ros2 param set /battery time_scale 60.0
# terminal 3: the logger
python3 ~/labs/week01/scripts/energy_log.py --time-scale 60
# terminal 2: the duty cycle (Ctrl-C after the logger has printed its summary)
python3 ~/labs/week01/scripts/drive_pattern.py
ros2 param set /battery time_scale 1.0
```

`--time-scale` must equal the value you set. `load_5v_w` and `buck_efficiency` can be changed the same way (e.g. a 20 W host).

## Lab C – latency commands

```bash
ros2 topic delay /scan          # without -s: ~1.79e9 s (wall clock minus simulated stamp) - a wrong measurement
ros2 topic delay -s /scan       # ~0 (-4..+1 ms): quantised by the 5 ms /clock
ros2 topic pub -r 50 /ping geometry_msgs/msg/PointStamped "{header: {stamp: now, frame_id: ping}}"
ros2 topic delay /ping          # DDS transport on the wall clock: ~1 ms
```

## Remember

* The simulated base has **no command timeout**: stop it with
  `ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"`.
* Every node you start must use simulated time (`--ros-args -p use_sim_time:=true`; the scripts here do it for you).
* Slow camera? Launch with `camera_width:=424 camera_height:=240` (about 17 Hz instead of 2-7 Hz at 848x480 on a laptop without a GPU).
* Label simulated evidence as simulated in your reports.

`commands.md` lists the lecture's commands in order.
