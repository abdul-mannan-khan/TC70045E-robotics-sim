# Week 12 – commands and code from the lecture, in order

Generated from the lecture (Week 12: Multi-Robot Systems, Integration and UAV Outlook – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 1.5 Measuring it: discovery traffic and data age

```bash
# terminal 1
ros2 launch tc70045e_sim multi_robot.launch.py gui:=false

# terminal 2 - the graph
ros2 node list
ros2 topic list | grep robot2
ros2 topic hz /robot2/scan
ros2 topic info /robot2/cmd_vel --verbose | grep -E "Node name|Node namespace|Endpoint type"
ros2 topic echo /robot2/scan --once --field header
```

```bash
# terminals 3 and 4 - one shared frame (the spawn poses), then cross-robot TF
ros2 run tf2_ros static_transform_publisher --x -3.0 --y -0.4 --frame-id world --child-frame-id robot1/odom
ros2 run tf2_ros static_transform_publisher --x 3.0 --y -1.0 --yaw 3.14159 --frame-id world --child-frame-id robot2/odom
# terminal 2
ros2 run tf2_ros tf2_echo robot1/base_footprint robot2/base_footprint
ros2 run tf2_tools view_frames                  # writes frames_<date>.pdf

# one robot only (then stop it: the base has no timeout)
ros2 topic pub -t 3 /robot2/cmd_vel geometry_msgs/msg/Twist "{angular: {z: 0.5}}"
ros2 topic pub -t 3 /robot2/cmd_vel geometry_msgs/msg/Twist "{}"
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/robot1/cmd_vel
```

```text
# domains and discovery
ROS_DOMAIN_ID=$((ROS_DOMAIN_ID + 1)) ros2 node list      # another domain: nothing
python3 ~/labs/week12/scripts/discovery_sniffer.py --seconds 20

# QoS and data age (no simulator needed; pub in one terminal, sub in another)
python3 ~/labs/week12/scripts/qos_lab.py pub
python3 ~/labs/week12/scripts/qos_lab.py sub --depth 10 --work 0.1
python3 ~/labs/week12/scripts/qos_lab.py sub --depth 1 --work 0.1
python3 ~/labs/week12/scripts/qos_lab.py sub --qos best_effort --depth 1 --work 0.1
python3 ~/labs/week12/scripts/qos_lab.py pub --qos best_effort    # + a RELIABLE sub: incompatible

# clock offset (the two static transforms must be running)
python3 ~/labs/week12/scripts/clock_skew_demo.py --offset 0.0
python3 ~/labs/week12/scripts/clock_skew_demo.py --offset 0.1
python3 ~/labs/week12/scripts/clock_skew_demo.py --offset 0.5
python3 ~/labs/week12/scripts/clock_skew_demo.py --offset -0.5
python3 ~/labs/week12/scripts/clock_skew_demo.py --wall-clock
```

## 2.3 The same method in software: the ROS 2 instruments

```bash
# terminal A - the downstream node (shows the symptom, never the cause)
python3 ~/labs/week12/scripts/scan_consumer.py

# terminal B - the stage under test: first healthy, then with a hidden fault
python3 ~/labs/week12/scripts/fault_inject.py --fault none
python3 ~/labs/week12/scripts/fault_inject.py --fault random

# terminal C - the instruments, in bisection order
ros2 node list | grep robot1
ros2 topic info /robot1/scan_filtered --verbose
ros2 topic hz /robot1/scan_filtered
ros2 topic echo /robot1/scan_filtered --field header --once
ros2 param get /robot1/scan_filter use_sim_time
ros2 run tf2_ros tf2_echo robot1/odom robot1/laser_link
cat /tmp/fault_answer.txt                     # only after you have decided
```

## 3.4 Bridging to ROS 2

```bash
docker compose up -d px4      # PX4 SITL + Gazebo, headless; MAVLink on UDP 14540/14550
docker compose up -d ros2     # the browser desktop, if it is not already running
docker compose ps             # both services 'running'
docker compose logs px4 | tail    # wait for "Ready for takeoff!"
```

```bash
# in a terminal inside the desktop at http://localhost:6080
python3 -c "import mavsdk; print('mavsdk ready')"

# talk to the simulated autopilot (note: udpin://, not the deprecated udp://)
python3 - <<'PY'
import asyncio
from mavsdk import System

async def main():
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("connected"); break
    async for h in drone.telemetry.health():
        print("global position ok:", h.is_global_position_ok); break
    async for b in drone.telemetry.battery():
        print("battery %.2f V" % b.voltage_v); break

asyncio.run(main())
PY
```

```python
import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, PositionNedYaw

async def run():
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    async for s in drone.core.connection_state():
        if s.is_connected: break
    async for h in drone.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok: break

    await drone.action.arm()
    await drone.action.takeoff()
    await asyncio.sleep(10)

    # PX4 refuses OFFBOARD unless setpoints are ALREADY streaming. This line is the lesson.
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -3.0, 0.0))
    try:
        await drone.offboard.start()
    except OffboardError as e:
        print("offboard start failed:", e._result.result)
        await drone.action.land(); return

    for north, east in ((2.0, 0.0), (2.0, 2.0), (0.0, 2.0), (0.0, 0.0)):
        await drone.offboard.set_position_ned(PositionNedYaw(north, east, -3.0, 0.0))
        await asyncio.sleep(6)

    async for p in drone.telemetry.position_velocity_ned():
        print("n=%.2f e=%.2f d=%.2f" % (p.position.north_m, p.position.east_m, p.position.down_m)); break

    await drone.offboard.stop()
    await drone.action.land()

asyncio.run(run())
```
