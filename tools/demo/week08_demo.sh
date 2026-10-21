#!/bin/bash
# Week 8 demo video: autonomous exploration - frontiers + Nav2 on a growing map. Tutor tool - run in the container
# desktop (narration is prepared first, see demo_lib.sh). The video follows the Week 8 README and lecture PDF step by
# step, with the same commands: A1, A2, A3, then the activity (three TODOs), solution last.
# Long runs are played faster (fast_on / fast_off).
#   PREPARE=1 bash ~/labs/tools/demo/week08_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week08_demo.sh /tmp/w8.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week08_demo.mp4}
W=~/labs/week08
# A3: where to click in RViz (screen pixels, RViz at 0,590 955x490): the "2D Goal Pose" button, then a grey cell just
# past a frontier, dragged a little to set the heading. Measured on a test screenshot of this layout.
GOAL_BTN=${GOAL_BTN:-497 600}
GOAL_AT=${GOAL_AT:-560 700}
stop_sim() { ctrlc T1 8; for p in gzserver gzclient; do pgrep -x $p >/dev/null && kill $(pgrep -x $p); done; sleep 4; kill_ros
    cls T2; cls T3; }   # stop the simulator, and start the next activity with empty T2 and T3
cls() { focus "$1"; xdotool key ctrl+l; sleep 0.3; }   # clear a terminal BEFORE typing, so the command stays on screen
view() { [ "${PREPARE:-0}" = 1 ] && return 0; timeout 10 python3 "$(dirname "$0")/gzview.py" "$@" >/dev/null 2>&1; }
close_up() { view -4.1 -1.3 0.7 -2.8 -0.35 0.1; }      # the lab robot at its start position
overview() { view 0 -7.2 7.8 0 0.2 0; }                # both rooms (the lab world's default view)
wait_proc() {   # wait_proc PATTERN SECONDS - wait until a script has started and finished
    local i; for i in $(seq 1 90); do pgrep -f "$1" >/dev/null && break; sleep 1; done
    for i in $(seq 1 "$2"); do pgrep -f "$1" >/dev/null || return 0; sleep 1; done; }
wait_simtime() {   # wait_simtime SECONDS - wait until the simulation clock passes SECONDS (coverage.py prints RESULT at 600 s)
    [ "${PREPARE:-0}" = 1 ] && return 0
    local i t; for i in $(seq 1 900); do
        t=$(bash -c 'source /opt/ros/humble/setup.bash; timeout 5 ros2 topic echo --once /clock --field clock.sec' 2>/dev/null | head -1)
        [ -n "$t" ] && [ "$t" -ge "$1" ] && return 0; sleep 2; done; }
rviz_goal() {   # click RViz's 2D Goal Pose tool, then press-drag-release on the map (like a student)
    [ "${PREPARE:-0}" = 1 ] && return 0
    wmctrl -a RViz; sleep 0.5
    xdotool mousemove $GOAL_BTN click 1; sleep 0.8
    set -- $GOAL_AT
    xdotool mousemove "$1" "$2" mousedown 1; sleep 0.3
    xdotool mousemove $(( $1 + 25 )) "$2"; sleep 0.3; xdotool mouseup 1; sleep 0.5; }
place_views() {   # Gazebo (the simulated world) top left, RViz (what the robot knows) bottom left
    for i in 1 2 3; do place Gazebo 0 90 955 495; place RViz 0 590 955 490; sleep 1; done; }

if [ "${PREPARE:-0}" != 1 ]; then
    for p in gzserver gzclient; do pgrep -x $p >/dev/null && kill $(pgrep -x $p); done; sleep 2
    rm -f ~/maps/w8_wander.* ~/maps/w8_explorer.* $W/scripts/my_explorer.py
    mkdir -p ~/maps
fi

caption_bar
term T1 960 90 960 300
term T2 960 400 960 330
term T3 960 740 960 340
rec_start "$OUT"

cap "Week 8 demo - autonomous exploration: the robot maps the lab by itself, choosing where to go next" 5 "Week eight demo. Autonomous exploration. The lab robot starts with no map, and decides by itself where to go next, until nothing is left to explore. This video follows the week eight read me and slides, step by step."

