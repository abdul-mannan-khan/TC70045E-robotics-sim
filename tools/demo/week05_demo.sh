#!/bin/bash
# Week 5 demo video: fuse for better localisation - wheel odometry + gyro -> EKF -> SLAM. Tutor tool - run in the
# container desktop (narration is prepared first, see demo_lib.sh). The video follows the Week 5 README and lecture
# PDF step by step, with the same commands: A1, A2, A3, A4, then the activity (three TODOs), solution last.
# The 24 m circuits are played faster (fast_on / fast_off).
#   PREPARE=1 bash ~/labs/tools/demo/week05_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week05_demo.sh /tmp/w5.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week05_demo.mp4}
W=~/labs/week05
stop_sim() { ctrlc T1 8; for p in gzserver gzclient; do pgrep -x $p >/dev/null && kill $(pgrep -x $p); done; sleep 4; kill_ros
    cls T2; cls T3; }   # stop the simulator, and start the next activity with empty T2 and T3
cls() { focus "$1"; xdotool key ctrl+l; sleep 0.3; }   # clear a terminal BEFORE typing, so the command stays on screen
view() { [ "${PREPARE:-0}" = 1 ] && return 0; timeout 10 python3 "$(dirname "$0")/gzview.py" "$@" >/dev/null 2>&1; }
close_up() { view -4.1 -1.3 0.7 -2.8 -0.35 0.1; }      # the lab robot at its start position
overview() { view 0 -7.2 7.8 0 0.2 0; }                # both rooms (the lab world's default view)
wait_drive() {   # wait until the circuit driver has started and finished (it prints its table in T1)
    local i; for i in $(seq 1 90); do pgrep -f week05/scripts/drive_and_score.py >/dev/null && break; sleep 1; done
    for i in $(seq 1 "$1"); do pgrep -f week05/scripts/drive_and_score.py >/dev/null || return 0; sleep 1; done; }
place_views() {   # Gazebo (the simulated world) top left, RViz (what the robot knows) bottom left
    for i in 1 2 3; do place Gazebo 0 90 955 495; place RViz 0 590 955 490; sleep 1; done; }

if [ "${PREPARE:-0}" != 1 ]; then
    for p in gzserver gzclient; do pgrep -x $p >/dev/null && kill $(pgrep -x $p); done; sleep 2
    rm -f $W/config/my_ekf.yaml
fi

caption_bar
term T1 960 90 960 300
term T2 960 400 960 330
term T3 960 740 960 340
rec_start "$OUT"

cap "Week 5 demo - fuse for better localisation: wheel odometry + IMU gyro -> EKF" 5 "Week five demo. Fuse for better localisation. The lab robot combines its wheel odometry with the gyroscope of its I M U in an extended Kalman filter. This video follows the week five read me and slides, step by step."
cap "The problem: wheel odometry drifts - about a metre on the 24 m circuit" 2 "Here is the problem. On the twenty four metre circuit, wheel odometry alone ends about a metre from the truth."

# ---------------- A1 ----------------
cap "A1 (T1): wheel odometry only - robot + SLAM + RViz, and drive the circuit" 2 "Activity one. Wheel odometry drifts. In terminal one, start the robot with wheel odometry only. Drive true starts the circuit thirty seconds after the launch, after the gyro calibration. Do not drive the robot yourself."
cls T1; run T1 "ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=raw drive:=true" 25
place_views
close_up
say "Gazebo, top left, shows the lab robot. RViz, below: the green trail is where the robot really goes, the red trail is where wheel odometry thinks it goes." 3
overview
fast_on 8
wait_drive 480
sleep 2
fast_off
cap "A1: the end of the circuit (T1) - wheel odometry about a metre off, SLAM about a centimetre" 8 "The circuit is finished. Terminal one prints the table. Wheel odometry alone is about a metre off at the end, with a heading error of about ten degrees. SLAM is about a centimetre off."
say "Why is a ten degree heading error worth a metre? Because the position error grows with the distance driven times the sine of the heading error." 2

# ---------------- A2 ----------------
cap "A2 (T2): meet the gyro - leave A1 running, the robot stands still" 2 "Activity two. Meet the gyro. Leave activity one running: the robot now stands still."
cls T2; run T2 "ros2 topic hz /imu/data_raw" 7
ctrlc T2 1
cls T2; run T2 "ros2 topic echo --once /imu/data_raw --field angular_velocity" 5
say "About a hundred samples a second. The robot is not moving, yet the turning rate z is not zero: a few thousandths of a radian per second." 2
cls T2; run T2 "python3 ~/labs/week05/scripts/gyro_bias.py --ros-args -p use_sim_time:=true -r /imu/data_cal:=/imu/test" 16
ctrlc T2 1
cap "A2: the turn-on bias - new at every start, like a real MEMS gyro at power-up" 7 "That offset is the gyro's turn-on bias. The simulated gyro draws a new one at every start, as a real MEMS gyro does at power-up. A tenth of a degree per second, integrated over the circuit, is twenty degrees of heading."
stop_sim

