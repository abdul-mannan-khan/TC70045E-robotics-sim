# Week 05 – commands and code from the lecture, in order

Generated from the lecture (Week 5: ROS2 for Sensor and Actuator Systems – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 1.3 Reading a driver critically

```text
self.create_subscription(Odometry, 'ground_truth/odom', self.on_truth, 20)
self.pub_vel  = self.create_publisher(Twist, 'vel_raw', 10)
self.pub_odom = self.create_publisher(Odometry, 'odom_raw', 10)
self.pub_js   = self.create_publisher(JointState, 'wheel_speeds', 10)
```

## 2.1 Domains and discovery

```bash
echo $ROS_DOMAIN_ID                 # expect: 7 in the module container
export ROS_DOMAIN_ID=17             # 17 = your allocated group number
ros2 daemon stop; ros2 daemon start # the daemon caches discovery; restart it
```

## 2.4 Deriving the numbers: size, bandwidth, staleness and latency

```bash
cd docker
docker compose up -d ros2           # first run downloads the image - allow 15-30 min
```

```bash
printenv ROS_DISTRO                 # expect: humble
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false
```

```bash
ros2 node list
ros2 node info /wheel_odometry
ros2 topic list -t
ros2 interface show sensor_msgs/msg/Imu
```

```bash
ros2 topic hz /imu/data_raw          # host (wall) clock
ros2 topic hz -s /imu/data_raw       # simulated clock (-s = --use-sim-time)
ros2 topic hz /clock                 # 200 Hz x RTF
```

```bash
ros2 topic bw /imu/data_raw
ros2 topic bw -w 1000 /imu/data_raw  # a 1000-message window
ros2 topic delay -s /imu/data_raw
ros2 topic hz -s /odom_raw
ros2 topic hz /voltage
```

```bash
ros2 topic info /imu/data_raw --verbose
ros2 topic info /tf_static --verbose
```

```bash
# terminal A
ros2 topic pub /qos_demo std_msgs/msg/Int32 "data: 66" --qos-reliability best_effort -r 10
# terminal B - incompatible request: expect NO data and one warning
ros2 topic echo /qos_demo --qos-reliability reliable
# terminal C - compatible request: expect data at 10 Hz
ros2 topic echo /qos_demo --qos-reliability best_effort
```

```bash
cd ~/labs/week05/scripts
python3 qos_probe.py /imu/data_raw sensor_msgs/msg/Imu --reliability best_effort
python3 qos_probe.py /imu/data_raw sensor_msgs/msg/Imu --durability transient_local
python3 qos_probe.py /imu/data_raw sensor_msgs/msg/Imu --deadline-ms 20
python3 qos_probe.py /tf_static tf2_msgs/msg/TFMessage --durability volatile
python3 qos_probe.py /tf_static tf2_msgs/msg/TFMessage --durability transient_local
```

```bash
python3 staleness_demo.py --depth 1
python3 staleness_demo.py --depth 10
python3 staleness_demo.py --depth 100 --seconds 12
```

## 4.1 Step 1 – the custom interface

```bash
cd ~/ws/src
ros2 pkg create lab_interfaces --build-type ament_cmake --dependencies std_msgs
ros2 pkg create lab_sensing --build-type ament_python \
  --dependencies rclpy sensor_msgs geometry_msgs std_msgs lab_interfaces
```

```text
std_msgs/Header header
float32 imu_rate_hz        # arrival rate at this node, host (wall) clock
float32 imu_jitter_ms      # std dev of the arrival interval, host clock
float32 stamp_rate_hz      # rate from the header stamps (sensor clock)
float32 stamp_jitter_ms    # std dev of the header-stamp interval
float32 accel_rms          # RMS |a| over the window, m/s^2
float32 gyro_rms           # RMS |w| over the window, rad/s
float32 body_speed         # sqrt(vx^2 + vy^2) from /vel_raw, m/s
float32 battery_v          # latest /voltage sample, V
uint32  samples            # samples in the window
uint32  missed             # samples expected from the stamps but not received
bool    healthy            # stamp rate within tolerance AND battery OK
```

```text
find_package(rosidl_default_generators REQUIRED)
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/SensorHealth.msg"
  DEPENDENCIES std_msgs
)
ament_export_dependencies(rosidl_default_runtime)
```

```text
<buildtool_depend>rosidl_default_generators</buildtool_depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

## 4.2 Step 2 – the node

```text
p = self.declare_parameter
imu_topic = p('imu_topic', '/imu/data_raw').value
self.window_s = float(p('window_s', 2.0).value)
self.expected_hz = float(p('expected_hz', 100.0).value)
self.tol = float(p('rate_tolerance', 0.10).value)     # +/- 10 %
self.vmin = float(p('battery_min_v', 10.5).value)

sensor_qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                        history=HistoryPolicy.KEEP_LAST, depth=5)
state_qos = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                       history=HistoryPolicy.KEEP_LAST, depth=1)
health_qos = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                        history=HistoryPolicy.KEEP_LAST, depth=1,
                        durability=DurabilityPolicy.TRANSIENT_LOCAL)
