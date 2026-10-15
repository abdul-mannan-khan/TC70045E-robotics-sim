#!/bin/bash
# Week 8 demo video: autonomous exploration - frontiers + Nav2 on a growing map. Tutor tool - run in the container
# desktop (narration is prepared first, see demo_lib.sh):
#   PREPARE=1 bash ~/labs/tools/demo/week08_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week08_demo.sh /tmp/w8.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week08_demo.mp4}
W=~/labs/week08
pkill -f gzserver; pkill -f gzclient; sleep 2
rm -f /tmp/w8demo_*.log
place_views() {   # Gazebo (the simulated world) top left, RViz (what the robot knows) bottom left
    for i in 1 2 3; do place Gazebo 0 90 955 495; place RViz 0 590 955 490; sleep 1; done; }

caption_bar
term T1 960 90 960 300
term T2 960 400 960 330
term T3 960 740 960 340
rec_start "$OUT"

cap "Week 8 demo - autonomous exploration: the robot maps the lab by itself, choosing where to go next" 5 "Week eight demo. Autonomous exploration. The robot starts with no map, and decides by itself where to go next, until nothing is left to explore."
cap "Step 1 (T1): robot + slam_toolbox (empty map, laser used to 3.5 m) + Nav2 + RViz + coverage log" 2 "Step one. In terminal one: the robot, slam toolbox starting from an empty map, Nav2, RViz, and a coverage log. The laser is used only up to three and a half metres, so the robot has to go places to see them."
run T1 "ros2 launch $W/launch/explore.launch.py 2>&1 | tee -i /tmp/w8demo_launch.log" 30
place_views
say "Gazebo, top left. RViz, below: the map is almost empty. Grey is unknown." 3
cap "Step 2 (T2): the explorer - frontiers (free cells next to unknown ones), choose big AND near, send to Nav2" 2 "Step two. In terminal two, the explorer: the solution of this week's activity. It finds the frontiers, the free cells next to unknown ones, chooses one that is big and near, and sends it to Nav2 as a goal."
run T2 "python3 ~/labs/solutions/week08/explorer.py --ros-args -p use_sim_time:=true 2>&1 | grep --line-buffered -v INFO | tee -i /tmp/w8demo_explorer.log" 5
cap "Watch RViz: every goal pushes the edge of the known map further out" 25 "Watch RViz. Every goal pushes the edge of the known map further out. Nav2 plans through unknown space, because the map is still growing."
cap "Terminal one prints the explored area every 30 s - the lab is about 80 square metres" 25 "Terminal one prints the explored area every thirty seconds. The whole lab is about eighty square metres."
cap "A goal already tried is never chosen again - some frontiers can never be resolved" 25 "Every goal that was tried is remembered. Some frontiers can never be resolved, for example unknown space behind an obstacle, and without that memory the robot would be sent there again and again."
wait_for "RESULT" /tmp/w8demo_explorer.log 500
sleep 2
cap "Finished (T2): no frontier left - the robot KNOWS the map is complete" 8 "Finished. No frontier left: the robot knows the map is complete, and it stops. A wandering robot never knows that."
cap "Step 3 (T3): save the map and measure the room against the true 10 x 8 m" 2 "Step three. Save the map and measure the room."
run T3 "clear; ros2 run nav2_map_server map_saver_cli -f ~/maps/w8_demo --ros-args -p use_sim_time:=true 2>&1 | grep -E 'saved success'; python3 ~/labs/week04/scripts/map_metrics.py ~/maps/w8_demo.yaml | grep -E 'room width|room depth'" 12
cap "Your turn: week08/README.md - A1-A3, then the three TODOs in explorer.py. Try first, then compare." 8 "Your turn. Follow the week eight read me, activities one to three, then the three to do's in the explorer. Try first, then compare with the solution."
rec_stop
ctrlc T1 8; pkill -f gzserver; pkill -f gzclient
echo "saved $OUT"
