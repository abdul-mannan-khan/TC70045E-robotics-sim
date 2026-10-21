#!/bin/bash
# Week 4 demo video: add a sensor, upgrade the SLAM - LiDAR + D455 camera, slam_toolbox -> RTAB-Map. Tutor tool - run
# in the container desktop (narration is prepared first, see demo_lib.sh). The video follows the Week 4 README and
# lecture PDF step by step, with the same commands: A1, A2, A3, A4, then the activity (three TODOs), solution last.
# The three 24 m circuits are played faster (fast_on / fast_off).
#   PREPARE=1 bash ~/labs/tools/demo/week04_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week04_demo.sh /tmp/w4.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week04_demo.mp4}
W=~/labs/week04
STRAFE_S=${STRAFE_S:-5.0}           # A1: seconds of strafing left (0.5 m/s) until the yellow step is in view
stop_sim() { ctrlc T1 8; for p in gzserver gzclient; do pgrep -x $p >/dev/null && kill $(pgrep -x $p); done; sleep 4; kill_ros
    cls T2; cls T3; }   # stop the simulator, and start the next activity with empty T2 and T3
view() { [ "${PREPARE:-0}" = 1 ] && return 0; timeout 10 python3 "$(dirname "$0")/gzview.py" "$@" >/dev/null 2>&1; }   # Gazebo camera: eye -> target
close_up() { view -4.1 -1.3 0.7 -2.8 -0.35 0.1; }      # the lab robot at its start position
step_view() { view -4.4 1.0 0.9 -1.8 2.4 0.0; }        # the robot after A1's drive, the yellow step ahead
overview() { view 0 -7.2 7.8 0 0.2 0; }                # both rooms (also the lab world's default view)
cls() { focus "$1"; xdotool key ctrl+l; sleep 0.3; }   # clear a terminal BEFORE typing, so the command stays on screen
wait_drive() {   # wait until the circuit driver has started and finished (it prints its score in T1)
    local i; for i in $(seq 1 60); do pgrep -f week04/scripts/drive_loop.py >/dev/null && break; sleep 1; done
    for i in $(seq 1 "$1"); do pgrep -f week04/scripts/drive_loop.py >/dev/null || return 0; sleep 1; done; }
place_views() {   # Gazebo (the simulated world) top left, RViz (what the robot knows) bottom left
    for i in 1 2 3; do place Gazebo 0 90 955 495; place RViz 0 590 955 490; sleep 1; done; }

if [ "${PREPARE:-0}" != 1 ]; then
    for p in gzserver gzclient; do pgrep -x $p >/dev/null && kill $(pgrep -x $p); done; sleep 2
    rm -f ~/maps/w4_toolbox.* ~/maps/w4_lidar.* ~/maps/w4_lidar_d455.* $W/config/my_rtabmap.yaml
    mkdir -p ~/maps
fi

caption_bar
term T1 960 90 960 300
term T2 960 400 960 330
term T3 960 740 960 340
rec_start "$OUT"

cap "Week 4 demo - add a sensor, upgrade the SLAM: LiDAR + D455 depth camera, RTAB-Map" 5 "Week four demo. Add a sensor, upgrade the SLAM. The lab robot gets a second sensor, a RealSense D455 depth camera, and a SLAM system that can use both sensors: RTAB-Map. This video follows the week four read me and slides, step by step."
cap "The problem: the LiDAR sees one flat slice, 18 cm above the floor" 2 "Here is the problem. The two D LiDAR on the top deck sees one flat slice of the world, eighteen centimetres above the floor. A low step, or a table top, is not in that slice."

