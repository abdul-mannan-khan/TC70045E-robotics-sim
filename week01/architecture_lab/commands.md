# Week 01 – commands and code from the lecture, in order

Generated from the lecture (Week 1: Robot System Architecture, Safety and Toolchain – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 2.1 The four layers

```text
+---------------------------------------------+
| L4 APPLICATION    Nav2, SLAM, perception,   |
|   100 ms - 1 s    your ROS 2 nodes, running |
|                   in a Docker container     |
+---------------------------------------------+
     ^  DDS: topics, services, shared memory
     v
+---------------------------------------------+
| L3 HOST COMPUTER  ARM single-board computer |
|   10 - 100 ms     or NVIDIA Jetson; Linux + |
|                   ROS 2; USB3 to the D455,  |
|                   USB to the 2D LiDAR       |
+---------------------------------------------+
     ^  USB-UART bridge -> UART, 115200 8N1
     v
+---------------------------------------------+
| L2 MICROCONTROLLER e.g. STM32F103 at 72 MHz:|
|   1 - 10 ms       PWM, encoder timers,      |
|                   9-axis IMU on I2C, CAN,   |
|                   SBUS, buzzer, H-bridges   |
+---------------------------------------------+
     ^  PWM / bridge current, encoder pulses
     v
+---------------------------------------------+
| L1 PLANT          4 x encoder gear motors,  |
|   0.1 - 1 ms      mecanum wheels, servos    |
+---------------------------------------------+
```

## 3.1 What the module's container is

```text
services:
  ros2:
    build: .                        # the image is built from the Dockerfile
    image: tc70045e/ros2-lab:humble
    ports:
      - "6080:80"                   # browser desktop (noVNC)
    environment:
      - ROS_DOMAIN_ID=7             # DDS isolation, see 3.3
    volumes:
      - ..:/home/ubuntu/labs        # the repository  -> ~/labs
      - ./workspace:/home/ubuntu/ws # your packages   -> ~/ws
      - ./bags:/home/ubuntu/bags    # your recordings -> ~/bags
    shm_size: "2gb"                 # Gazebo, point clouds
```

## 3.3 ROS 2 Humble, domains and simulated time

```text
# /etc/udev/rules.d/90-robot.rules   (on the HOST)
KERNEL=="ttyUSB*", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", \
  MODE="0660", GROUP="dialout", SYMLINK+="robot_mcu"
KERNEL=="ttyUSB*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", \
  MODE="0660", GROUP="dialout", SYMLINK+="robot_lidar"
```

```bash
# ---- on YOUR laptop, in the student repository ----
cd docker
docker compose up -d ros2      # first time: builds the image (20-40 min)
# then open http://localhost:6080 and open a terminal in that desktop
```

```bash
# ---- terminal 1 (inside the browser desktop): the simulated lab robot ----
printenv ROS_DISTRO ROS_DOMAIN_ID
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false
```

```bash
# ---- terminal 2: audit the graph ----
ros2 node list
ros2 topic list -t
ros2 topic info -v /scan
ros2 topic hz /scan                          # Ctrl-C after ~10 s
ros2 topic echo /scan --once --field header
python3 ~/labs/week01/scripts/topic_audit.py
```

```text
$ ros2 node list
/battery
/gazebo
/imu_driver
/lidar_driver
/magnetometer
/mecanum_base
/robot_state_publisher
/wheel_odometry
$ ros2 topic hz /scan
average rate: 5.375
	min: 0.181s max: 0.217s std dev: 0.00625s window: 55
```

```text
$ ros2 topic info -v /scan          (extract)
Node name: lidar_driver
Topic type: sensor_msgs/msg/LaserScan
Endpoint type: PUBLISHER
  Reliability: RELIABLE
  Durability: VOLATILE
```

```text
$ python3 ~/labs/week01/scripts/topic_audit.py
topic              type            Hz wall  Hz sim  sd ms frame_id     age ms
/scan              LaserScan          5.23    5.49   11.5 laser_link     -1.2
/imu/data_raw      Imu               95.11   99.91    2.2 imu_link       -2.5
/imu/mag           MagneticField     47.58   50.00    3.1 imu_link        0.1
/wheel_speeds      JointState        23.75   24.95    4.7 ''              0.2
/vel_raw           Twist             23.75   24.95    4.7 -               nan
/odom_raw          Odometry          23.75   24.95    4.7 odom            0.5
/ground_truth/odom Odometry          47.59   50.00    3.2 world           0.1
/battery           BatteryState       9.51   10.00    7.8 ''              0.1
/voltage           Float32            9.51   10.00    7.9 -               nan
/power/current     Float32            9.51   10.00    7.8 -               nan
```

```bash
# ---- terminal 2: frames, transforms and the node graph ----
cd ~/labs/week01
ros2 run tf2_tools view_frames --ros-args -p use_sim_time:=true
ros2 run tf2_ros tf2_echo base_footprint laser_link --ros-args -p use_sim_time:=true
rqt_graph
```

```text
At time 0.0
- Translation: [0.020, 0.000, 0.142]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
```

```bash
# ---- terminal 2: first drive ----
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1}}"
#   Ctrl-C after 3 s, then check: is it still moving?
ros2 topic echo /ground_truth/odom --once --field twist.twist.linear
#   STOP - the robot has no command timeout:
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## 5.1 The topology

```text
  3S pack            main
  E_oc, R_int       switch
  11.1 V nominal      |
  12.6 V full   --[ ]--/--+---> 12 V bus ---> 4 H-bridges
  9.6 V alarm             |
                          +--> [BUCK 1] --> 5 V rail
                          |      |-> host computer
                          |      |-> 2D LiDAR, D455 (USB)
                          |      |-> 3V3 LDO -> MCU, IMU
                          |
                          +--> [BUCK 2] --> servo rail
                                 (jumper: 6.8 V or 5 V)
```

## 5.3 Worked example: predicted endurance

```text
mean |v|  = 0.30 x 12 / 19.28          = 0.187 m/s
mean |w|  = 1.0 x 6.283 / 19.28        = 0.326 rad/s
speed changes per lap: 2 (start of leg 1,
  end of leg 4); 0.30 m/s in one 0.1 s model
  step -> 3 m/s^2 for 0.1 s, twice per lap

P_5V,in  = 16.5 / 0.85                 = 19.41 W
P_drive  = 1.5 + 28 x 0.187 + 6 x 0.326
         + 10 x 3 x (2 x 0.1 / 19.28)  =  9.00 W
                                          -------
P_in                                   = 28.4 W
I_bat at a mean 11.1 V = 28.4 / 11.1   = 2.56 A
```

```text
t_run = 5.4 A h / 2.56 A = 2.11 h = 127 minutes of driving this pattern.
```

## 5.4 Conductor and connector drop – a Level 7 trap

```bash
# ---- terminal 2: the live rails ----
ros2 topic echo /power/rails --once        # [V5, I5, P_total]
ros2 topic echo /battery --once
```

```text
data:
- 4.934000015258789
- 3.299999952316284
- 20.91176414489746
```

```bash
# ---- terminal 2 (after relaunching the simulator): accelerate the pack ----
ros2 param set /battery time_scale 60.0
# ---- terminal 3: the logger (stops itself at 9.6 V) ----
python3 ~/labs/week01/scripts/energy_log.py --time-scale 60
# ---- terminal 2: the duty cycle (Ctrl-C when the logger has finished) ----
python3 ~/labs/week01/scripts/drive_pattern.py
ros2 param set /battery time_scale 1.0          # afterwards
```

```text
[energy_log]: battery time  0.16 h   V 11.881   I  2.47 A   P  29.3 W   SoC  86.0 %
[energy_log]: battery time  0.33 h   V 11.716   I  2.50 A   P  29.3 W   SoC  79.5 %
   ...
[energy_log]: battery time  2.00 h   V 10.198   I  2.87 A   P  29.3 W   SoC   7.8 %

--- energy summary (SIMULATED battery model, time_scale 60) ---
logged            125.1 s simulated = 2.08 h battery time
pack voltage      11.85 V -> 9.59 V
state of charge   92.8 % -> 3.5 %
mean current      2.57 A   (min 1.77, max 5.84)
mean power        28.6 W
charge delivered  5.36 Ah   energy 59.6 Wh
ENDURANCE to the 9.6 V alarm: 2.08 h = 125 min (from 93 % SoC)
```

```bash
# ---- terminal 2: the figure for your report ----
python3 ~/labs/week01/scripts/plot_energy.py
#   -> ~/labs/week01/energy_log.png  (voltage, current, SoC against battery time)
```

## 7.3 Bench instruments: the limits LO5 asks about

```bash
# ---- terminal 2 (simulator still running in terminal 1) ----
ros2 topic delay /scan              # Ctrl-C after 5 s - what went wrong?
ros2 topic delay -s /scan           # -s: use simulated time
ros2 topic delay -s /odom_raw
```

```text
$ ros2 topic delay /scan
average delay: 1790014932.138
	min: 1790014932.129s max: 1790014932.150s std dev: 0.00770s window: 16
$ ros2 topic delay -s /scan
average delay: -0.002
	min: -0.004s max: 0.001s std dev: 0.00147s window: 38
$ ros2 topic delay -s /odom_raw
average delay: 0.000
	min: 0.000s max: 0.005s std dev: 0.00045s window: 123
```

```bash
# ---- terminal 3: a wall-clock-stamped test topic ----
ros2 topic pub -r 50 /ping geometry_msgs/msg/PointStamped \
  "{header: {stamp: now, frame_id: ping}}"
# ---- terminal 2 ----
ros2 topic delay /ping              # no -s: both ends use the wall clock
```

```text
average delay: 0.001
	min: 0.000s max: 0.004s std dev: 0.00024s window: 349
```

```bash
# ---- terminal 2: stop /ping (Ctrl-C in terminal 3), then ----
python3 ~/labs/week01/scripts/step_latency.py --trials 10
```

```text
trial  1   cmd->truth   14.0 ms   cmd->vel_raw   40.0 ms
trial  2   cmd->truth    4.0 ms   cmd->vel_raw   30.0 ms
   ...
cmd_vel -> ground truth          mean   12.5 ms   sd   4.5 ms   max   19.0 ms   (n=10)
cmd_vel -> /vel_raw (encoders)   mean   30.5 ms   sd  12.3 ms   max   45.0 ms   (n=10)
```

## 🤖 AI co-pilot: the "derive, then verify" prompt pattern

```text
You are an electronics engineer reviewing a mobile-robot energy budget.

CONTEXT (from my simulated lab robot, ROS 2 Humble, 21 Sep 2026):
  3S Li-ion pack, 6.0 Ah, R_int 0.09 ohm, alarm at 9.6 V
  5 V rail: host 12 W, 2D LiDAR 2.5 W, D455 1.5 W, logic 0.5 W
  5 V buck efficiency 0.85
  drive model: 1.5 W + 28 W per m/s + 6 W per rad/s
  duty cycle: mean |v| 0.187 m/s, mean |w| 0.326 rad/s
  simulated result: mean 2.57 A, 28.6 W, 125 min from 93 % SoC

TASK
1. Recompute the mean input power and pack current, showing formulae.
2. Repeat for a 20 W host and for buck efficiencies of 0.80 and 0.90.
3. List five physical effects this model omits, each with the sign of
   its effect on the endurance of a real robot.
4. Flag any number in my context block that looks physically implausible.

OUTPUT: a table with units in the header, then at most 120 words.
Do not invent any measurement I have not given you.
```
