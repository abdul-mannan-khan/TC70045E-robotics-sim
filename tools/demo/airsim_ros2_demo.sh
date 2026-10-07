#!/bin/bash
# Demo video: AirSim + PX4 WITH ROS 2 (sensor bridge, control bridge, RViz, a mission node), in the Neighborhood
# (urban) and Mountains worlds. Tutor tool - run in the drone container desktop:
#   DISPLAY=:1 bash ~/labs/tools/demo/airsim_ros2_demo.sh /tmp/airsim_ros2_demo.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/airsim_ros2_demo.mp4}
E=~/labs/examples/airsim
rm -f /tmp/r2sq1.log /tmp/r2sq2.log
drone-sim stop >/dev/null 2>&1
rm -f /tmp/simstart*.log

caption_bar
term T1 960 90 960 240
term T2 960 340 960 240
term T3 960 590 960 240
term T4 960 840 960 240
rec_start "$OUT"

cap "Drones WITH ROS 2: two bridge nodes turn AirSim and PX4 into ordinary ROS 2 topics and services" 5 "Drones with ROS 2. Two small bridge nodes turn the simulator and the autopilot into ordinary ROS 2 topics and services. After that, a mission is just a ROS 2 node."
cap "Step 1 (T1): start the urban Neighborhood world" 2 "Step one. In terminal one we start the urban neighbourhood world."
run T1 "drone-sim start --world neighborhood | tee /tmp/simstart1.log" 3
say "AirSim and the PX4 autopilot start together. This takes about a minute." 45
wait_for "ready for take-off" /tmp/simstart1.log 240
place AirSimNH 0 90 955 540
sleep 10
cap "Step 2 (T2): the SENSOR bridge - camera, pose, IMU and GPS from AirSim become ROS 2 topics" 2 "Step two. In terminal two, the sensor bridge. It reads the camera, the pose, the IMU and the GPS from AirSim and publishes them as ROS 2 topics."
run T2 "python3 $E/03_airsim_ros2_bridge.py" 6
cap "Step 3 (T3): the CONTROL bridge - ROS 2 commands go to the autopilot through MAVSDK" 2 "Step three. In terminal three, the control bridge. It offers take off and land services, and a velocity command topic, and passes them to the autopilot."
run T3 "python3 $E/04_px4_ros2_bridge.py --ros-args -p altitude:=15.0" 6
cap "Step 4 (T4): the drone is now a ROS 2 robot - list its topics" 2 "Step four. The drone is now a ROS 2 robot like any other. We list its topics."
run T4 "ros2 topic list | grep drone" 5
cap "Step 5: RViz shows the front camera and the drone's path" 2 "Step five. RViz shows the front camera and the path of the drone."
run T4 "rviz2 -d $E/airsim.rviz > /dev/null 2>&1 &" 12
place RViz 0 640 955 440
sleep 3
cap "Step 6 (T4): take off with a ROS 2 service call" 2 "Step six. Take off, with an ordinary ROS 2 service call."
run T4 "clear; ros2 service call /drone/takeoff std_srvs/srv/Trigger" 4
say "The drone arms, climbs to fifteen metres, above the trees, and holds its position, waiting for velocity commands." 18
cap "Step 7 (T4): fly forward with a velocity command on /drone/cmd_vel" 2 "Step seven. We fly forward by publishing a velocity command, exactly like driving a ground robot."
run T4 "clear; ros2 topic pub -r 10 /drone/cmd_vel geometry_msgs/msg/Twist \"{linear: {x: 2.0}}\"" 6
ctrlc T4 4
say "When the commands stop, the bridge holds the drone still. A safe default." 4
cap "Step 8 (T4): a mission node - a 10 m square flown with ROS 2 messages only" 2 "Step eight. A mission node. It reads the drone's position from ROS 2 and sends velocity commands. A ten metre square, with no AirSim or MAVSDK code in it."
run T4 "clear; python3 -u $E/05_fly_square_ros2.py --side 10 2>&1 | tee /tmp/r2sq1.log" 5
cap "Watch the path grow in RViz while the drone flies the square (real time)" 20 "Watch the path grow in RViz while the drone flies the square. This is real time."
wait_for RESULT /tmp/r2sq1.log 180
sleep 5
cap "Step 9: the same nodes in the Mountains world" 2 "Step nine. The same nodes work in any world. We switch to the mountains."
ctrlc T2 1; ctrlc T3 1
run T1 "clear; drone-sim stop; drone-sim start --world mountains | tee /tmp/simstart2.log" 3
say "The bridges are restarted after the new world is up." 60
wait_for "ready for take-off" /tmp/simstart2.log 240
place LandscapeMountains 0 90 955 540
run T2 "clear; python3 $E/03_airsim_ros2_bridge.py" 5
run T3 "clear; python3 $E/04_px4_ros2_bridge.py --ros-args -p altitude:=30.0" 6
run T4 "clear; python3 -u $E/05_fly_square_ros2.py --side 10 2>&1 | tee /tmp/r2sq2.log" 25
cap "The mission node flies the square over the valley - the code did not change (real time)" 20 "The mission node flies the same square over the valley. Not one line of code changed."
wait_for RESULT /tmp/r2sq2.log 200
sleep 5
cap "Your turn: examples/airsim/README.md, steps 3 to 5. Make the mission node fly a survey pattern." 8 "Your turn. Follow steps three to five in the examples folder, then make the mission node fly a survey pattern."
rec_stop
ctrlc T2 1; ctrlc T3 1
pkill -f rviz2
run T1 "drone-sim stop" 4
echo "saved $OUT"
