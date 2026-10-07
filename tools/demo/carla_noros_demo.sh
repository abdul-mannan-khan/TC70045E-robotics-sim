#!/bin/bash
# Demo video: CARLA WITHOUT ROS 2 - the Python API: a self-driving car with a chase camera, then your own cruise
# control. Tutor tool - run in the CARLA container desktop (narration is prepared first, see demo_lib.sh):
#   PREPARE=1 bash ~/labs/tools/demo/carla_noros_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/carla_noros_demo.sh /tmp/out.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/carla_noros_demo.mp4}
E=~/labs/examples/carla
carla-sim stop >/dev/null 2>&1
rm -f /tmp/cs1.log /tmp/cs2.log /tmp/cc.log /tmp/hello.log

caption_bar
term T1 1250 90 670 470
term T2 1250 580 670 490
rec_start "$OUT"

cap "Self-driving car without ROS 2: CARLA draws the world, the Python API drives the car" 5 "The self driving car, without ROS 2. CARLA simulates a town, the cars and their sensors. Our Python scripts talk to it through the CARLA programming interface."
cap "Step 1 (T1): start the CARLA server in Town04 - motorways and a small town" 2 "Step one. In terminal one we start the CARLA server, in town four: motorways and a small town."
run T1 "carla-sim start --town Town04 | tee /tmp/cs1.log" 3
say "CARLA renders on the graphics card with no window of its own. We look at it through a client. The first start takes up to a minute." 10
wait_for "CARLA is up" /tmp/cs1.log 300
cap "Step 2 (T2): a car, a chase camera and CARLA's autopilot - the window is our own Python client" 2 "Step two. Our first script spawns a car and a chase camera, and switches on CARLA's autopilot. The window you see is drawn by our own Python script, from the camera images."
run T2 "python3 -u $E/01_hello_carla.py --seconds 45 | tee /tmp/hello.log" 8
place "CARLA chase camera" 100 200 960 540
cap "The simulation runs in synchronous mode: every step is 0.05 s, the same in every run" 25 "The simulation runs in synchronous mode. Our script advances the world in fixed steps of fifty milliseconds, so every run is the same. The speed is printed in terminal two."
wait_for "t= 40" /tmp/hello.log 180
sleep 6
cap "Step 3 (T2): YOUR cruise control - a PI controller sets throttle and brake to hold 50 km/h" 2 "Step three. Now we write the driver ourselves: our own cruise control. A proportional integral controller sets the throttle and the brake to hold fifty kilometres an hour, and a simple pure pursuit controller keeps the car in its lane."
run T2 "clear; python3 -u $E/02_cruise_control_api.py --target 50 --seconds 45 --show | tee /tmp/cc.log" 8
place "CARLA cruise control" 100 200 960 540
cap "Watch the speed climb to the target and hold it - throttle drops once the car is at speed" 25 "Watch the speed climb to the target and stay there. Once the car is at speed, the throttle drops to what is needed to overcome the drag."
wait_for RESULT /tmp/cc.log 240
sleep 4
cap "Result: mean speed and the largest error over the last 10 s - a number for your report" 6 "The script ends with a result: the mean speed and the largest error over the last ten seconds. That is a number you can put in your report."
cap "Your turn: examples/carla/README.md, steps 1 and 2. Tune kp and ki, and compare the results." 8 "Your turn. Follow steps one and two in the examples folder, then tune the controller gains and compare the results."
rec_stop
run T1 "carla-sim stop" 3
echo "saved $OUT"
