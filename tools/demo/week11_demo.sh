#!/bin/bash
# Week 11 demo video: the self-driving car - CARLA through the Python API (A1, A2), through ROS 2 (A3), then adaptive
# cruise control with a radar, as given (it hits the car ahead) and the solution. Tutor tool - run in the CARLA
# container desktop (narration prepared first, see demo_lib.sh):
#   PREPARE=1 bash ~/labs/tools/demo/week11_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week11_demo.sh /tmp/w11.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week11_demo.mp4}
S=~/labs/week11/scripts
SOL=~/labs/solutions/week11/acc.py
carla-sim stop >/dev/null 2>&1
pkill -f carla_ros_bridge; pkill -f carla_manual_control; pkill -f carla_spawn_objects
rm -f /tmp/w11demo_*.log

caption_bar
term T1 960 90 960 240
term T2 960 340 960 240
term T3 960 590 960 490
rec_start "$OUT"

cap "Week 11 demo - the self-driving car: CARLA, a radar and adaptive cruise control" 5 "Week eleven demo. The third robot in the module: a car. CARLA simulates the town, the traffic, the car's physics and its sensors."
cap "Step 0 (T1): start the CARLA server in Town04 - it has no window; we look through our scripts' cameras" 2 "Step zero. In terminal one we start the CARLA server, in town four. The server has no window of its own: we look through the camera windows our scripts open."
run T1 "carla-sim start --town Town04 | tee /tmp/w11demo_cs.log" 3
say "The first start takes up to a minute." 10
wait_for "CARLA is up" /tmp/w11demo_cs.log 300
cap "A1 (T2): a car on CARLA's autopilot, seen through a chase camera" 2 "Activity one. A car on CARLA's own autopilot, seen through a chase camera."
run T2 "python3 -u $S/01_hello_carla.py --seconds 25 | tee /tmp/w11demo_a1.log" 8
place "CARLA chase camera" 0 90 955 540
say "The simulation runs in synchronous mode: our script advances the world in steps of fifty milliseconds, so every run is the same." 15
snap w11_carla_chase_camera_autopilot
wait_for "t= 24" /tmp/w11demo_a1.log 120
sleep 4
cap "A2 (T2): YOUR cruise control through the CARLA API - a PI controller sets throttle and brake" 2 "Activity two. Our own cruise control, through the CARLA programming interface. A P I controller sets the throttle and the brake to hold fifty kilometres an hour."
run T2 "clear; python3 -u $S/02_cruise_control_api.py --target 50 --seconds 35 --show | tee /tmp/w11demo_a2.log" 8
place "CARLA cruise control" 0 90 955 540
snap w11_cruise_api_no_ros_camera
cap "Measured: 50.0 km/h, largest error 0.1 km/h over the last 10 s (P only: 46.8 km/h)" 20 "Watch the speed climb to fifty and hold it. We measured fifty point zero, with the largest error point one kilometres an hour. With the P term alone, the car settles at forty six point eight: the I term removes that steady error."
wait_for RESULT /tmp/w11demo_a2.log 200
sleep 3
snap w11_cruise_api_no_ros_terminal_result
cap "A3 (T2): the same controller through ROS 2 - the CARLA ROS 2 bridge spawns 'ego_vehicle' and its sensors" 2 "Activity three. The same controller as a ROS 2 node. First, the CARLA ROS bridge. It spawns our car, ego vehicle, with its sensors, and publishes them as ROS 2 topics."
run T2 "clear; ros2 launch carla_ros_bridge carla_ros_bridge_with_example_ego_vehicle.launch.py host:=127.0.0.1 timeout:=60 town:=Town04 synchronous_mode:=true spawn_point_ego_vehicle:=\"-365.9,-33.6,0.8,0,0,0.4\" 2>&1 | grep -v ALSA | tee /tmp/w11demo_bridge.log" 30
place "CARLA ROS manual control" 0 90 955 540
run T3 "ros2 topic list | grep ego_vehicle | head -12" 5
run T3 "clear; rviz2 -d $S/carla.rviz > /dev/null 2>&1 &" 14
place RViz 0 590 955 490
run T3 "clear; python3 -u $S/03_cruise_control_ros2.py --ros-args -p target_kmh:=50.0 2>&1 | tee /tmp/w11demo_a3.log" 5
cap "Speedometer in, throttle and brake out: the node reaches 50 km/h - the inputs and outputs became ROS 2 topics" 30 "The node subscribes to the speedometer and publishes throttle and brake. The car reaches fifty kilometres an hour, the same controller, only its inputs and outputs became ROS 2 topics."
snap w11_ros2_bridge_rviz_cruise_node
ctrlc T3 2; ctrlc T2 8
pkill -f rviz2
cap "Your activity: adaptive cruise control - a radar sees the car ahead, which slows from 50 to 25 km/h" 4 "Your activity: adaptive cruise control. A forward radar measures the gap to the car ahead and how fast it is closing. The car ahead slows from fifty to twenty five kilometres an hour, and speeds up again."
run T3 "clear; python3 -u $S/acc.py --seconds 45 --show | tee /tmp/w11demo_given.log" 8
place "CARLA adaptive cruise control" 0 90 955 540
cap "As given: a P speed controller that ignores the radar - watch the gap when the car ahead slows down" 30 "As given, the script is a plain speed controller that ignores the radar. Watch the gap when the car ahead slows down."
wait_for "t= 32" /tmp/w11demo_given.log 240
snap w11_acc_as_given_closing_on_lead_car
wait_for RESULT /tmp/w11demo_given.log 240
sleep 3
cap "As given: smallest gap below zero - it hit the car ahead" 6 "The smallest gap is below zero. It hit the car ahead."
cap "Solution: PI speed loop + 2 s time gap + full brake when time-to-collision < 1.5 s or closer than 5 m" 2 "Now the solution. A P I speed loop, a two second time gap to the car ahead, and a full brake when the time to collision drops below one and a half seconds, or the gap below five metres."
run T3 "clear; python3 -u $SOL --show | tee /tmp/w11demo_sol.log" 8
place "CARLA adaptive cruise control" 0 90 955 540
wait_for "t= 10" /tmp/w11demo_sol.log 120
snap w11_acc_solution_following_at_50
cap "The car ahead slows at 25 s: your car slows with it and keeps the gap, then speeds up again" 40 "The car ahead slows at twenty five seconds. Our car slows with it, keeps its distance, and speeds up again when the road ahead is clear."
wait_for "t= 34" /tmp/w11demo_sol.log 300
snap w11_acc_solution_following_slow_lead_25
wait_for RESULT /tmp/w11demo_sol.log 300
snap w11_acc_solution_result_line
sleep 4
cap "Measured: smallest gap 18.2 m, smallest time gap 2.04 s - and no emergency brake needed" 6 "The result line: the smallest gap was eighteen metres, the smallest time gap two point zero four seconds, and the emergency brake was never needed. Numbers for your report."
cap "Your turn: week11/README.md - A1-A3, then the three TODOs in acc.py. Try first, then compare." 8 "Your turn. Follow the week eleven read me, activities one to three, then the three to do's in the adaptive cruise control. Try first, then compare with the solution."
rec_stop
run T1 "carla-sim stop" 3
echo "saved $OUT"
