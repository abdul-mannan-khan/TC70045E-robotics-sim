#!/bin/bash
# Week 6 demo video: see and understand with the D455 - find the coloured boxes and put them on the SLAM map.
# Tutor tool - run in the container desktop (narration is prepared first, see demo_lib.sh):
#   PREPARE=1 bash ~/labs/tools/demo/week06_demo.sh && DISPLAY=:1 bash ~/labs/tools/demo/week06_demo.sh /tmp/w6.mp4
source "$(dirname "$0")/demo_lib.sh"
OUT=${1:-/tmp/week06_demo.mp4}
W=~/labs/week06
pkill -f gzserver; pkill -f gzclient; sleep 2
rm -f /tmp/w6demo_*.log
place_views() {   # Gazebo (the simulated world) top left, RViz (what the robot knows) bottom left
    for i in 1 2 3; do place Gazebo 0 90 955 495; place RViz 0 590 955 490; sleep 1; done; }

caption_bar
term T1 960 90 960 300
term T2 960 400 960 330
term T3 960 740 960 340
rec_start "$OUT"

cap "Week 6 demo - see and understand with the D455: find the boxes, put them on the map" 5 "Week six demo. See and understand with the D455 camera. The robot finds two coloured boxes in its camera image and puts them on its map."
cap "Step 1 (T1): robot + D455 + SLAM + RViz, and the tour past both boxes" 2 "Step one. In terminal one, one launch file starts the robot with its camera, slam toolbox and RViz. Tour true drives past the red box and the green box, and stops to look at each."
run T1 "ros2 launch $W/launch/perception.launch.py tour:=true 2>&1 | tee /tmp/w6demo_launch.log" 12
cap "Step 2 (T2): the box finder - colour mask, depth, back-projection, transform to the map" 2 "Step two. In terminal two, the box finder: the solution of this week's activity. For every colour image it makes a colour mask, takes the depth of the blob, turns the pixel into a three D point, and transforms it into the map."
run T2 "python3 ~/labs/solutions/week06/box_finder.py --ros-args -p use_sim_time:=true 2>&1 | tee -i /tmp/w6demo_finder.log" 18
place_views
say "Gazebo, top left, is the simulated world. RViz, below, shows the map, the camera image, and the mask: white where the colour matches." 3
cap "Step 3 (T3): the camera matrix K - fx, cx, fy, cy - from camera_info" 2 "Step three. The camera matrix K comes with every image, on the camera info topic. f x and f y are the focal length in pixels; c x and c y the image centre."
run T3 "clear; ros2 topic echo --no-daemon --once /camera/color/camera_info --field k" 8
cap "The pinhole model: X = (u - cx) * Z / fx,  Y = (v - cy) * Z / fy  -  a pixel plus its depth is a 3-D point" 7 "The pinhole model. A pixel is a ray from the camera. The depth image says how far along the ray the box is. X equals u minus c x, times Z, over f x."
cap "Watch Gazebo: the robot stops with the red box off to the right of the image" 20 "Watch Gazebo. The robot stops with the red box off to the right of the camera image. The mask in RViz shows the box in white, and a red cube appears on the map."
wait_for "leg 3 done" /tmp/w6demo_launch.log 300
cap "Now the green box: the same HSV recipe with a different hue (H about 60)" 20 "Now the green box. The same recipe with a different hue: about sixty on OpenCV's scale. A green cube appears on the map."
wait_for "leg 8 done" /tmp/w6demo_launch.log 300
wait_for "tour finished" /tmp/w6demo_launch.log 200
cap "Step 4 (T2): Ctrl+C prints each box's position and its error against the truth" 2 "Step four. Control C in terminal two prints each box's position on the map, and its error against the true position."
ctrlc T2 4
cap "Both boxes on the map within about 10 cm - with a 424 x 240 camera, from 1.5 m" 8 "Both boxes are on the map within about ten centimetres, with a small four hundred and twenty four by two hundred and forty pixel camera, from one and a half metres away."
cap "Your turn: week06/README.md - A1-A3, then the three TODOs in box_finder.py. Then: Assessment 1." 8 "Your turn. Follow the week six read me, activities one to three, then the three to do's in the box finder. Try first, then compare with the solution. And then, submit assessment one."
rec_stop
ctrlc T1 8; pkill -f gzserver; pkill -f gzclient
echo "saved $OUT"