# ---------------- A1 ----------------
cap "A1 (T1): robot + D455 + slam_toolbox + RViz" 2 "Activity one. Look at the new sensor. In terminal one, start the robot, its camera, slam toolbox and RViz."
run T1 "ros2 launch ~/labs/week04/launch/slam.launch.py slam:=toolbox" 30
place_views
close_up
say "Gazebo, top left, is the simulated world, here close up on the lab robot: the LiDAR on the top deck, the depth camera on the middle deck. RViz, below, shows what the robot knows: the map, the laser in red, and the coloured points of the depth camera." 3
cap "A1 (T2): how fast does the depth image arrive? Ctrl+C after 10 s" 2 "In terminal two, measure how often a depth image arrives. Control C after ten seconds."
run T2 "ros2 topic hz /camera/aligned_depth_to_color/image_raw" 12
ctrlc T2 1
cap "A1 (T2): the camera matrix k - the focal length fx is k[0]" 2 "Then print the camera matrix, k. The first number is the focal length, f x, in pixels."
cls T2; run T2 "ros2 topic echo --once /camera/color/camera_info --field k" 6
say "f x is about two hundred and twenty three pixels: half the real D455's value, because the image is half size." 2
cap "A1 (T3): drive with the keyboard until the yellow low step is in front of the robot" 2 "In terminal three, start the keyboard driver, and drive until the yellow low step is in front of the robot."
run T3 "ros2 run teleop_twist_keyboard teleop_twist_keyboard" 4
keys T3 J
sleep "$STRAFE_S"
keys T3 k
step_view
cap "The depth cloud shows the step. The red laser slice passes over it" 8 "Look at RViz. The coloured depth points show the yellow step on the floor. The red laser points do not: the laser slice passes over it."
cap "Depth points on the far wall are noisier: stereo error grows with distance squared" 6 "And the depth points on the far wall are visibly noisier than on a near one. That is the stereo error from the lecture: it grows with distance squared."
ctrlc T3 1
stop_sim

# ---------------- A2 ----------------
cap "A2 (T1): Week 2 again - a LiDAR-only map with slam_toolbox, on the same 24 m circuit" 2 "Activity two. Week two again: a LiDAR only map with slam toolbox. Drive true makes the robot drive the same twenty four metre circuit every time. Do not drive it yourself."
cls T1; run T1 "ros2 launch ~/labs/week04/launch/slam.launch.py slam:=toolbox drive:=true" 25
place_views
overview
say "The circuit takes about three and a half minutes. We play it faster." 2
fast_on 8
wait_drive 420
sleep 2
fast_off
cap "A2: the end of the circuit - SLAM error against the truth (T1)" 6 "The circuit is finished. Terminal one prints the error against the true position: SLAM is within a few centimetres, wheel odometry alone is more than a metre off."
cap "A2 (T2): save the map, then score it against the true world" 2 "In terminal two, save the map, and score it against the true world."
cls T2; run T2 "ros2 run nav2_map_server map_saver_cli -f ~/maps/w4_toolbox --ros-args -p use_sim_time:=true -p save_map_timeout:=10.0" 4
wait_file $HOME/maps/w4_toolbox.yaml 40; sleep 2
tall T2
cls T2; run T2 "python3 ~/labs/week04/scripts/map_check.py ~/maps/w4_toolbox.yaml" 6
cap "A2: low step and table top MISSED; everything the laser slice cuts is SEEN" 7 "The low step and the table top are missed. The table's thin legs are seen, and everything the laser slice cuts is seen."
short T2
stop_sim

# ---------------- A3 + A4 ----------------
cap "A3 (T1): RTAB-Map with the LiDAR only - a new SLAM system, the same sensor" 2 "Activity three. RTAB-Map, with the LiDAR only: a new SLAM system, the same sensor."
cls T1; run T1 "ros2 launch ~/labs/week04/launch/slam.launch.py slam:=rtabmap drive:=true" 25
place_views
overview
cap "A3 (T3): read the settings while it drives - LiDAR only, a node every 0.1 m" 2 "While it drives, read the settings in terminal three. As given, RTAB-Map uses the LiDAR only, and adds a node to its graph every ten centimetres."
cls T3; run T3 "grep -E 'subscribe_scan|subscribe_rgbd|Reg/Strategy|LinearUpdate|Grid/Sensor' ~/labs/week04/config/rtabmap.yaml" 8
fast_on 8
wait_drive 420
sleep 2
fast_off
cap "A3 (T2): save the map and compare it with the slam_toolbox map" 2 "The circuit is finished. Save the RTAB-Map map, and score both maps."
cls T2; run T2 "ros2 run nav2_map_server map_saver_cli -f ~/maps/w4_lidar --ros-args -p use_sim_time:=true -p save_map_timeout:=10.0" 4
wait_file $HOME/maps/w4_lidar.yaml 40; sleep 2
tall T2
cls T2; run T2 "python3 ~/labs/week04/scripts/map_check.py ~/maps/w4_toolbox.yaml ~/maps/w4_lidar.yaml" 6
cap "A3: the same two objects MISSED - the algorithm changed, the sensor did not" 7 "The same two objects are missed. The algorithm changed. The sensor did not."
short T2
cap "A4 (T2): read the RTAB-Map graph - loop closures and topics" 2 "Activity four, with RTAB-Map still running: read its graph."
cls T2; run T2 "ros2 topic echo --once /rtabmap/info --field loop_closure_id" 6
run T2 "ros2 topic list | grep rtabmap" 5
say "Loop closure I D is zero while no loop closes. With the LiDAR only, RTAB-Map closes loops by proximity: matching scans near a place it knows. With the camera, it can also recognise a place from its picture." 2
stop_sim