# ---------------- A1 ----------------
cap "A1 (T1): the baseline - Week 2's wander brick for 10 minutes; the laser is used to 3.5 m" 2 "Activity one. The baseline: the wander brick from week two drives for ten minutes. The laser is used only up to three and a half metres, so the robot has to go places to see them."
cls T1; run T1 "ros2 launch ~/labs/week08/launch/explore.launch.py brain:=wander" 25
place_views
close_up
say "Gazebo, top left, shows the lab robot. RViz, below: the map is almost empty. Grey is unknown. Terminal one prints the explored area every thirty seconds." 3
overview
fast_on 12
wait_simtime 625
sleep 2
fast_off
cap "A1: the RESULT line after 600 s - area known, distance driven. Is the robot finished? It cannot tell." 8 "After six hundred seconds terminal one prints the result: the area known and the distance driven. The robot is still driving. It does not know whether the map is finished."
cls T2; run T2 "ros2 run nav2_map_server map_saver_cli -f ~/maps/w8_wander --ros-args -p use_sim_time:=true -p save_map_timeout:=10.0" 4
wait_file $HOME/maps/w8_wander.yaml 40; sleep 2
cls T2; run T2 "python3 ~/labs/week04/scripts/map_metrics.py ~/maps/w8_wander.yaml" 6
stop_sim

# ---------------- A2 + A3 ----------------
cap "A2 (T1): no brain - Nav2 starts and waits; (T2) the explorer as given" 2 "Activity two. See the frontiers. Launch with no brain: Nav2 starts and waits. Then run the explorer as given."
cls T1; run T1 "ros2 launch ~/labs/week08/launch/explore.launch.py" 30
place_views
overview
cls T2; run T2 "python3 ~/labs/week08/scripts/explorer.py --ros-args -p use_sim_time:=true" 10
cap "A2: 'no frontier left' at once - as given, no cell counts as a frontier (that is TODO 1)" 8 "As given, the explorer says no frontier left, at once: zero goals. No cell counts as a frontier. In RViz, the frontiers are where white, free, touches grey, unknown. Finding them is to do one."
cap "A3 (RViz): one goal into the unknown, by hand - the 2D Goal Pose tool, just past a frontier" 2 "Activity three. One goal into the unknown, by hand. In RViz, choose the two D goal pose tool, click on a grey area just past a frontier, and drag to set the heading."
rviz_goal
cap "A3: Nav2 plans through unknown space - the laser turns grey cells white or black as the robot goes" 15 "Nav2 plans a path through the unknown area, and drives. The laser turns grey cells white or black as the robot goes, and the frontier moves on. This is what the explorer relies on."
stop_sim

# ---------------- Your activity ----------------
cap "Your activity (T3): copy explorer.py, keep the original" 2 "Now your activity: finish the explorer. First copy it, and keep the original."
cls T3; run T3 "cp ~/labs/week08/scripts/explorer.py ~/labs/week08/scripts/my_explorer.py" 2
run T3 "grep -n TODO ~/labs/week08/scripts/my_explorer.py | cut -c1-110" 5
cap "Three TODOs in my_explorer.py - PAUSE the video and try them (README); run with distance_weight 0.0, then 1.0" 10 "There are three TO DOs: find the frontiers, choose one that is big and near, and skip goals already tried. Pause the video now and try them yourself, then run your explorer with distance weight zero, and again with one. Then come back for the solution."

# ---------------- Solution ----------------
cap "Solution: frontier = free & near_unknown; score = size - k*d; skip goals within 0.5 m of one already tried" 2 "The solution. A frontier cell is free and has an unknown neighbour. The score is the size minus k times the distance: big and near. And a goal within half a metre of one already tried is skipped."
cls T1; run T1 "ros2 launch ~/labs/week08/launch/explore.launch.py" 30
place_views
overview
cls T2; run T2 "python3 ~/labs/solutions/week08/explorer.py --ros-args -p use_sim_time:=true" 8
say "Watch RViz: every goal pushes the edge of the known map further out." 2
fast_on 10
wait_proc solutions/week08/explorer.py 700
sleep 2
fast_off
cap "Solution (T2): 'no frontier left' - the robot KNOWS the map is complete, and stops" 8 "Finished. No frontier left: the robot knows the map is complete, and it stops. The wandering robot never knew that."
cls T2; run T2 "ros2 run nav2_map_server map_saver_cli -f ~/maps/w8_explorer --ros-args -p use_sim_time:=true -p save_map_timeout:=10.0" 4
wait_file $HOME/maps/w8_explorer.yaml 40; sleep 2
cls T2; run T2 "python3 ~/labs/week04/scripts/map_metrics.py ~/maps/w8_explorer.yaml" 6
cap "For your report: wander / k = 0 / k = 1 x (time to 70 m2, finished after, driven, known area, scale error)" 8 "For your report: a table, wander, k zero and k one, against the time to seventy square metres, when it finished, the distance driven, the area known and the scale error. Label all results as simulated."
rec_stop
stop_sim
echo "saved $OUT"
