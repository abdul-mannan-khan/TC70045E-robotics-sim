#!/bin/bash
# Week 2 demo video: snapping ROS 2 bricks together (about 7 minutes). Tutor tool - run in the container:
#   DISPLAY=:1 bash ~/labs/tools/demo/week02_demo.sh /tmp/week02_demo.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week02_demo.mp4}
pkill -f gzserver; sleep 2

caption_bar
term T1 960 90 960 300
term T2 960 400 960 300
term T3 960 710 960 370
rec_start "$OUT"

cap "Week 2 demo - ROS 2 as Lego: snap bricks together, add your own, build an explorer" 5 "Week two demo. ROS 2 as Lego. We snap ready made bricks together, add a brick of our own, and build a robot that explores by itself."
cap "Step 1 (T1): the robot brick + the viewer brick + the mapping brick, with one launch file" 2 "Step one. In terminal one, a single launch file starts three bricks: the simulated robot, the RViz viewer, and the mapping brick."
run T1 "ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true" 28
place rviz 0 90 955 990
cap "Step 2 (T2): what studs does it offer? Topic names and message types" 2 "Step two. What studs does the robot offer? We list the topic names and their message types."
run T2 "ros2 topic list -t | grep -E 'scan|cmd_vel|map|odom'" 5
cap "Step 3 (T3): snap on the keyboard brick and drive - watch the map grow in RViz" 2 "Step three. We snap on the keyboard brick in terminal three and drive. Watch the map grow in RViz."
run T3 "ros2 run teleop_twist_keyboard teleop_twist_keyboard" 3
keys T3 x x x x x                       # slow down to 0.3 m/s: x lowers the speed by 10 % each press
keys T3 i; sleep 4; keys T3 k           # 1.2 m forward, clear of the crate on the right
keys T3 j; sleep 1.6; keys T3 k         # quarter turn left
keys T3 i; sleep 3; keys T3 k           # 0.9 m, clear of the pillar
keys T3 l; sleep 1.6; keys T3 k         # quarter turn right
cap "Step 4 (T2): see the graph of bricks with rqt_graph" 2 "Step four. r q t graph shows how the bricks are connected: the keyboard drives the robot, and the laser feeds the mapping brick."
run T2 "rqt_graph" 10
place rqt_graph 0 90 955 900; sleep 1.5; place rqt_graph 0 90 955 900   # rqt resizes itself once after it opens
sleep 1.5; place rqt_graph 0 90 955 900
sleep 6
wmctrl -c rqt_graph; sleep 2
cap "Step 5: add YOUR brick. Restart with safety:=true, and plug the keyboard into /cmd_vel_in with a remap" 3 "Step five. We add our own brick, the safety stop. We restart with safety set to true, and plug the keyboard into cmd vel in with a remap."
ctrlc T3 1
ctrlc T1 8; pkill -f gzserver; sleep 2
run T1 "clear; ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true safety:=true" 28
place rviz 0 90 955 990
run T3 "clear; ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_in" 3
run T2 "clear; ros2 topic echo /safety/blocked" 2
cap "Drive straight at the wall... the safety brick blocks the motion before the robot hits it" 2 "Now we drive straight at the wall. The safety brick blocks the motion before the robot hits it."
keys T3 i; sleep 16; keys T3 k
cap "safety/blocked went true. Turning away (j) is still allowed - only motion towards the obstacle is removed" 4 "The safety brick reported blocked. Turning away is still allowed. Only motion towards the obstacle is removed."
keys T3 j; sleep 3; keys T3 k
cap "Step 6: the EXPLORER - wander + safety + slam. Nobody drives: it maps the lab by itself" 3 "Step six. The explorer. Wander, safety and mapping bricks together. Nobody drives. The robot maps the lab by itself."
ctrlc T2 1; ctrlc T3 1
ctrlc T1 8; pkill -f gzserver; sleep 2
run T1 "clear; ros2 launch ~/labs/week02/launch/lego.launch.py slam:=true wander:=true safety:=true" 25
place rviz 0 90 955 990
cap "Exploring... (real time - nothing sped up)" 50 "Exploring. This is real time, nothing is sped up. The wander brick drives forward and turns away from walls, the safety brick checks every command, and the mapping brick draws the map."
cap "Step 7 (T2): save the map it drew" 2 "Step seven. We save the map it drew to a file."
run T2 "clear; ros2 run nav2_map_server map_saver_cli -f ~/explorer_map --ros-args -p use_sim_time:=true" 6
cap "Your turn: Activities A1-A5 in the lecture. Open the bricks in ~/labs/week02/scripts and read them." 8 "Your turn. Do activities one to five in the lecture, and open the bricks in the week two scripts folder to read how they work."
rec_stop
ctrlc T1 6; pkill -f gzserver
echo "saved $OUT"
