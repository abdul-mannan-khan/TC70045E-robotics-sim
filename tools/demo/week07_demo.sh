#!/bin/bash
# Week 7 demo video: RGB-D SLAM with the D455 alone, then Nav2 on the camera map. Tutor tool - run in the container
# desktop (narration is prepared first, see demo_lib.sh). The video follows the Week 7 README and lecture PDF step by
# step, with the same commands: A1, A2, A3 (with the solution settings, as the README says), then the activity
# (three TODOs); the answers to the TODOs come last. The 24 m circuit is played faster (fast_on / fast_off).
#   PREPARE=1 bash ~/labs/tools/demo/week07_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week07_demo.sh /tmp/w7.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week07_demo.mp4}
W=~/labs/week07
stop_sim() { ctrlc T1 8; for p in gzserver gzclient; do pgrep -x $p >/dev/null && kill $(pgrep -x $p); done; sleep 4
    cls T2; cls T3; }   # stop the simulator, and start the next activity with empty T2 and T3
cls() { focus "$1"; xdotool key ctrl+l; sleep 0.3; }   # clear a terminal BEFORE typing, so the command stays on screen
view() { [ "${PREPARE:-0}" = 1 ] && return 0; timeout 10 python3 "$(dirname "$0")/gzview.py" "$@" >/dev/null 2>&1; }
close_up() { view -4.1 -1.3 0.7 -2.8 -0.35 0.1; }      # the lab robot at its start position
overview() { view 0 -7.2 7.8 0 0.2 0; }                # both rooms (the lab world's default view)
wait_proc() {   # wait_proc PATTERN SECONDS - wait until a script has started and finished
    local i; for i in $(seq 1 90); do pgrep -f "$1" >/dev/null && break; sleep 1; done
    for i in $(seq 1 "$2"); do pgrep -f "$1" >/dev/null || return 0; sleep 1; done; }
place_views() {   # Gazebo (the simulated world) top left, RViz (what the robot knows) bottom left
    for i in 1 2 3; do place Gazebo 0 90 955 495; place RViz 0 590 955 490; sleep 1; done; }

if [ "${PREPARE:-0}" != 1 ]; then
    for p in gzserver gzclient; do pgrep -x $p >/dev/null && kill $(pgrep -x $p); done; sleep 2
    rm -f ~/maps/w7_camera.* $W/config/my_camera.yaml
    mkdir -p ~/maps
fi

caption_bar
term T1 960 90 960 300
term T2 960 400 960 330
term T3 960 740 960 340
rec_start "$OUT"

cap "Week 7 demo - RGB-D SLAM with the D455 alone, then Nav2 on the camera's map" 5 "Week seven demo. The LiDAR is switched off. The lab robot maps the lab with the D455 depth camera alone, then navigates on that map. This video follows the week seven read me and slides, step by step."

# ---------------- A1 ----------------
cap "A1 (T1): camera-only RTAB-Map with the SOLUTION settings (as the README says: see the goal first)" 2 "Activity one. A map from the camera alone. As the read me says, activities one to three use the solution settings, so you see the goal first. In your activity you build them yourself."
cls T1; run T1 "ros2 launch ~/labs/week07/launch/rgbd_nav.launch.py mode:=mapping drive:=true config:=\$HOME/labs/solutions/week07/rtabmap_camera.yaml" 30
place_views
close_up
say "Gazebo, top left, shows the lab robot. RViz, below: no red laser this week. The map is drawn from the coloured depth points of the camera." 3
overview
fast_on 8
wait_proc week04/scripts/drive_loop.py 520
sleep 2
fast_off
cap "A1: small error at the END (a loop closure), but tens of cm DURING the drive - LiDAR: 2 cm" 9 "The circuit is finished. The error at the end is small: the loop closure at the start pulls the graph straight. But the R M S error during the drive is tens of centimetres. With the LiDAR it was two."
cap "A1 (T2): save the map, score it, measure the room" 2 "Save the map, score it against the true world, and measure the room."
cls T2; run T2 "ros2 run nav2_map_server map_saver_cli -f ~/maps/w7_camera --ros-args -p use_sim_time:=true" 10
cls T2; run T2 "python3 ~/labs/week04/scripts/map_check.py ~/maps/w7_camera.yaml" 6
run T2 "python3 ~/labs/week04/scripts/map_metrics.py ~/maps/w7_camera.yaml" 6
cap "A1: step and table top SEEN - but more phantom cells, and the room measures too big" 8 "The step and the table top are seen. The price: hundreds of phantom cells, and the room measures a few percent too big. Compare with your week four table."
stop_sim

