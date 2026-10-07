#!/bin/bash
# Demo video: CARLA WITH ROS 2 - the official CARLA ROS 2 bridge, RViz, and a cruise control written as a ROS 2 node.
# Tutor tool - run in the CARLA container desktop (narration is prepared first, see demo_lib.sh):
#   PREPARE=1 bash ~/labs/tools/demo/carla_ros2_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/carla_ros2_demo.sh /tmp/out.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/carla_ros2_demo.mp4}
E=~/labs/examples/carla
carla-sim stop >/dev/null 2>&1
pkill -f carla_ros_bridge; pkill -f carla_manual_control; pkill -f carla_spawn_objects
rm -f /tmp/cs1.log /tmp/bridge.log /tmp/cruise.log

caption_bar
term T1 960 90 960 240
term T2 960 340 960 240
term T3 960 590 960 240
term T4 960 840 960 240
rec_start "$OUT"

cap "Self-driving car WITH ROS 2: the CARLA ROS 2 bridge turns the car and its sensors into ROS 2 topics" 5 "The self driving car with ROS 2. The CARLA ROS bridge turns the car and its sensors into ordinary ROS 2 topics. After that, a controller is just a ROS 2 node."
cap "Step 1 (T1): start the CARLA server in Town04" 2 "Step one. In terminal one we start CARLA in town four."
run T1 "carla-sim start --town Town04 | tee /tmp/cs1.log" 3
say "CARLA renders on the graphics card with no window of its own. The first start takes up to a minute." 10
wait_for "CARLA is up" /tmp/cs1.log 300
cap "Step 2 (T2): the ROS 2 bridge spawns 'ego_vehicle' with a camera, a LiDAR, GNSS and a speedometer" 2 "Step two. In terminal two we launch the bridge. It spawns our car, called ego vehicle, with a camera, a LiDAR, a GNSS receiver and a speedometer, at the start of a long straight."
run T2 "ros2 launch carla_ros_bridge carla_ros_bridge_with_example_ego_vehicle.launch.py host:=127.0.0.1 timeout:=60 town:=Town04 synchronous_mode:=true spawn_point_ego_vehicle:=\"-365.9,-33.6,0.8,0,0,0.4\" 2>&1 | tee /tmp/bridge.log | grep -v ALSA" 5
say "Note the host address: one two seven dot zero dot zero dot one. The name localhost does not work here." 25
place "CARLA ROS manual control" 0 90 955 540
cap "Step 3 (T3): the car is now a ROS 2 robot - list its topics" 2 "Step three. The car is now a ROS 2 robot. We list its topics."
run T3 "ros2 topic list | grep ego_vehicle | head -16" 6
cap "Step 4: RViz shows the camera image, the LiDAR point cloud and the car's path" 2 "Step four. RViz shows the camera image, the LiDAR point cloud, and the path of the car."
run T3 "clear; rviz2 -d $E/carla.rviz > /dev/null 2>&1 &" 14
place RViz 0 640 955 440
sleep 3
cap "Step 5 (T4): YOUR cruise control as a ROS 2 node - speedometer in, throttle and brake out" 2 "Step five. Our cruise control as a ROS 2 node. It subscribes to the speedometer and publishes throttle and brake on the vehicle control topic."
run T4 "python3 -u $E/03_cruise_control_ros2.py --ros-args -p target_kmh:=40.0 2>&1 | tee /tmp/cruise.log" 5
cap "Watch the speed converge to 40 km/h - in the node's log, the manual control window and RViz" 30 "Watch the speed converge to forty kilometres an hour, in the node's log, in the manual control window, and in RViz."
wait_for "speed 40.0" /tmp/cruise.log 120
sleep 8
cap "Same controller as the Python API version - only the inputs and outputs became ROS 2 topics" 6 "This is the same controller as in the Python version. Only its inputs and outputs became ROS 2 topics."
cap "Your turn: examples/carla/README.md, steps 3 and 4. Add a speed limit that follows a topic." 8 "Your turn. Follow steps three and four in the examples folder. Then make the target speed follow a ROS 2 topic, like a speed limit sign."
rec_stop
ctrlc T4 1; ctrlc T2 4
pkill -f rviz2
run T1 "carla-sim stop" 3
echo "saved $OUT"