# ---------------- A3 + A4 ----------------
cap "A3 (T1): the EKF with the settings as given" 2 "Activity three. Start the E K F with the settings in E K F dot yaml as they are now."
cls T1; run T1 "ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=ekf drive:=true" 25
place_views
overview
cls T2; run T2 "ros2 topic hz /odometry/filtered" 7
ctrlc T2 1
cap "A3 (T3): read the settings while it drives - 15 true/false values per sensor" 2 "While it drives, read the settings. Each sensor has fifteen true or false values: which parts of the robot's state the E K F takes from that sensor."
cls T3; run T3 "grep -n -E 'two_d_mode|_config|TODO' ~/labs/week05/config/ekf.yaml | cut -c1-110" 8
fast_on 8
wait_drive 480
sleep 2
fast_off
cap "A3: blue (EKF) lies on red (wheels) - the EKF runs, but only follows the wheels" 8 "The blue E K F trail lies exactly on the red wheel trail, and the table shows the same error for both. The E K F is running, but it takes the wheels' position as if it were a measurement. Your activity fixes that."
cap "A4 (T2): who owns the transform odom -> base_footprint?" 2 "Activity four, with activity three still running. Who owns the transform from odom to base footprint?"
cls T2; run T2 "ros2 param get /wheel_odometry publish_tf" 4
run T2 "ros2 param get /ekf_filter_node publish_tf" 4
cls T2; run T2 "ros2 run tf2_ros tf2_echo odom base_footprint" 6
ctrlc T2 1
cls T3; run T3 "ros2 topic echo --once /odometry/filtered --field pose.pose.position" 5
say "The wheel odometry node says false and the E K F says true: exactly one owner. The translation tf2 echo prints is the position in odometry filtered." 2
stop_sim

# ---------------- Your activity ----------------
cap "Your activity (T3): copy the settings, keep the original" 2 "Now your activity: configure the E K F and prove it helps. First copy the settings file, and keep the original."
cls T3; run T3 "cp ~/labs/week05/config/ekf.yaml ~/labs/week05/config/my_ekf.yaml" 2
run T3 "grep -n TODO ~/labs/week05/config/my_ekf.yaml | cut -c1-110" 5
cap "Three TODOs in my_ekf.yaml - PAUSE the video and try them, one at a time (README, Your activity)" 10 "There are three TO DOs in your copy. Pause the video now, read the read me, and try them yourself, one at a time. Then come back for the solution."

# ---------------- Solution ----------------
cap "Solution: TODO 1 gyro yaw rate ON, TODO 2 wheel position OFF (velocities only), TODO 3 two_d_mode: true" 2 "The solution. To do one: switch on the gyro's yaw rate. To do two: switch off the wheels' position and heading, and keep their velocities, because the position is only the velocities added up. To do three: two D mode true, the robot drives on a flat floor."
cls T3; run T3 "diff ~/labs/week05/config/ekf.yaml ~/labs/solutions/week05/ekf.yaml | grep '^[<>]' | cut -c1-70" 6
cap "Solution (T1): run the worked solution, the same circuit" 2 "Run the worked solution on the same circuit."
cls T1; run T1 "ros2 launch ~/labs/week05/launch/fusion.launch.py odom:=ekf drive:=true ekf_config:=\$HOME/labs/solutions/week05/ekf.yaml" 25
place_views
overview
say "Watch RViz at every turn: the wheels slip a little, so the red trail bends away. The gyro measures the turn directly, so the blue trail stays closer to the green one." 2
fast_on 8
wait_drive 480
sleep 2
fast_off
cap "Solution: the EKF ends closer than the wheels; EKF height z 0.000 m, small variance (TODO 3)" 9 "The E K F ends closer to the truth than the wheels. The height line shows zero, with a small variance: that is to do three. Every start draws a new gyro bias, so run it more than once."
cap "Honest result: in this lab SLAM is ~1 cm with OR without the EKF - the laser always sees walls" 8 "An honest result. In this lab, SLAM is about one centimetre off with or without the E K F, because the laser always sees walls. The E K F matters where the laser cannot help: long corridors, open halls, glass, smoke."
cap "For your report: one row per configuration, an RViz screenshot of the three trails. Label results as simulated." 7 "For your report: a table with one row per configuration, a screenshot of RViz with the three trails, and which to do made the biggest difference. Label all results as simulated."
rec_stop
stop_sim
echo "saved $OUT"