# ---------------- Your activity ----------------
cap "Your activity (T3): copy the settings, keep the original" 2 "Now your activity: add the D455 to RTAB-Map. First copy the settings file, and keep the original."
cls T3; run T3 "cp ~/labs/week04/config/rtabmap.yaml ~/labs/week04/config/my_rtabmap.yaml" 2
run T3 "grep -n TODO ~/labs/week04/config/my_rtabmap.yaml | cut -c1-100" 5
cap "Three TODOs in my_rtabmap.yaml - PAUSE the video and try them first (README, Your activity)" 10 "There are three TO DOs in your copy. Pause the video now, read the read me, and try them yourself. Then come back for the solution."

# ---------------- Solution ----------------
cap "Solution - TODO 1: subscribe_rgbd: true (RTAB-Map receives the D455 colour + depth pair)" 2 "The solution. To do one: subscribe R G B D, true. RTAB-Map now receives the camera's colour and depth images, paired by R G B D sync."
nano_replace T3 ~/labs/week04/config/my_rtabmap.yaml "subscribe_rgbd: false" "subscribe_rgbd: true"
cap "Solution - TODO 2: Grid/Sensor \"1\" - the camera draws the map (\"2\": the LiDAR beam passes OVER the step and erases it)" 2 "To do two: grid sensor one. The camera draws the map. With two, both sensors, the LiDAR beam passes over the step, reports nothing there many times a second, and erases what the camera saw. The LiDAR still corrects the robot's position either way."
nano_replace T3 ~/labs/week04/config/my_rtabmap.yaml 'Grid/Sensor: "0"' 'Grid/Sensor: "1"'
cap "Solution - TODO 3: Grid/MaxGroundHeight \"0.04\" - above the depth noise, below the 8 cm step" 2 "To do three: max ground height, zero point zero four. Four centimetres is above the depth noise on the floor, and below the eight centimetre step."
nano_replace T3 ~/labs/week04/config/my_rtabmap.yaml 'Grid/MaxGroundHeight: "0.0"' 'Grid/MaxGroundHeight: "0.04"'
cls T3; run T3 "diff ~/labs/week04/config/rtabmap.yaml ~/labs/week04/config/my_rtabmap.yaml | grep '^[<>]' | cut -c1-60" 5
cap "Solution (T1): run RTAB-Map with your settings, the same circuit" 2 "Run RTAB-Map with your settings, on the same circuit."
cls T1; run T1 "ros2 launch ~/labs/week04/launch/slam.launch.py slam:=rtabmap drive:=true config:=\$HOME/labs/week04/config/my_rtabmap.yaml" 25
place_views
overview
say "Watch the yellow step, near the top of the left room, and the wooden table in the right room. In RViz they become black cells in the map." 2
fast_on 8
wait_drive 480
sleep 2
fast_off
cap "Solution (T2): save the third map, then score all three" 2 "Save the third map, and score all three maps."
cls T2; run T2 "ros2 run nav2_map_server map_saver_cli -f ~/maps/w4_lidar_d455 --ros-args -p use_sim_time:=true -p save_map_timeout:=10.0" 4
wait_file $HOME/maps/w4_lidar_d455.yaml 40; sleep 2
tall T2
cls T2; run T2 "python3 ~/labs/week04/scripts/map_check.py ~/maps/w4_toolbox.yaml ~/maps/w4_lidar.yaml ~/maps/w4_lidar_d455.yaml" 6
cap "Low step and table top: MISSED by both LiDAR maps, SEEN with the D455" 8 "The low step and the table top are missed by both LiDAR maps, and seen only in the map that uses the D455."
short T2
cls T3; run T3 "python3 ~/labs/week04/scripts/map_metrics.py ~/maps/w4_lidar_d455.yaml" 6
cap "The cost: about ten times the CPU and memory of slam_toolbox, slightly thicker walls, gaps outside the camera's 87 degree view" 7 "The camera has a cost: about ten times the processing and memory of slam toolbox, slightly thicker walls because depth noise grows with distance squared, and gaps where the camera never looked."
cap "For your report: the three-map table, an RViz screenshot, your TODO 3 value and why. Label results as simulated." 7 "For your report: the three map table, a screenshot of RViz with the step and the table in the map, your to do three value and why. Label all results as simulated."
rec_stop
stop_sim
echo "saved $OUT"
