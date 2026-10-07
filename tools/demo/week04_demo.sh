#!/bin/bash
# Week 4 demo video: add a sensor, upgrade the SLAM - LiDAR + D455 camera, slam_toolbox -> RTAB-Map. Tutor tool - run
# in the container desktop (narration is prepared first, see demo_lib.sh). Needs the A2 and A3 maps in ~/maps
# (w4_toolbox, w4_lidar) for the final comparison:
#   PREPARE=1 bash ~/labs/tools/demo/week04_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week04_demo.sh /tmp/w4.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week04_demo.mp4}
W=~/labs/week04
pkill -f gzserver; pkill -f gzclient; sleep 2
rm -f /tmp/w4demo_*.log
place_views() {   # Gazebo (the simulated world) top left, RViz (what the robot knows) bottom left
    for i in 1 2 3; do place Gazebo 0 90 955 495; place RViz 0 590 955 490; sleep 1; done; }

caption_bar
term T1 960 90 960 300
term T2 960 400 960 330
term T3 960 740 960 340
rec_start "$OUT"

cap "Week 4 demo - add a sensor, upgrade the SLAM: LiDAR + D455 depth camera, RTAB-Map" 5 "Week four demo. Add a sensor, upgrade the SLAM. The robot gets a second sensor, a RealSense D455 depth camera, and a SLAM system that can use both sensors: RTAB-Map."
cap "The problem: the LiDAR sees one flat slice, 14 cm above the floor" 2 "Here is the problem. The two D LiDAR sees one flat slice of the world, fourteen centimetres above the floor. A low step, or a table top, is not in that slice."
cap "Step 1 (T1): robot + D455 + RTAB-Map (solution settings) + RViz, and drive the 24 m circuit" 2 "Step one. In terminal one, one launch file starts the robot in Gazebo with its camera, RTAB-Map with the solution settings, and RViz. Drive true makes the robot drive the same twenty four metre circuit every time."
run T1 "ros2 launch $W/launch/slam.launch.py slam:=rtabmap config:=\$HOME/labs/solutions/week04/rtabmap.yaml drive:=true 2>&1 | tee /tmp/w4demo_slam.log" 35
place_views
say "Gazebo, top left, is the simulated world. RViz, below, shows what the robot knows: the map, the laser in red, and the coloured points of the depth camera." 3
cap "Step 2 (T2): the D455 brick - colour + depth, paired by rgbd_sync on /rgbd_image" 2 "Step two. The D455 brick. Its colour and depth images are paired, picture by picture, and published on slash R G B D image."
run T2 "timeout 8 ros2 topic hz /rgbd_image" 10
cap "Red: one laser slice. Coloured points: a 3D surface - floor, walls, furniture" 6 "Compare the two sensors in RViz. The laser gives one ring of red points. The depth camera gives a three dimensional surface in front of the robot: the floor, the walls and the sides of the furniture."
cap "Step 3 (T3): what changed in the settings - three lines (your activity)" 2 "Step three. Your activity is to switch the camera on in the RTAB-Map settings. Three lines change. Here they are."
run T3 "clear; diff $W/config/rtabmap.yaml ~/labs/solutions/week04/rtabmap.yaml | grep -E '^[<>] +(subscribe_rgbd|Grid/Sensor|Grid/MaxGroundHeight)' | cut -c1-40" 4
say "Subscribe R G B D: use the camera. Grid sensor one: the camera draws the map, while the LiDAR still corrects the robot's position. And max ground height: points lower than four centimetres are floor." 3
cap "Why Grid/Sensor 1, not 2? With 2 the LiDAR beam passes OVER the step and marks it free - erasing it" 7 "Why does only the camera draw the map? With both, the LiDAR beam passes over the step and under the table, reports nothing there, many times a second, and erases what the camera saw. Fusing sensors needs thought."
cap "Watch Gazebo: the yellow step (top middle of the left room) and the table (bottom right room)" 25 "While the robot drives, watch the yellow step, near the top of the left room, and the wooden table in the right room. In RViz they appear in the map as black cells."
cap "The map grows node by node: RTAB-Map adds a node every 10 cm and checks for loop closures" 25 "RTAB-Map adds a node to its graph every ten centimetres, with the laser scan and the camera picture, and keeps checking whether it has been here before. That is a loop closure."
wait_for "RMS error" /tmp/w4demo_slam.log 400
sleep 2
cap "End of the circuit: SLAM error against the truth (T1)" 6 "The circuit is finished. Terminal one prints the error against the true position. The SLAM pose is within millimetres at the end, while wheel odometry alone is more than a metre off."
cap "Step 4 (T2): save the map, then score it against the true world" 2 "Step four. Save the map, and score it against the true world, together with the two LiDAR-only maps from activities two and three."
run T2 "clear; ros2 run nav2_map_server map_saver_cli -f ~/maps/w4_lidar_d455 --ros-args -p use_sim_time:=true 2>&1 | grep -E 'saved success'" 2
sleep 12
run T2 "clear; python3 $W/scripts/map_check.py ~/maps/w4_toolbox.yaml ~/maps/w4_lidar.yaml ~/maps/w4_lidar_d455.yaml | grep -E 'object|low_step|table_top|phantom' | cut -c1-94" 4
cap "Low step and table top: MISSED by both LiDAR maps, SEEN with the D455" 8 "Look at the first two lines. The low step and the table top are missed by both LiDAR maps, slam toolbox and RTAB-Map, and seen only in the map that uses the D455."
cap "The cost: about ten times the CPU and memory of slam_toolbox, slightly thicker walls, gaps outside the camera's 87 degree view" 6 "The camera has a cost: about ten times the processing and memory of slam toolbox, slightly thicker walls because depth noise grows with distance squared, and gaps where the camera never looked."
cap "Your turn: week04/README.md - activities A1-A4, then the three TODOs in rtabmap.yaml. Try first, then compare." 8 "Your turn. Follow the week four read me, activities one to four, then the three to do's in the RTAB-Map settings, and score your map. Try first, then compare with the solution."
rec_stop
ctrlc T1 8; pkill -f gzserver; pkill -f gzclient
echo "saved $OUT"
