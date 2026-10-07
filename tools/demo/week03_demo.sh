#!/bin/bash
# Week 3 demo video: the navigation brick - from a map to autonomous delivery (Nav2). Tutor tool - run in the
# container desktop (narration is prepared first, see demo_lib.sh):
#   PREPARE=1 bash ~/labs/tools/demo/week03_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week03_demo.sh /tmp/w3.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week03_demo.mp4}
S=~/labs/week03/scripts
pkill -f gzserver; pkill -f gzclient; sleep 2
rm -f /tmp/w3_*.log
place_views() {   # Gazebo (the simulated world) top left, RViz (what the robot knows) bottom left
    for i in 1 2 3; do place Gazebo 0 90 955 495; place RViz 0 590 955 490; sleep 1; done; }

caption_bar
term T1 960 90 960 300
term T2 960 400 960 330
term T3 960 740 960 340
rec_start "$OUT"

cap "Week 3 demo - the navigation brick: from a map to autonomous delivery" 5 "Week three demo. The navigation brick. We give the robot the map from week two, it works out where it is, and then it drives itself to any goal we give it."
cap "Step 1 (T1): one launch file - robot (Gazebo) + map + AMCL + Nav2 + RViz" 2 "Step one. In terminal one, one launch file starts five bricks: the robot in Gazebo, the saved map, AMCL for localisation, the Nav2 navigation stack, and RViz."
run T1 "ros2 launch ~/labs/week03/launch/nav.launch.py gui:=true 2>&1 | tee /tmp/w3_nav.log" 30
place_views
say "Gazebo, top left, is the real world of the simulation. RViz, below, shows what the robot knows: the saved map, the laser in red, and the blue arrows of AMCL." 3
cap "Step 2 (T2): where am I? AMCL matches the laser to the map - the blue particle cloud shrinks" 2 "Step two. Where am I? AMCL keeps hundreds of guesses, the blue arrows, and keeps the ones whose laser view matches the map. The launch file told it that the robot starts at the origin."
run T2 "ros2 topic echo --once /amcl_pose --field pose.pose.position" 5
cap "Step 3 (T2): send a goal from Python - through the doorway into the other room" 2 "Step three. We send a goal from a Python script: the doorway between the two rooms. Clicking two D goal pose in RViz does exactly the same."
run T2 "clear; python3 -u $S/go_to.py 4.0 -1.0 0 | tee /tmp/w3_goal1.log" 4
cap "Green: the global plan on the map. Orange: the local plan the controller is following right now" 6 "The green line is the global plan, computed on the map. The orange line is the local plan the controller follows right now, using the latest laser data."
wait_for RESULT /tmp/w3_goal1.log 120
sleep 3
cap "Step 4 (T3): drop a box on the way back - it is NOT on the map" 2 "Step four. Something new appears: we drop a box on the way back. The map does not know about it."
run T3 "python3 $S/drop_box.py 2.0 -1.0" 5
cap "The laser sees the box: it appears in the costmap, and Nav2 plans round it" 2 "The laser sees the box, it appears in the costmap, and Nav2 plans a way round it."
run T2 "clear; python3 -u $S/go_to.py 0.0 0.0 180 | tee /tmp/w3_goal2.log" 4
wait_for RESULT /tmp/w3_goal2.log 120
sleep 3
run T3 "clear; python3 $S/drop_box.py --remove" 4
cap "Step 5 (T3): the costmap - walls are grown by the inflation radius so the robot keeps its distance" 2 "Step five. The costmap. Every wall and obstacle is grown by the inflation radius, so the planner keeps the robot away from them."
run T3 "clear; ros2 param get /global_costmap/global_costmap inflation_layer.inflation_radius" 5
say "Point three five metres. Make it smaller and the robot cuts closer to the walls. Make it bigger and narrow doorways close." 3
cap "Your activity: patrol.py - a security patrol through both rooms. As given it does nothing (three TODOs)" 2 "Your activity is a security patrol through both rooms. The patrol script you are given has three to do's, so at first it does nothing."
run T2 "clear; python3 $S/patrol.py" 12
cap "The worked solution: five waypoints, each reached or reported, then a RESULT line" 2 "Here is the worked solution: five waypoints through both rooms. Each one is reached, or reported and skipped, and the patrol ends with a result line."
run T2 "clear; python3 -u ~/labs/solutions/week03/patrol.py 1 | tee /tmp/w3_patrol.log" 4
cap "Watch the patrol in Gazebo and RViz (real time)" 30 "Watch the patrol in Gazebo and in RViz. This is real time."
wait_for RESULT /tmp/w3_patrol.log 400
sleep 4
cap "Your turn: week03/README.md - activities A1-A5, then patrol.py. Try first, then compare with the solution." 8 "Your turn. Follow the week three read me, activities one to five, then write your patrol. Try first, then compare with the solution."
rec_stop
ctrlc T1 8; pkill -f gzserver; pkill -f gzclient
echo "saved $OUT"
