#!/bin/bash
# Week 6 demo video: see and understand with the D455 - find the coloured boxes and put them on the SLAM map.
# Tutor tool - run in the container desktop (narration is prepared first, see demo_lib.sh). The video follows the
# Week 6 README and lecture PDF step by step, with the same commands: A1, A2, A3, then the activity (three TODOs),
# solution last.
#   PREPARE=1 bash ~/labs/tools/demo/week06_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week06_demo.sh /tmp/w6.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week06_demo.mp4}
W=~/labs/week06
stop_sim() { ctrlc T1 8; for p in gzserver gzclient; do pgrep -x $p >/dev/null && kill $(pgrep -x $p); done; sleep 4
    cls T2; cls T3; }   # stop the simulator, and start the next activity with empty T2 and T3
cls() { focus "$1"; xdotool key ctrl+l; sleep 0.3; }   # clear a terminal BEFORE typing, so the command stays on screen
view() { [ "${PREPARE:-0}" = 1 ] && return 0; timeout 10 python3 "$(dirname "$0")/gzview.py" "$@" >/dev/null 2>&1; }
close_up() { view -4.1 -1.3 0.7 -2.8 -0.35 0.1; }      # the lab robot at its start position
overview() { view 0 -7.2 7.8 0 0.2 0; }                # both rooms (the lab world's default view)
red_view() { view 0.4 -0.4 1.3 -1.3 -2.3 0.0; }        # the robot looking at the red box
green_view() { view 1.6 0.9 1.3 3.6 -0.8 0.0; }        # the robot looking at the green box
near() {   # near X Y R SECONDS - wait until the robot is within R m of (X, Y) in Gazebo (not shown in the video)
    [ "${PREPARE:-0}" = 1 ] && return 0
    local i; for i in $(seq 1 "$4"); do
        timeout 5 gz model -m lab_robot -p 2>/dev/null | python3 -c "
import sys; x, y = map(float, sys.stdin.read().split()[:2]); sys.exit(0 if (x - $1) ** 2 + (y - $2) ** 2 < $3 ** 2 else 1)" \
            && return 0; sleep 1; done; return 1; }
wait_tour() {   # wait until the tour has started and finished
    local i; for i in $(seq 1 60); do pgrep -f week06/scripts/tour.py >/dev/null && break; sleep 1; done
    for i in $(seq 1 "$1"); do pgrep -f week06/scripts/tour.py >/dev/null || return 0; sleep 1; done; }
place_views() {   # Gazebo (the simulated world) top left, RViz (camera image, mask, map) bottom left - RViz taller
    for i in 1 2 3; do place Gazebo 0 90 955 420; place RViz 0 515 955 565; sleep 1; done; }

if [ "${PREPARE:-0}" != 1 ]; then
    for p in gzserver gzclient; do pgrep -x $p >/dev/null && kill $(pgrep -x $p); done; sleep 2
    rm -f $W/scripts/my_box_finder.py
fi

caption_bar
term T1 960 90 960 300
term T2 960 400 960 330
term T3 960 740 960 340
rec_start "$OUT"

cap "Week 6 demo - see and understand with the D455: find the boxes, put them on the map" 5 "Week six demo. See and understand with the D455 camera. The lab robot finds two coloured boxes in its camera image, measures how far away they are, and puts them on the SLAM map. This video follows the week six read me and slides, step by step."

# ---------------- A1 ----------------
cap "A1 (T1): robot + D455 + SLAM + RViz" 2 "Activity one. The camera as a sensor. In terminal one, start the robot with its camera, slam toolbox and RViz."
cls T1; run T1 "ros2 launch ~/labs/week06/launch/perception.launch.py" 25
place_views
close_up
say "Gazebo, top left, shows the lab robot: the depth camera sits on the middle deck. RViz, below, shows the camera image, the mask of the box finder, and the map." 3
cls T2; run T2 "ros2 topic hz /camera/color/image_raw" 12
ctrlc T2 1
cls T2; run T2 "ros2 topic echo --once /camera/color/camera_info --field k" 6
cap "A1: K = [fx, 0, cx, 0, fy, cy, 0, 0, 1] - fx = fy = 223.4 px, centre (212.5, 120.5)" 7 "K is the camera matrix. f x and f y are the focal length in pixels: two hundred and twenty three point four. c x and c y are the image centre. Check: half the image width, divided by the tangent of half the eighty seven degree view, gives the same f x."

# ---------------- A2 ----------------
cap "A2 (T2): depth at one pixel - (T3) drive towards a wall and back" 2 "Activity two. Depth at a pixel. In terminal two, the pixel probe prints the colour and the depth of the centre pixel once a second. In terminal three, drive towards a wall and back."
cls T2; run T2 "python3 ~/labs/week06/scripts/pixel_probe.py --ros-args -p use_sim_time:=true" 5
cls T3; run T3 "ros2 run teleop_twist_keyboard teleop_twist_keyboard" 4
keys T3 j; sleep 1.6; keys T3 k; sleep 2
keys T3 i; sleep 3.0; keys T3 k; sleep 3
keys T3 comma; sleep 3.0; keys T3 k
cap "The depth follows the distance; 0 = no depth (closer than ~0.5 m, or no stereo match)" 7 "The depth, in millimetres, follows the distance to the wall. A zero means no depth: closer than about half a metre, or no stereo match."
ctrlc T3 1
ctrlc T2 1
stop_sim

# ---------------- A3 ----------------
cap "A3 (T1): the tour past both boxes - (T2) probe pixel u = 317, where the box will be" 2 "Activity three. The colours of the boxes. The tour stops twice with a box twenty five degrees to the right of the image centre: that is pixel column three hundred and seventeen. Probe that pixel."
cls T1; run T1 "ros2 launch ~/labs/week06/launch/perception.launch.py tour:=true" 3
cls T2; run T2 "python3 ~/labs/week06/scripts/pixel_probe.py --ros-args -p use_sim_time:=true -p u:=317" 20
place_views
overview
near -0.8 -1.4 0.3 200
red_view
cap "A3: on the red box HSV about (0, 255, 178) - saturation 255; walls have low S" 12 "On the red box the probe reads a hue of zero and a saturation of two hundred and fifty five. The brick and grey walls have a low saturation: that is what separates them from the boxes."
near 2.4 -0.6 0.3 200
green_view
cap "A3: on the green box HSV about (60, 255, 153) - your numbers for TODO 1" 12 "On the green box: hue sixty, saturation two hundred and fifty five. These are your numbers for to do one."
wait_tour 200
ctrlc T2 1
stop_sim

# ---------------- Your activity ----------------
cap "Your activity (T3): copy box_finder.py, keep the original" 2 "Now your activity: finish the box finder. First copy it, and keep the original."
cls T3; run T3 "cp ~/labs/week06/scripts/box_finder.py ~/labs/week06/scripts/my_box_finder.py" 2
run T3 "grep -n TODO ~/labs/week06/scripts/my_box_finder.py | cut -c1-110" 5
cap "Three TODOs in my_box_finder.py - PAUSE the video and try them, one at a time (README, Your activity)" 10 "There are three TO DOs: the green colour range, the back projection from a pixel and its depth to a point, and the transform into the map. Pause the video now, read the read me, and try them yourself, one at a time. Then come back for the solution."

# ---------------- Solution ----------------
cap "Solution: TODO 1 green H 50-70, TODO 2 X = (u-cx)Z/fx, Y = (v-cy)Z/fy, TODO 3 do_transform_point(p, tr)" 2 "The solution. To do one: a green range round hue sixty. To do two: the pinhole model. X is u minus c x, times Z, over f x, and the same for Y. To do three: transform the point into the map with do transform point."
cls T1; run T1 "ros2 launch ~/labs/week06/launch/perception.launch.py tour:=true" 3
cls T2; run T2 "python3 ~/labs/solutions/week06/box_finder.py --ros-args -p use_sim_time:=true" 20
place_views
overview
say "The mask, in RViz, is white where the colour matches. Every detection becomes a cube on the map." 2
near -0.8 -1.4 0.3 200
red_view
cap "Watch RViz: the mask shows the red box in white, a red cube appears on the map" 10 "Watch RViz. The mask shows the red box in white, and a red cube appears on the map where the box really is."
near 2.4 -0.6 0.3 200
green_view
cap "Now the green box: the same recipe with a different hue" 10 "Now the green box: the same recipe, with a different hue."
wait_tour 200
overview
cap "Solution (T2): when T1 prints 'tour finished', Ctrl+C prints each box and its error" 2 "When terminal one prints tour finished, press control C in terminal two. It prints each box's position on the map and its error against the truth."
ctrlc T2 4
cap "Both boxes on the map within about 10 cm - from a 424 x 240 camera, 1.5 m away" 8 "Both boxes are on the map within about ten centimetres, from a small four hundred and twenty four by two hundred and forty camera, a metre and a half away."
cap "For your report: one row per step (as given, + TODO 1, + 2, + 3). Assessment 1 is due in Week 7." 8 "For your report: a table with one row per step, as given, then with each to do. Label all results as simulated. Assessment one is due in week seven."
rec_stop
stop_sim
echo "saved $OUT"
