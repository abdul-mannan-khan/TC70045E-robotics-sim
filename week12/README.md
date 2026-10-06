# Week 12 - Multi-robot systems, integration and UAV outlook

Everything here runs in the module's ROS 2 Humble container (browser desktop at http://localhost:6080).
The repository is mounted at `~/labs`, so the scripts are in `~/labs/week12/scripts`.

```bash
cd docker && docker compose up -d ros2          # on your laptop; add px4 for Lab C
```

## Lab A - two robots, one network

```bash
ros2 launch tc70045e_sim multi_robot.launch.py gui:=false     # robot1 at (-3.0, -0.4), robot2 at (3.0, -1.0) facing west
```

| Script | What it does | Expected output |
|---|---|---|
| `scripts/discovery_sniffer.py` | Listens to DDS discovery multicast (239.255.0.1, port 7400 + 250 x domain) and counts RTPS packets and participants. No root needed. | `N RTPS packets, x packets/s, y B/s, k participants heard (Fast DDS)` |
| `scripts/qos_lab.py` | `pub` sends 1 MB images at 30 Hz; `sub` processes each for 100 ms with a chosen reliability and depth and prints the age of the data it acts on. No simulator needed. | e.g. `... skipped, age p50 ... ms p95 ... ms` every 5 s |
| `scripts/clock_skew_demo.py` | Pretends robot2's scans were stamped by a clock `--offset` seconds off (or by the wall clock with `--wall-clock`) and counts TF lookups into `world` that succeed/fail. Needs the two static `world -> robotN/odom` transforms from the lecture. | `offset +0.200 s: 0 OK, 27 failed  Lookup would require extrapolation into the future ...` |

## Lab B - fault isolation drill

```bash
python3 ~/labs/week12/scripts/scan_consumer.py              # the downstream node: shows the symptom
python3 ~/labs/week12/scripts/fault_inject.py --fault random # partner: injects frame | qos | simtime | stop
cat /tmp/fault_answer.txt                                    # only after you have found it
```

`fault_inject.py` runs `/robot1/scan_filter` (`/robot1/scan` -> `/robot1/scan_filtered`); `scan_consumer.py` runs
`/obstacle_monitor`, which prints scans received, TF lookups OK/failed and the nearest obstacle every 2 s.
Find the fault with `ros2 node list`, `ros2 topic info -v`, `ros2 topic hz`, `ros2 topic echo --field header`,
`ros2 param get ... use_sim_time`, `ros2 run tf2_ros tf2_echo`.

## Lab C - PX4 SITL and MAVSDK (the `px4` service)

| Script | What it does |
|---|---|
| `scripts/px4_connect.py` | connect to PX4 SITL with MAVSDK (`udpin://0.0.0.0:14540`) and read health and battery |
| `scripts/px4_square.py` | arm, take off, fly a 2 m square in offboard mode, land - verified on PX4 SITL 1.17 |

MAVROS is not used: there is no `ros-humble-mavros` binary package. MAVSDK-Python (`mavsdk<4`) is in the image.

## Notes
- Two simulated robots need about twice the CPU of one; keep `gui:=false` and cameras off (the default).
- `tc netem` (packet loss) cannot run in the container: Docker does not grant `NET_ADMIN` by default.
- `commands.md` is generated from the lecture.