# ---------------- A2 ----------------
cap "A2 (T1): localisation mode - the saved map is loaded; (T2) is the robot on the map yet?" 2 "Activity two. Localise in the camera map. RTAB-Map loads the saved map and only recognises places. Terminal two asks: is there a transform from map to odom yet?"
cls T1; run T1 "ros2 launch ~/labs/week07/launch/rgbd_nav.launch.py mode:=localization config:=\$HOME/labs/solutions/week07/rtabmap_camera.yaml" 25
place_views
overview
cls T2; run T2 "ros2 run tf2_ros tf2_echo map odom" 15
cls T3; run T3 "ros2 run teleop_twist_keyboard teleop_twist_keyboard" 4
keys T3 j; sleep 2.0; keys T3 k; sleep 6
cap "A2: once the camera RECOGNISES a stored place, map -> odom appears: the robot is on the map" 8 "At first, the frame map does not exist: the robot does not know where it is. As soon as the camera recognises a place it saw while mapping, RTAB-Map publishes map to odom, and tf2 echo prints a translation."
ctrlc T3 1
ctrlc T2 1
stop_sim

# ---------------- A3 ----------------
cap "A3 (T1): Nav2 on the camera map - (T2) three goals, after about 45 s" 2 "Activity three. Nav2 on the camera map: the map from RTAB-Map, the obstacles from the depth point cloud. After about forty five seconds, send three goals."
cls T1; run T1 "ros2 launch ~/labs/week07/launch/rgbd_nav.launch.py mode:=localization nav:=true config:=\$HOME/labs/solutions/week07/rtabmap_camera.yaml" 45
place_views
overview
cls T2; run T2 "python3 ~/labs/week07/scripts/three_goals.py" 5
cap "A3: the local costmap fills only in front of the robot - the camera's 87 degree view" 10 "Look at the costmaps in RViz. The global costmap is the camera map. The local costmap fills only in front of the robot: the camera sees eighty seven degrees, not three hundred and sixty."
fast_on 6
wait_proc week07/scripts/three_goals.py 400
sleep 2
fast_off
cap "A3 (T2): which goals were reached, and how far from each the robot REALLY stopped" 9 "Here is the result: which goals were reached, and how far from each goal the robot really stopped, measured against the truth."
stop_sim

# ---------------- Your activity ----------------
cap "Your activity (T3): copy the settings, keep the original" 2 "Now your activity: build the camera-only settings yourself. First copy the settings file."
cls T3; run T3 "cp ~/labs/week07/config/rtabmap_camera.yaml ~/labs/week07/config/my_camera.yaml" 2
run T3 "grep -n TODO ~/labs/week07/config/my_camera.yaml | cut -c1-110" 5
cap "Three TODOs in my_camera.yaml - map with config:=...my_camera.yaml database:=\$HOME/maps/w7_mine.db, then three goals" 10 "There are three TO DOs. Map with your copy, and a database of your own, w7 mine dot d b, then navigate with the same two settings, as in the read me. Pause the video now and try them yourself."

# ---------------- Solution ----------------
cap "Solution: subscribe_scan false (no LiDAR), Reg/Strategy \"0\" (visual), strict loop closures" 2 "The solution. Subscribe scan false: no LiDAR. Registration strategy zero: match image features and depth, because without a scan there is nothing for I C P to match. And stricter loop closures: a wrong one, two places that look alike, bends the whole map."
cls T3; run T3 "diff ~/labs/week07/config/rtabmap_camera.yaml ~/labs/solutions/week07/rtabmap_camera.yaml | grep '^[<>]' | cut -c1-70" 6
cap "For your report: as given / TODO 1 / all three x (RMS, phantoms, room, goals). A1 is due this week." 8 "For your report: a table, as given, with to do one, and with all three, against the R M S error, phantom cells, room size and goals reached. Label all results as simulated. Assessment one is due this week."
rec_stop
stop_sim
echo "saved $OUT"
