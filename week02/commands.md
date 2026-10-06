# Week 02 – commands and code from the lecture, in order

Generated from the lecture (Week 2: ROS 2 as Lego – Building Robots from Bricks – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 

```bash
ros2 launch tc70045e_sim sim.launch.py camera:=false      # T1: the robot (Gazebo window opens)
ros2 topic list -t                                         # T2: its studs
ros2 topic hz /scan                                        #     about 5.5 Hz
ros2 topic echo --once /imu/data_raw
```

```bash
ros2 launch ~/labs/week02/launch/lego.launch.py           # T1: robot + rviz2
ros2 run teleop_twist_keyboard teleop_twist_keyboard      # T2: drive - click in T2 first
rqt_graph                                                 # T3
```

```bash
# Ctrl+C everything, then:
ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true
ros2 run teleop_twist_keyboard teleop_twist_keyboard
# when the map looks good:
ros2 run nav2_map_server map_saver_cli \
  -f ~/labs/week02/my_map --ros-args -p use_sim_time:=true
```

```python
def on_cmd(self, cmd):                              # a wanted motion arrives on /cmd_vel_in
    heading = math.atan2(cmd.linear.y, cmd.linear.x)    # which way does it want to go?
    if self.nearest_towards(heading) < stop_distance:   # LiDAR: anything close that way?
        cmd.linear.x = cmd.linear.y = 0.0               # yes: keep turning, stop moving
    self.pub.publish(cmd)                               # pass it on to /cmd_vel
```

```bash
ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true safety:=true
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_in
ros2 topic echo /safety/blocked
ros2 param set /safety_stop stop_distance 0.8
```
