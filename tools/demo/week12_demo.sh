#!/bin/bash
# Week 12 demo video: the pre-flight check in SITL - as given, the solution, a too-big survey, GPS failure injection
# (the mission stays on the ground), GPS back: GO again. HIL itself is the lecturer's live demo.
# Tutor tool - run in the drone container desktop (narration prepared first):
#   PREPARE=1 bash ~/labs/tools/demo/week12_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week12_demo.sh /tmp/w12.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week12_demo.mp4}
S=~/labs/week12/scripts
SOL=~/labs/solutions/week12/preflight.py
M=~/labs/solutions/week09/mission.py
drone-sim stop >/dev/null 2>&1
rm -f /tmp/w12demo_*.log
place_sim() { for i in 1 2 3; do place LandscapeMountains 0 90 1240 700; sleep 1; done; }
pkill -9 -f bin/rqt_graph; pkill -f rviz2

caption_bar
term T1 1250 90 670 300
term T2 1250 400 670 680
rec_start "$OUT"

cap "Week 12 demo - before a real autopilot flies: a pre-flight check that can say NO-GO" 5 "Week twelve demo. Before the mission flies a real Pixhawk, it needs a pre-flight check: software that can say no go. We test it here in software in the loop, on exactly the code the hardware runs."
cap "SITL here; in the lecture's HIL demo only the MAVLink address changes: serial:///dev/ttyTHS0:921600" 6 "In the hardware in the loop demo, the autopilot is a real Pixhawk six C and the mission runs on a Jetson. Only the MAVLink address changes."
run T1 "drone-sim start --world mountains | tee /tmp/w12demo_sim.log" 3
say "PX4 needs about a minute after the start for its first GPS fix." 30
wait_for "ready for take-off" /tmp/w12demo_sim.log 240
place_sim
# off camera: switch PX4's failure injection on now (a harmless 'ok'), so A3 needs no parameter write later
timeout 35 python3 $S/inject_fault.py --sensor gps --type ok > /tmp/w12demo_pre.log 2>&1 &
sleep 40
cap "As given (T2): GO - but the link reads 0.0 per s and PASSES, the battery needs 0 %" 2 "First the pre-flight check as given. Watch the link line and the battery line."
run T2 "python3 $S/preflight.py" 16
say "It says go. But zero position messages per second passes, and the battery needs zero percent. Three of the four checks pass anything." 4
cap "Solution: a measured value on every line - link 50 per s, 3D fix with 15 satellites, battery 37 %" 2 "Now the solution. Every line shows a measured value: fifty position messages per second, a 3 D fix with fifteen satellites, and the battery the Week nine survey needs plus a thirty percent reserve."
run T2 "clear; python3 $SOL" 16
snap w12_preflight_solution_GO
cap "A 1 x 1 km survey: NO-GO on the battery line (needs more than 100 %)" 2 "A one by one kilometre survey needs more battery than the drone has: no go, on the battery line."
run T2 "clear; python3 $SOL --length 1000 --width 1000" 16
snap w12_preflight_big_survey_NO_GO_battery
cap "A3: break the GPS (failure injection - simulator only), then 'preflight && mission'" 2 "Activity three. We break the GPS with PX4's failure injection. Simulator only: never on a drone that will fly. Then we chain the check and the mission with a double ampersand."
run T2 "clear; python3 $S/inject_fault.py --sensor gps --type off" 18
run T2 "clear; python3 $SOL && python3 $M | tee /tmp/w12demo_m1.log" 18
snap w12_gps_off_NO_GO_mission_not_started
cap "NO-GO: GPS NO_GPS, link FAIL - exit code 1, so the mission never takes off" 8 "No go. The GPS line shows no GPS, and the check exits with code one, so the mission never starts. The drone stays on the ground."
cap "GPS back: --type ok, wait about 20 s, check again - GO" 2 "Now we give the GPS back, wait about twenty seconds, and check again."
run T2 "clear; python3 $S/inject_fault.py --sensor gps --type ok" 25
run T2 "clear; python3 $SOL" 16
snap w12_gps_back_GO_again
cap "GO again - but restart the simulator before the next flight: the position estimate needs time to settle" 8 "Go again. But before the next flight, restart the simulator. In our test, a survey started straight after the GPS came back missed three waypoints by more than a hundred metres: the position estimate had not settled. A check can only test what it measures."
cap "Your turn: week12/README.md - A1, the three TODOs in preflight.py, A3. Then the A2 report." 8 "Your turn. Follow the week twelve read me. Activity one, the three to do's in the pre-flight check, and activity three. Then work on your A2 report."
rec_stop
run T1 "drone-sim stop" 4
echo "saved $OUT"