```

```text
self.create_subscription(Imu, imu_topic, self.imu_cb, sensor_qos)
self.create_subscription(Twist, '/vel_raw', self.vel_cb, sensor_qos)
self.create_subscription(Float32, '/voltage', self.volt_cb, state_qos)
self.pub = self.create_publisher(SensorHealth, '/sensor_health', health_qos)
self.create_timer(1.0 / report_hz, self.report)
self.add_on_set_parameters_callback(self.on_set)

def on_set(self, params):
    for prm in params:
        if prm.name == 'expected_hz' and prm.value <= 0.0:
            return SetParametersResult(successful=False,
                                       reason='expected_hz must be > 0')
        if prm.name in self.TUNABLE:
            setattr(self, self.TUNABLE[prm.name], float(prm.value))
    return SetParametersResult(successful=True)
```

```python
def imu_cb(self, msg):
    now = time.monotonic()                    # host clock
    stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
    la, av = msg.linear_acceleration, msg.angular_velocity
    self.win.append((now, stamp, math.sqrt(la.x**2 + la.y**2 + la.z**2),
                     math.sqrt(av.x**2 + av.y**2 + av.z**2)))
    while now - self.win[0][0] > self.window_s:
        self.win.popleft()
```

```text
arr, stp, acc, gyr = zip(*self.win)
m_arr, s_arr = mean_std([b - a for a, b in zip(arr, arr[1:])])
m_stp, s_stp = mean_std([b - a for a, b in zip(stp, stp[1:])])
m.imu_rate_hz = float(1.0 / m_arr)
m.imu_jitter_ms = float(s_arr * 1e3)
m.stamp_rate_hz = float(1.0 / m_stp)
m.stamp_jitter_ms = float(s_stp * 1e3)
m.missed = max(0, round((stp[-1] - stp[0]) * self.expected_hz) + 1 - n)
rate_ok = abs(m.stamp_rate_hz - self.expected_hz) <= self.tol * self.expected_hz
batt_ok = not math.isnan(m.battery_v) and m.battery_v >= self.vmin
m.healthy = bool(rate_ok and batt_ok)
```

## 4.3 Step 3 – build, source, run

```bash
cp -r ~/labs/week05/packages/lab_interfaces ~/labs/week05/packages/lab_sensing ~/ws/src/
cd ~/ws
colcon build --packages-select lab_interfaces
source install/setup.bash
ros2 interface show lab_interfaces/msg/SensorHealth
colcon build --packages-select lab_sensing
source install/setup.bash
```

```bash
ros2 run lab_sensing sensor_monitor --ros-args \
  --params-file ~/labs/week05/params/sensor_monitor_params.yaml

