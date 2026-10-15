#!/bin/bash
# Week 1 demo video: the workstation in use - turtlesim, then the sensor -> controller -> actuator loop and its PI
# fix (about 8 minutes). Tutor tool - run in the container desktop (narration is prepared first, see demo_lib.sh):
#   PREPARE=1 bash ~/labs/tools/demo/week01_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week01_demo.sh /tmp/w1.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week01_demo.mp4}
S=~/labs/week01/scripts
pkill -f turtlesim_node; pkill -f thermal_loop; pkill -f "week01/scripts"; sleep 1
place_plot() { for i in 1 2 3; do place "Temperature plot" 0 90 955 990; sleep 1; done; }

caption_bar
term T1 960 90 960 300
term T2 960 400 960 330
term T3 960 740 960 340
rec_start "$OUT"

cap "Week 1 demo - the robotics workstation in use: turtlesim, then a sensor -> controller -> actuator loop" 5 "Week one demo. Your robotics workstation in use. Everything runs in the course container, in this desktop in your web browser. First turtlesim, then a small control loop: a sensor, a controller and an actuator."
cap "Activity 1 (T1): the turtlesim node - a tiny simulated robot" 2 "Activity one. In terminal one we start turtlesim, a tiny simulated robot."
run T1 "ros2 run turtlesim turtlesim_node" 4
for i in 1 2 3; do place TurtleSim 150 200 600 600; sleep 1; done
cap "T2: the keyboard node - arrow keys publish velocity commands on /turtle1/cmd_vel" 2 "In terminal two, the keyboard node. Each arrow key publishes a velocity command."
run T2 "ros2 run turtlesim turtle_teleop_key" 3
keys T2 Up Up Up Left Up Up Left Left Up Up Up Right Up Up
sleep 2
cap "T3: what is on the network? Topics, and how often the turtle reports its pose" 2 "In terminal three: which topics exist, and how often does the turtle report where it is?"
run T3 "ros2 topic list" 3
run T3 "ros2 topic hz /turtle1/pose" 8
say "About sixty two times a second." 2
ctrlc T3 1
cap "rqt_graph: two nodes joined by one topic - the keyboard drives the turtle" 2 "r q t graph draws the system: two nodes, joined by one topic. The keyboard drives the turtle."
run T3 "clear; rqt_graph" 10
for i in 1 2 3; do place rqt_graph 0 90 955 900; sleep 1.5; done
xdotool mousemove 22 128 click 1; sleep 2; xdotool mousemove 1900 1060   # refresh: the graph is re-fitted to the window
sleep 6
wmctrl -c rqt_graph; sleep 1
ctrlc T2 1; ctrlc T1 2

cap "Activity 2 (T3): first a live plot of what the sensor measures (/room/temperature) and what the actuator does (/fan/speed)" 2 "Activity two. First, a live plot of what the sensor measures, and what the actuator does."
run T3 "clear; python3 ~/labs/tools/demo/temp_plot.py 26 24" 6
place_plot
cap "T1: one launch file starts a room sensor, a P controller and a fan (the actuator)" 2 "In terminal one, one launch file starts three nodes: a room temperature sensor, a proportional controller, and a fan with its motor driver. The setpoint is twenty six degrees."
run T1 "clear; ros2 launch $S/thermal_loop.launch.py 2>&1 | grep --line-buffered fan_controller" 4
say "The room starts at twenty five degrees, and a heater warms it. Once it is above the setpoint, the controller turns the fan on, in proportion to the error." 25
cap "It settles near 27.6 C, not 26.0: a P controller needs an error to keep the fan running" 20 "But it settles near twenty seven point six degrees, not twenty six. A proportional controller only drives the fan when there is an error, so some error always remains. This is the steady state error."
cap "T2: change a parameter of a running node - the new setpoint is 24 C" 2 "In terminal two we change a parameter of the running controller. The new setpoint is twenty four degrees."
run T2 "ros2 param set /fan_controller setpoint 24.0" 20
say "Again it stops short, at about twenty six point four." 2
cap "T2: a service call - stop the fan, and watch the room heat up" 2 "Now a service call. We ask the fan driver to stop the fan, and the room heats up."
run T2 "clear; ros2 service call /fan/stop std_srvs/srv/SetBool '{data: true}'" 15
run T2 "clear; ros2 service call /fan/stop std_srvs/srv/SetBool '{data: false}'" 3
ctrlc T1 4; wmctrl -c "Temperature plot"; sleep 1

cap "Your TODO: add integral action (PI). The solution, run in place of the P controller:" 2 "Your to do this week: add integral action, so the controller reaches the setpoint. Here is the solution, running in place of the proportional controller."
run T3 "clear; python3 ~/labs/tools/demo/temp_plot.py 26" 6
place_plot
run T1 "clear; python3 $S/room_sensor.py & python3 $S/fan_driver.py" 3
run T2 "clear; python3 ~/labs/solutions/week01/fan_controller_pi.py" 3
cap "PI: the integral keeps growing while any error is left, so the room reaches 26.0 C" 35 "With integral action, the controller keeps adding duty while any error is left, so the room reaches twenty six degrees and stays there."
ctrlc T2 1; ctrlc T1 2; pkill -f "week01/scripts"; wmctrl -c "Temperature plot"; sleep 1
run T1 "clear" 1; run T2 "clear" 0.5; run T1 "clear" 0.5

cap "Activity 3 (T3): what survives when the container is deleted? Write one file in /tmp and one in ~/work" 2 "Activity three. What survives when the container is deleted? We write one note in slash t m p, and one in the work folder."
run T3 "clear; echo hello > /tmp/note.txt; echo hello > ~/work/my_note.txt; ls /tmp/note.txt ~/work/my_note.txt" 4
cap "On your laptop: docker rm -f tc70045e, then docker run again - only ~/work/my_note.txt is still there" 8 "Then, on your laptop, delete the container and run it again. Only the note in the work folder is still there, because the work folder is a Docker volume. Keep your own files in work."
cap "Your turn: week01/README.md - Activities 1-3, then the PI TODO in fan_controller.py. Try first, then compare." 8 "Your turn. Follow the week one read me, activities one to three, then the to do in the fan controller. Try first, then compare with the solution."
rec_stop
pkill -f turtlesim_node; pkill -f "week01/scripts"
echo "saved $OUT"
