# Week 05 - ROS 2 for Sensor and Actuator Systems

Everything here runs in the module's ROS 2 Humble container against the simulated lab robot. This folder is
mounted in the container at `~/labs/week05`.

```bash
cd docker && docker compose up -d ros2          # then open http://localhost:6080
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false     # terminal 1, wait ~30 s
```

## What is in the folder

| Path | What it is | Laboratory |
|---|---|---|
| `scripts/qos_probe.py` | subscribes with the QoS profile you choose and reports incompatible-QoS events | A |
| `scripts/staleness_demo.py` | 100 Hz publisher + slow consumer: measures sample age against depth / rate (no simulator needed) | A |
| `packages/lab_interfaces/` | ament_cmake package with the custom message `SensorHealth.msg` | B |
| `packages/lab_sensing/` | ament_python package: the `sensor_monitor` node and `launch/monitor_launch.py` | B, C |
| `params/sensor_monitor_params.yaml` | parameters for `sensor_monitor` (use_sim_time, expected_hz, window, thresholds) | B, C |
| `scripts/drive_pattern.py` | drives the scripted ~55 s manoeuvre (settle, 1 m square, lateral out and back, stop) in simulated time | C |
| `scripts/bag_jitter.py` | interval statistics and histogram of one topic in a bag, on the stamp and receive clocks | C |

## How to run it (expected output measured on 21 Sept 2026)

```bash
# Laboratory A
cd ~/labs/week05/scripts
python3 qos_probe.py /imu/data_raw sensor_msgs/msg/Imu --reliability best_effort      # received ~499 messages in 5.0 s
python3 qos_probe.py /imu/data_raw sensor_msgs/msg/Imu --durability transient_local   # INCOMPATIBLE QoS: policy DURABILITY
python3 qos_probe.py /imu/data_raw sensor_msgs/msg/Imu --deadline-ms 20               # INCOMPATIBLE QoS: policy DEADLINE
python3 qos_probe.py /tf_static tf2_msgs/msg/TFMessage --durability volatile          # received 0 messages
python3 staleness_demo.py --depth 10        # median age 0.096 s; depth/rate = 0.100 s; 44 % dropped

# Laboratory B - build the two packages in your workspace
cp -r ~/labs/week05/packages/lab_interfaces ~/labs/week05/packages/lab_sensing ~/ws/src/
cd ~/ws
colcon build --packages-select lab_interfaces && source install/setup.bash
colcon build --packages-select lab_sensing && source install/setup.bash
ros2 run lab_sensing sensor_monitor --ros-args --params-file ~/labs/week05/params/sensor_monitor_params.yaml
ros2 topic echo /sensor_health        # stamp_rate_hz 100.0, accel_rms ~9.78-9.80, healthy: true

# Laboratory C
ros2 launch lab_sensing monitor_launch.py                  # or with_sim:=true to start the simulator too
ros2 bag record -s mcap --use-sim-time -o ~/bags/w5_run1 /imu/data_raw /imu/mag /vel_raw /odom_raw \
  /wheel_speeds /ground_truth/odom /tf /tf_static /cmd_vel /voltage /sensor_health
python3 ~/labs/week05/scripts/drive_pattern.py            # ends with "done - robot stopped"; then Ctrl+C the recorder
ros2 bag info ~/bags/w5_run1                              # ~70 s, ~25 000 messages, ~8.1 MiB
python3 ~/labs/week05/scripts/bag_jitter.py ~/bags/w5_run1 --topic /imu/data_raw   # writes jitter_imu_data_raw.png
```

Keep the bag `~/bags/w5_run1` - Week 6 uses it.

Notes
- The monitor's launch argument is `monitor_params`, not `params_file`: the simulator's launch files already use
  `params_file`, and launch arguments are global.
- `ros2 param set /sensor_monitor expected_hz 50.0` must be written as a float (`50` is refused as INTEGER).
- Everything is simulated: label figures and tables as simulated in your report.