ros2 topic echo /sensor_health
ros2 param list /sensor_monitor
ros2 param set /sensor_monitor expected_hz 50.0     # watch healthy flip to False
ros2 param set /sensor_monitor expected_hz 100.0
```

```text
imu_rate_hz: 99.83
imu_jitter_ms: 0.311
stamp_rate_hz: 100.0
stamp_jitter_ms: 2.09e-11
accel_rms: 9.784
gyro_rms: 0.00429
body_speed: 0.0
battery_v: 12.135
samples: 200
missed: 0
healthy: true
```

## 5.1 Launch: one command, every time

```text
DeclareLaunchArgument('monitor_params', default_value=DEFAULT_PARAMS),
DeclareLaunchArgument('with_sim', default_value='false'),
IncludeLaunchDescription(PythonLaunchDescriptionSource(sim_launch),
    launch_arguments={'gui': 'false', 'camera': 'false'}.items(),
    condition=IfCondition(LaunchConfiguration('with_sim'))),
Node(package='lab_sensing', executable='sensor_monitor', name='sensor_monitor',
     parameters=[LaunchConfiguration('monitor_params'),
                 {'expected_hz': LaunchConfiguration('expected_hz')}]),
```

```bash
ros2 launch lab_sensing monitor_launch.py                  # simulator already running
ros2 launch lab_sensing monitor_launch.py with_sim:=true   # everything in one command
```

## 5.2 TF2: the frames your data live in

```text
map  --->  odom  --->  base_footprint  --->  base_link  --->  imu_link
                                                    +--->  laser_link
                                                    +--->  camera_link ---> camera_color_optical_frame
                                                    +--->  wheel_fl_link ... wheel_rr_link
```

```bash
ros2 run tf2_tools view_frames            # writes frames_<date>.pdf - a ready-made figure
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo base_footprint imu_link
```

## 5.3 rosbag2: the raw data behind your figures

```bash
ros2 bag record -s mcap --use-sim-time -o ~/bags/w5_run1 \
  /imu/data_raw /imu/mag /vel_raw /odom_raw /wheel_speeds /ground_truth/odom \
  /tf /tf_static /cmd_vel /voltage /sensor_health
ros2 bag info ~/bags/w5_run1
ros2 bag play ~/bags/w5_run1 --clock 200 --topics /imu/data_raw /vel_raw /voltage
```

```bash
python3 ~/labs/week05/scripts/drive_pattern.py
```

```bash
python3 ~/labs/week05/scripts/bag_jitter.py ~/bags/w5_run1 --topic /imu/data_raw
python3 ~/labs/week05/scripts/bag_jitter.py ~/bags/w5_run1 --topic /odom_raw
```

```text
Files:             w5_run1_0.mcap
Bag size:          8.1 MiB
Storage id:        mcap
Duration:          69.775000000s
Messages:          24937
Topic: /imu/data_raw     | Count: 6978     Topic: /ground_truth/odom | Count: 3489
Topic: /imu/mag          | Count: 3489     Topic: /cmd_vel           | Count: 3164
Topic: /odom_raw         | Count: 1744     Topic: /vel_raw           | Count: 1744
Topic: /wheel_speeds     | Count: 1744     Topic: /tf                | Count: 1745
Topic: /voltage          | Count: 698      Topic: /sensor_health     | Count: 141
Topic: /tf_static        | Count: 1
```

## 5.4 rqt and rviz2 as figure sources

```bash
ros2 run rqt_graph rqt_graph                # node/topic graph - Figure 1 of your Method
ros2 run rqt_plot rqt_plot                  # e.g. /sensor_health/stamp_rate_hz
ros2 run rqt_reconfigure rqt_reconfigure    # live parameter editing
rviz2                                       # Fixed Frame odom; add TF, LaserScan, Odometry
```

## 🤖 AI co-pilot

```text
You are reviewing a ROS 2 Humble rclpy node (pasted below) that measures
the publication rate and jitter of sensor_msgs/Imu on two clocks.

1. List every rclpy API call and say whether it exists in Humble, with the
   exact module path. Flag anything that is Iron-or-later, Foxy-only or ROS 1.
2. The IMU subscription is BEST_EFFORT/KEEP_LAST/5 and the publisher offers
   RELIABLE/VOLATILE. Do they match under the DDS request/offer rules?
3. Identify any unit error, any float/int error that would fail message
   assignment, and any place the window can grow without bound.
Answer as a table. Do not rewrite the code.
```
