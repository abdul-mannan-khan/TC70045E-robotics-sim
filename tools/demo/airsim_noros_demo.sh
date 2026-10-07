#!/bin/bash
# Demo video: AirSim + PX4 WITHOUT ROS 2, in the Mountains and the Neighborhood (urban) worlds. Tutor tool - run in
# the drone container desktop:   DISPLAY=:1 bash ~/labs/tools/demo/airsim_noros_demo.sh /tmp/airsim_noros_demo.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/airsim_noros_demo.mp4}
E=~/labs/examples/airsim
rm -f /tmp/sq1.log /tmp/sq2.log
drone-sim stop >/dev/null 2>&1
rm -f /tmp/simstart*.log

caption_bar
term T1 1250 90 670 470
term T2 1250 580 670 490
rec_start "$OUT"

cap "Drones without ROS 2: AirSim draws the world, PX4 flies the drone, Python talks to both" 5 "Drones without ROS 2. AirSim simulates the world, the physics and the sensors. PX4 is the autopilot that keeps the drone stable. Our Python scripts talk to both, with no ROS at all."
cap "Step 1 (T1): start the Mountains world - AirSim and the PX4 autopilot start together" 2 "Step one. In terminal one we start the mountains world. The drone sim command starts AirSim and the PX4 autopilot together."
run T1 "drone-sim start --world mountains | tee /tmp/simstart1.log" 3
say "The first start takes up to a minute while the simulator loads the terrain." 30
wait_for "ready for take-off" /tmp/simstart1.log 240
place LandscapeMountains 0 90 1240 700
sleep 20
cap "AirSim is up (API on port 41451) and PX4 is ready for take-off" 3 "AirSim is up, its programming interface answers on port four one four five one, and PX4 reports ready for take-off."
cap "Step 2 (T2): the AirSim API - read the drone's position, attitude, IMU, GPS and camera" 2 "Step two. In terminal two, the first script uses the AirSim Python interface. It reads the position, the attitude, the IMU, the GPS, and a picture from the front camera."
run T2 "python3 $E/01_hello_airsim.py --show" 12
place "AirSim front camera" 1250 580 660 500
say "The live window shows the drone's front camera." 8
keys "AirSim front camera" q
sleep 2
cap "Step 3 (T2): fly with MAVSDK - arm, take off to 30 m (clear of the valley sides), a 10 m square, land" 2 "Step three. Now we fly. This script talks to the autopilot with MAVSDK: it arms, takes off to thirty metres, high enough to clear the sides of the valley, flies a ten metre square, and lands."
run T2 "clear; python3 -u $E/02_fly_square_mavsdk.py --side 10 --alt 30 | tee /tmp/sq1.log" 5
say "The autopilot keeps the drone stable. The script only sends the corner positions." 20
cap "Watch the drone fly the square over the mountain valley (real time)" 20 "This is real time. Each corner is a position set point. The autopilot flies there and holds it, then the script sends the next corner."
wait_for landed /tmp/sq1.log 150
cp /tmp/drone-sim/px4.log /tmp/px4_flight1.log 2>/dev/null
sleep 3
cap "Step 4 (T1): the same scripts in the urban Neighborhood world" 2 "Step four. The same scripts work in any world. We stop the mountains and start the urban neighbourhood."
ctrlc T2 1
run T1 "clear; drone-sim stop; drone-sim start --world neighborhood | tee /tmp/simstart2.log" 3
say "Starting a new world takes about a minute: the previous simulation first releases its network port." 60
wait_for "ready for take-off" /tmp/simstart2.log 240
place AirSimNH 0 90 1240 700
sleep 15
run T2 "clear; python3 $E/01_hello_airsim.py --show" 12
place "AirSim front camera" 1250 580 660 500
cap "The front camera now sees houses and trees" 6 "The front camera now sees houses and trees."
keys "AirSim front camera" q
sleep 2
cap "Step 5 (T2): fly the square above the houses and trees at 15 m" 2 "Step five. We fly the square again, at fifteen metres, above the houses and the trees."
run T2 "clear; python3 -u $E/02_fly_square_mavsdk.py --side 10 --alt 15 | tee /tmp/sq2.log" 5
cap "Same code, different world: only the scenery changed (real time)" 20 "Same code, different world. Only the scenery has changed. This is the idea of a simulator: test your code safely in many places before it flies for real."
wait_for landed /tmp/sq2.log 150
cp /tmp/drone-sim/px4.log /tmp/px4_flight2.log 2>/dev/null
sleep 3
cap "Your turn: examples/airsim/README.md, steps 1 and 2. Change the square into a survey pattern." 8 "Your turn. Follow steps one and two in the examples folder, then change the square into a survey pattern."
rec_stop
run T1 "drone-sim stop" 4
echo "saved $OUT"
