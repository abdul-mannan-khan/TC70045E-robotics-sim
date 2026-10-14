#!/bin/bash
# Week 7 demo video: RGB-D SLAM with the D455 alone, then Nav2 on the camera map. Tutor tool - run in the container
# desktop (narration is prepared first, see demo_lib.sh):
#   PREPARE=1 bash ~/labs/tools/demo/week07_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week07_demo.sh /tmp/w7.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week07_demo.mp4}
W=~/labs/week07
SOL=\$HOME/labs/solutions/week07/rtabmap_camera.yaml
pkill -f gzserver; pkill -f gzclient; sleep 2
rm -f /tmp/w7demo_*.log
place_views() {   # Gazebo (the simulated world) top left, RViz (what the robot knows) bottom left
    for i in 1 2 3; do place Gazebo 0 90 955 495; place RViz 0 590 955 490; sleep 1; done; }

caption_bar
term T1 960 90 960 300
term T2 960 400 960 330
term T3 960 740 960 340
rec_start "$OUT"

cap "Week 7 demo - RGB-D SLAM with the D455 alone, then Nav2 on the camera's map" 5 "Week seven demo. The LiDAR is switched off. The robot maps the lab with the D455 camera alone, then navigates on that map."
cap "Step 1 (T1): robot + D455 + RTAB-Map, camera only (solution settings), and drive the 24 m circuit" 2 "Step one. In terminal one: the robot, the camera, and RTAB-Map with camera-only settings. Drive true drives the same circuit as in week four."
run T1 "ros2 launch $W/launch/rgbd_nav.launch.py mode:=mapping drive:=true config:=$SOL 2>&1 | tee -i /tmp/w7demo_map.log" 35
place_views
say "Gazebo, top left. RViz, below: no red laser this week. The map is drawn from the coloured depth points of the camera." 3
cap "Step 2 (T3): what changed in the settings - camera only, visual registration, strict loop closures" 2 "Step two. Your activity changes three things in the RTAB-Map settings."
run T3 "clear; diff $W/config/rtabmap_camera.yaml ~/labs/solutions/week07/rtabmap_camera.yaml | grep -E '^[<>] +(subscribe_scan|Reg/Strategy|Vis/MinInliers|RGBD/OptimizeMaxError)' | cut -c1-60" 4
say "One. Subscribe scan false: no LiDAR. Two. Registration strategy zero: match image features and depth, because without a scan there is nothing for I C P to match. Three. Strict loop closures: twenty matched features, and reject a closure that bends the graph too much." 3
cap "A loop closure straightens the map. A WRONG one (two places that look alike) bends all of it - be strict" 25 "A loop closure, I have been here before, straightens the map. A wrong one, two places that look alike, bends all of it. In one of our test runs with loose settings the room came out thirteen metres deep instead of eight."
cap "Watch the walls in RViz: the camera sees only in front, and its depth noise grows with distance" 25 "Watch the walls in RViz. The camera sees only in front of the robot, and its depth noise grows with distance squared, so walls are drawn thicker than with the LiDAR."
wait_for "max error" /tmp/w7demo_map.log 500
sleep 2
cap "End of the circuit (T1): small error at the end, but tens of cm during the drive (LiDAR: 2 cm)" 8 "The circuit is finished. The error at the end is small, because the loop closure at the start pulls the graph straight. But look at the R M S error: during the drive the robot was tens of centimetres off. With the LiDAR it was two."
ctrlc T1 10
cap "Step 3 (T1): localisation mode - the saved map is loaded, frozen, and places are recognised" 2 "Step three. Localisation mode. RTAB-Map loads the saved map and only recognises places. Nav2 is started on top, with the depth camera as its only obstacle sensor."
run T1 "clear; ros2 launch $W/launch/rgbd_nav.launch.py mode:=localization nav:=true config:=$SOL 2>&1 | tee -i /tmp/w7demo_nav.log" 40
place_views
cap "Step 4 (T2): three Nav2 goals on the camera map - and how far from each goal the robot REALLY stopped" 2 "Step four. Three Nav2 goals on the camera map. The script also prints how far from each goal the robot really stopped, measured against the simulator's truth."
run T2 "clear; python3 $W/scripts/three_goals.py 2>&1 | grep -v INFO | tee -i /tmp/w7demo_goals.log" 5
cap "Nav2: the global costmap is the camera map, the local costmap fills only in front of the robot" 25 "Look at the costmaps. The global costmap is the camera's map. The local costmap fills only in front of the robot, where the camera looks."
wait_for "RESULT" /tmp/w7demo_goals.log 300
sleep 2
run T3 "clear; timeout 5 ros2 run tf2_ros tf2_echo map odom" 9
say "Terminal three: the transform from map to odom exists - RTAB-Map recognised places from the camera images and put the robot on the stored map." 2
cap "Result (T2): goals reached, and the true stopping distance for each" 8 "Here is the result: which goals were reached, and how far from each the robot really stopped."
cap "Your turn: week07/README.md - A1-A3, then the three TODOs in rtabmap_camera.yaml and three goals." 8 "Your turn. Follow the week seven read me, activities one to three, then the three to do's in the RTAB-Map settings, and navigate to the three goals on your own map."
rec_stop
ctrlc T1 8; pkill -f gzserver; pkill -f gzclient
echo "saved $OUT"
