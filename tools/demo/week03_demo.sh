#!/bin/bash
# Week 3 demo video: the integration clinic, start to finish (about 6 minutes). Tutor tool - run in the container:
#   DISPLAY=:1 bash ~/labs/tools/demo/week03_demo.sh /tmp/week03_demo.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week03_demo.mp4}
pkill -f gzserver; sleep 2
rm -f ~/labs/week03/config/my_driver.yaml

caption_bar
term T1 960 90 960 300
term T2 960 400 960 300
term T3 960 710 960 370
rec_start "$OUT"

cap "Week 3 demo - make the robot move: plug in a motor-controller driver, test it, fix its config" 5 "Week three demo. Making the robot move. We plug in the driver of a motor controller board, test it, and fix its configuration."
cap "Step 1 (T1): start the simulated robot and RViz - the robot brick from Week 2" 2 "Step one. In terminal one we start the simulated robot and RViz, with the Lego launch file from week two."
run T1 "ros2 launch ~/labs/week02/launch/lego.launch.py" 25
place rviz 0 90 955 990
cap "Step 2 (T2): copy the driver's config file that came with the board, and look at it" 2 "Step two. In terminal two we make our own copy of the configuration file that came with the board, and print it."
run T2 "cp ~/labs/week03/config/base_driver.yaml ~/labs/week03/config/my_driver.yaml" 1
run T2 "cat ~/labs/week03/config/my_driver.yaml" 6
cap "Step 3 (T2): start the driver brick:  /cmd_vel_in  ->  base_driver  ->  /cmd_vel  ->  robot" 2 "Step three. We start the driver brick with that file. It listens on cmd vel in, and drives the robot through cmd vel."
run T2 "clear; python3 ~/labs/week03/scripts/base_driver.py --ros-args --params-file ~/labs/week03/config/my_driver.yaml" 4
cap "Step 4 (T3): run the acceptance test - forward 1 m, left 1 m, turn 90 deg, stop when silent" 2 "Step four. In terminal three we run the acceptance test: one metre forward, one metre to the left, a ninety degree turn, and a check that the robot stops when the commands stop."
run T3 "python3 ~/labs/week03/scripts/motion_test.py" 4
say "Watch the robot in RViz on the left. The test takes about half a minute and prints a table at the end." 34
cap "0 of 4 passed. The robot spins instead of driving straight. Look at the four wheel commands..." 6 "Zero of four tests passed. The robot spins instead of driving straight. Let us look at the four wheel commands while we ask for forward motion."
run T3 "clear; ros2 service call /reset_world std_srvs/srv/Empty > /dev/null" 2
run T3 "ros2 topic echo --once /driver/wheel_cmd --field velocity & sleep 2; ros2 topic pub --once /cmd_vel_in geometry_msgs/msg/Twist '{linear: {x: 0.1}}' > /dev/null" 5
run T3 "ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{}' > /dev/null" 3
cap "Forward should be  + + + +  for FL FR RL RR.  FR (the 2nd) is negative: the config claims FR is wired backwards" 7 "For forward motion all four wheels should turn forwards. But the second one, front right, is negative. The configuration claims that the front right motor is wired backwards."
cap "Fix 1 (T2): stop the driver, edit the config in nano:  reversed: ['none'],  start the driver again" 2 "Fix one. We stop the driver, open the file in nano, and change the reversed list to none. Then we start the driver again and repeat the forward test."
ctrlc T2 2
run T2 "clear" 1
nano_replace T2 ~/labs/week03/config/my_driver.yaml "reversed: ['fr']" "reversed: ['none']"
run T2 "grep reversed ~/labs/week03/config/my_driver.yaml" 3
run T2 "python3 ~/labs/week03/scripts/base_driver.py --ros-args --params-file ~/labs/week03/config/my_driver.yaml" 4
run T3 "clear; ros2 service call /reset_world std_srvs/srv/Empty > /dev/null; python3 ~/labs/week03/scripts/motion_test.py --only forward" 16
cap "Straight now - but only 0.5 m instead of 1 m. The wheel is 75 mm across: 0.075 is the DIAMETER, the radius is 0.0375" 7 "It drives straight now, but only half a metre instead of one. The wheel is seventy five millimetres across. So zero point zero seven five is the diameter, and the radius is half of that."
cap "Fix 2 (T2): wheel_radius: 0.0375" 2 "Fix two. We set the wheel radius to zero point zero three seven five, and run all four tests again."
ctrlc T2 2
run T2 "clear" 1
nano_replace T2 ~/labs/week03/config/my_driver.yaml "wheel_radius: 0.075 " "wheel_radius: 0.0375"
run T2 "grep wheel_radius ~/labs/week03/config/my_driver.yaml" 3
run T2 "python3 ~/labs/week03/scripts/base_driver.py --ros-args --params-file ~/labs/week03/config/my_driver.yaml" 4
run T3 "clear; ros2 service call /reset_world std_srvs/srv/Empty > /dev/null; python3 ~/labs/week03/scripts/motion_test.py" 40
cap "3 of 4. The watchdog fails: if your program crashes, the robot drives on for ever. cmd_timeout_s: 0 means 'never stop'" 7 "Three of four. The watchdog test fails. If your program crashes, this robot would drive on for ever, because a command timeout of zero means never stop."
cap "Fix 3 (T2): cmd_timeout_s: 0.5  - stop the motors if no command arrives for half a second" 2 "Fix three. We set the command timeout to half a second, so the motors stop when the commands stop."
ctrlc T2 2
run T2 "clear" 1
nano_replace T2 ~/labs/week03/config/my_driver.yaml "cmd_timeout_s: 0.0" "cmd_timeout_s: 0.5"
run T2 "grep cmd_timeout ~/labs/week03/config/my_driver.yaml" 3
run T2 "python3 ~/labs/week03/scripts/base_driver.py --ros-args --params-file ~/labs/week03/config/my_driver.yaml" 4
run T3 "clear; ros2 service call /reset_world std_srvs/srv/Empty > /dev/null; python3 ~/labs/week03/scripts/motion_test.py" 40
cap "4 of 4 passed: the drive system is integrated. Now read base_driver.py and motion_test.py, then do the exercises." 8 "Four of four passed. The drive system is integrated. Now open base driver dot p y and motion test dot p y, read them, and do the exercises in the lecture."
rec_stop
ctrlc T2 1; ctrlc T1 6; pkill -f gzserver
rm -f ~/labs/week03/config/my_driver.yaml
echo "saved $OUT"
