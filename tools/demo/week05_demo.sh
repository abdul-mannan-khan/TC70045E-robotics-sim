#!/bin/bash
# Week 5 demo video: fuse for better localisation - wheel odometry + gyro -> EKF -> SLAM. Tutor tool - run in the
# container desktop (narration is prepared first, see demo_lib.sh):
#   PREPARE=1 bash ~/labs/tools/demo/week05_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week05_demo.sh /tmp/w5.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week05_demo.mp4}
W=~/labs/week05
pkill -f gzserver; pkill -f gzclient; sleep 2
rm -f /tmp/w5demo_*.log
place_views() {   # Gazebo (the simulated world) top left, RViz (what the robot knows) bottom left
    for i in 1 2 3; do place Gazebo 0 90 955 495; place RViz 0 590 955 490; sleep 1; done; }

caption_bar
term T1 960 90 960 300
term T2 960 400 960 330
term T3 960 740 960 340
rec_start "$OUT"

cap "Week 5 demo - fuse for better localisation: wheel odometry + IMU gyro -> EKF" 5 "Week five demo. Fuse for better localisation. The robot combines its wheel odometry with the gyroscope of its I M U in an extended Kalman filter."
cap "The problem: wheel odometry drifts - more than a metre on the 24 m circuit of Week 4" 2 "Here is the problem. On the twenty four metre circuit of week four, wheel odometry alone ended more than a metre from the truth."
cap "Step 1 (T1): robot + gyro calibration + IMU filter + EKF (solution settings) + SLAM + RViz, and drive" 2 "Step one. In terminal one, one launch file starts the robot in Gazebo, a gyro calibration, the I M U filter, the E K F with the solution settings, slam toolbox and RViz. Drive true drives the same circuit as week four."
run T1 "ros2 launch $W/launch/fusion.launch.py odom:=ekf ekf_config:=\$HOME/labs/solutions/week05/ekf.yaml drive:=true 2>&1 | tee /tmp/w5demo_fusion.log" 30
place_views
say "Gazebo, top left, is the simulated world. RViz, below, shows what the robot knows. The robot stands still for the first thirty seconds: the gyro is being calibrated." 3
cap "Step 2 (T2): the gyro's turn-on bias - measured while the robot stands still" 2 "Step two. A M E M S gyro reads a small rotation even when the robot stands still. This offset is new every time it starts. The calibration brick measured it."
run T2 "clear; grep -o 'gyro bias measured.*' /tmp/w5demo_fusion.log" 6
say "Here it is, in radians and degrees per second. Integrated over the whole circuit, a tenth of a degree per second would become twenty degrees of heading error. So it is subtracted from every sample." 2
cap "Step 3 (T2): the IMU publishes at 100 Hz, the EKF at about 25 Hz" 2 "Step three. The I M U publishes a hundred times a second. The E K F publishes the fused odometry about twenty five times a second."
run T2 "clear; timeout 6 ros2 topic hz /odometry/filtered" 8
cap "Green: the truth.  Red: wheel odometry.  Blue: the EKF (wheels + gyro)" 6 "Now watch the three trails in RViz. Green is the truth. Red is wheel odometry alone. Blue is the E K F, wheels plus gyro."
cap "Step 4 (T3): your activity - three lines of ekf.yaml change" 2 "Step four. Your activity is the E K F settings file. Three things change. Here they are."
run T3 "clear; diff $W/config/ekf.yaml ~/labs/solutions/week05/ekf.yaml | grep -E '^[<>] +(two_d_mode|odom0_config|imu0_config|false, false, (true|false), +# vroll|false, false, (true|false), +# roll)' | cut -c1-60" 4
say "One. The gyro's yaw rate is switched on. Two. The wheels' position is switched off, because it is only the wheel velocities added up: fusing both would count the same measurement twice. Three. Two D mode: the robot drives on a flat floor." 3
cap "Watch RViz at every turn: the red trail bends away, the blue one stays with the green" 25 "Watch RViz at every turn. The wheels slip a little in each turn, so the red trail bends away. The gyro measures the turn directly, so the blue trail stays with the green one."
cap "Meanwhile SLAM (the map and the robot model) corrects whatever odometry it is given" 25 "Meanwhile slam toolbox matches the laser to the map and corrects whatever odometry it is given."
wait_for "EKF height" /tmp/w5demo_fusion.log 400
sleep 2
run T2 "clear; grep -A7 'loop finished' /tmp/w5demo_fusion.log | sed 's/^.python3-[0-9]*. //' | grep -v INFO" 3
cap "End of the circuit: errors against the truth (T2) - wheels > 1 m, EKF less, SLAM ~1 cm" 10 "The circuit is finished. Terminal two shows the error against the true position. Wheel odometry alone is more than a metre off. The E K F is closer: in our runs between three centimetres and eighty centimetres, because the gyro's bias keeps wandering during the drive, and a calibration at the start cannot remove that. SLAM, with the laser, is within about a centimetre."
cap "Honest result: in this lab SLAM is ~1 cm with OR without the EKF - the laser always sees walls" 8 "An honest result. In this lab, slam is about one centimetre off with or without the E K F, because the laser always sees walls. The E K F matters where the laser cannot help: long corridors, open halls, and drones. And the gyro's wandering bias is exactly why a robot needs a sensor that sees the world."
cap "Your turn: week05/README.md - activities A1-A4, then the three TODOs in ekf.yaml. Try first, then compare." 8 "Your turn. Follow the week five read me, activities one to four, then the three to do's in the E K F settings, one at a time, and measure each. Try first, then compare with the solution."
rec_stop
ctrlc T1 8; pkill -f gzserver; pkill -f gzclient
echo "saved $OUT"
