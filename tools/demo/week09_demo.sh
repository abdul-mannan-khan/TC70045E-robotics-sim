#!/bin/bash
# Week 9 demo video: drones without ROS 2 - AirSim + PX4, the AirSim API, a MAVSDK square, then the survey mission
# (as given, the solution, and the battery-reserve stop). Tutor tool - run in the drone container desktop (narration is
# prepared first, see demo_lib.sh):
#   PREPARE=1 bash ~/labs/tools/demo/week09_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week09_demo.sh /tmp/w9.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week09_demo.mp4}
S=~/labs/week09/scripts
SOL=~/labs/solutions/week09/mission.py
drone-sim stop >/dev/null 2>&1
rm -f /tmp/w9demo_*.log
place_sim() { for i in 1 2 3; do place "$1" 0 90 1240 700; sleep 1; done; }   # place_sim AirSimNH | LandscapeMountains
pkill -9 -f bin/rqt_graph; pkill -f rviz2

caption_bar
term T1 1250 90 670 330
term T2 1250 430 670 400
term T3 1250 840 670 240
rec_start "$OUT"

cap "Week 9 demo - drones without ROS 2: AirSim draws the world, PX4 flies the drone, Python plans the survey" 5 "Week nine demo. Drones without ROS 2. AirSim simulates the world and the cameras. PX4, the same autopilot that runs on a real Pixhawk, keeps the drone in the air. Our Python script only tells it where to go."
cap "Step 0 (T1): start the neighborhood world (a town) - AirSim and the PX4 autopilot start together" 2 "Step zero. In terminal one we start the neighborhood world, a small town. AirSim and the PX4 autopilot start together."
run T1 "drone-sim start --world neighborhood | tee /tmp/w9demo_sim.log" 3
say "This takes about a minute. We wait for PX4 to report that it is ready for take-off." 30
wait_for "ready for take-off" /tmp/w9demo_sim.log 240
place_sim AirSimNH
sleep 10
snap w09_neighborhood_drone_on_ground_px4_ready
cap "A1 (T2): the AirSim API - position, attitude, IMU, GPS and the front camera, no autopilot involved" 2 "Activity one. In terminal two, the AirSim programming interface. It reads the position, the attitude, the IMU, the GPS and a picture from the front camera. No autopilot is involved."
run T2 "python3 $S/01_hello_airsim.py --show" 12
place "AirSim front camera" 1250 430 660 500
sleep 2; snap w09_a1_front_camera_and_sensors
say "The IMU's z reads about minus nine point eight, standing still: the push of the ground against gravity, and z points down in N E D." 6
keys "AirSim front camera" q
sleep 2
say "Before the first flight PX4 needs its first GPS fix: about a minute after the start." 25
cap "A2 (T2): MAVSDK over MAVLink - arm, take off to 15 m (above the trees), a 5 m square of position set-points, land" 2 "Activity two. Now we fly, through the autopilot. The script sends position set points over MAVLink. PX4 does the flying."
run T2 "clear; python3 -u $S/02_fly_square_mavsdk.py --side 5 --alt 15 | tee /tmp/w9demo_sq.log" 5
say "Fifteen metres up, above the trees, is z equals minus fifteen: N E D, z points down." 20
snap w09_a2_square_over_the_town
wait_for landed /tmp/w9demo_sq.log 150
sleep 3
snap w09_a2_square_landed_terminal
cap "A3 (T1): the survey flies over a mountain valley - stop the town, start the mountains world" 2 "For the survey we change worlds: a mountain valley. In terminal one we stop the town and start the mountains world."
run T1 "clear; drone-sim stop; drone-sim start --world mountains | tee /tmp/w9demo_sim2.log" 3
say "The survey has no obstacle avoidance, so it flies forty metres above the start: above the valley floor and its ridges." 30
wait_for "ready for take-off" /tmp/w9demo_sim2.log 240
place_sim LandscapeMountains
sleep 5
snap w09_mountains_drone_on_ground
say "Again, PX4 needs its first GPS fix before it can fly." 35
cap "A3 (T2): the survey AS GIVEN - 22 waypoints, every one MISSED, all photos of the take-off point" 2 "Activity three. The survey mission as given, at forty metres over a hundred by hundred metre field of the valley. Watch the waypoint lines."
run T2 "clear; python3 -u $S/mission.py --alt 40 --length 100 --width 100 | tee /tmp/w9demo_given.log" 5
say "Twenty two waypoints, because the row spacing is wrong. And every waypoint after the first is missed: the script never waits for the drone to arrive." 25
wait_for RESULT /tmp/w9demo_given.log 200
sleep 2; snap w09_survey_as_given_waypoints_missed
sleep 2
cap "Your activity: three TODOs - plan from the camera footprint, wait to arrive, stop in time to fly home" 4 "Your activity has three to do's. Plan the rows from the camera footprint. Wait until each waypoint is reached. And stop in time to fly home. Here is the solution."
run T2 "clear; rm -rf ~/survey; python3 -u $SOL --alt 40 --length 100 --width 100 | tee /tmp/w9demo_sol.log" 5
cap "Solution: from 40 m a 90-degree camera sees an 80 m strip - rows 64 m apart, 6 waypoints" 20 "From forty metres a ninety degree camera sees an eighty metre strip. With twenty percent overlap the rows are sixty four metres apart: six waypoints instead of twenty two."
cap "Every waypoint 'reached' within 1 m, one photo each (real time)" 25 "Now every waypoint is reached within one metre, and a photo is taken at each one. This is real time."
snap w09_survey_solution_mid_flight_over_the_valley
wait_for RESULT /tmp/w9demo_sol.log 300
sleep 2; snap w09_survey_solution_all_waypoints_reached
sleep 2
run T3 "ls ~/survey" 3
snap w09_survey_solution_photos_listed
cap "Battery reserve (TODO 3): the same survey with --max-time 20 must stop early and fly home" 2 "Finally, the battery reserve. The same survey with a time limit of twenty seconds must stop early and fly home."
run T2 "clear; python3 -u $SOL --alt 40 --length 100 --width 100 --max-time 20 | tee /tmp/w9demo_time.log" 5
wait_for RESULT /tmp/w9demo_time.log 300
sleep 4
snap w09_battery_reserve_aborted_time_limit
cap "time limit reached - ABORTED (time limit), the drone flew home and landed" 6 "Time limit reached. The survey is aborted, the drone flies home and lands."
cap "Your turn: week09/README.md - A1-A3, then the three TODOs in mission.py. Try first, then compare." 8 "Your turn. Follow the week nine read me, activities one to three, then the three to do's in the mission script. Try first, then compare with the solution."
rec_stop
run T1 "drone-sim stop" 4
echo "saved $OUT"
