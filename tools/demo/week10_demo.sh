#!/bin/bash
# Week 10 demo video: drones WITH ROS 2 - the two bridges, RViz, take-off/cmd_vel/land from ROS 2, then the mission
# node (solution) and its watchdog. Tutor tool - run in the drone container desktop (narration prepared first):
#   PREPARE=1 bash ~/labs/tools/demo/week10_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week10_demo.sh /tmp/w10.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week10_demo.mp4}
S=~/labs/week10/scripts
SOL=~/labs/solutions/week10/mission_node.py
drone-sim stop >/dev/null 2>&1
rm -f /tmp/w10demo_*.log
place_sim() { for i in 1 2 3; do place Blocks 0 90 955 540; sleep 1; done; }

caption_bar
term T1 960 90 960 240
term T2 960 340 960 240
term T3 960 590 960 240
term T4 960 840 960 240
rec_start "$OUT"

cap "Week 10 demo - drones WITH ROS 2: two bridges make AirSim and PX4 ordinary ROS 2 topics and services" 5 "Week ten demo. Drones with ROS 2. Two bridge nodes turn the simulator and the autopilot into ordinary ROS 2 topics and services. After that, a mission is just a ROS 2 node."
cap "A1 (T1): start the blocks world" 2 "Activity one. In terminal one we start the blocks world."
run T1 "drone-sim start --world blocks | tee /tmp/w10demo_sim.log" 3
say "AirSim and PX4 start together. This takes about a minute." 30
wait_for "ready for take-off" /tmp/w10demo_sim.log 240
place_sim
sleep 8
cap "T2: the AirSim bridge - camera, odometry, IMU, GPS become ROS 2 topics" 2 "In terminal two, the AirSim bridge. Camera, odometry, IMU and GPS become ROS 2 topics."
run T2 "python3 $S/03_airsim_ros2_bridge.py 2>&1 | tee /tmp/w10demo_b3.log" 6
cap "T3: the PX4 bridge - take-off and land services and /drone/cmd_vel go to the autopilot" 2 "In terminal three, the PX4 bridge. Take off and land services, and a velocity command topic, go to the autopilot."
run T3 "python3 $S/04_px4_ros2_bridge.py 2>&1 | tee /tmp/w10demo_b4.log" 10
cap "T4: RViz - the front camera and the map -> base_link transform" 2 "In terminal four, RViz: the front camera, and the drone's transform."
run T4 "rviz2 -d $S/airsim.rviz > /dev/null 2>&1 &" 12
place RViz 0 640 955 440
run T4 "clear; ros2 topic list | grep drone" 6
cap "A2 (T4): take off with a ROS 2 service call, fly with /drone/cmd_vel, land" 2 "Activity two. Take off with an ordinary ROS 2 service call."
run T4 "clear; ros2 service call /drone/takeoff std_srvs/srv/Trigger" 4
say "The drone arms and climbs to five metres." 15
run T4 "clear; ros2 topic pub -r 10 /drone/cmd_vel geometry_msgs/msg/Twist \"{linear: {x: 1.0}}\"" 6
ctrlc T4 3
say "When the commands stop, the bridge holds the drone still. A safe default." 3
run T4 "clear; ros2 service call /drone/land std_srvs/srv/Trigger" 4
say "And it lands." 15
cap "Your activity: mission_node.py - rotate into the body frame, a FRESH photo when still, a watchdog" 4 "Your activity: the mission node. Three to do's. Rotate the map frame error into the body frame. Take a fresh photo when the drone is still. And a watchdog that lands when data stops. Here is the solution."
run T4 "clear; python3 -u $SOL 2>&1 | grep -v INFO | tee /tmp/w10demo_sol.log" 5
cap "A 10 m square, a photo of the middle at each corner (real time)" 30 "A ten metre square. At each corner the drone stops, turns to the middle, and takes a photo. This is real time."
wait_for RESULT /tmp/w10demo_sol.log 240
sleep 8
cap "Watchdog test: start the mission again, then Ctrl+C on the AirSim bridge (T2) in flight" 2 "Now the watchdog test. We start the mission again, and stop the AirSim bridge in flight."
run T4 "clear; python3 -u $SOL 2>&1 | grep -v INFO | tee /tmp/w10demo_wd.log" 5
wait_for "waypoint 1/" /tmp/w10demo_wd.log 120
sleep 2
ctrlc T2 2
cap "No camera image for 2 s - WATCHDOG - the drone lands instead of hovering blind" 15 "No new camera image for two seconds. The watchdog fires, and the drone lands, instead of hovering blind."
wait_for RESULT /tmp/w10demo_wd.log 120
sleep 5
cap "Your turn: week10/README.md - A1-A3, then the three TODOs in mission_node.py. Try first, then compare." 8 "Your turn. Follow the week ten read me, activities one to three, then the three to do's in the mission node. Try first, then compare with the solution."
rec_stop
ctrlc T3 2; pkill -f rviz2
run T1 "drone-sim stop" 4
echo "saved $OUT"
