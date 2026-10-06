#!/bin/bash
# TC70045E - self-test of the Docker lab kit. Run it inside the container before your first laboratory:
#     bash ~/labs/tools/validate.sh
# It checks the ROS 2 packages the lectures use, starts the simulated lab robot headless for about a minute,
# measures its sensor rates, and starts the EKF, SLAM and navigation nodes against it. Nothing is installed.
# It takes about three minutes; a slow laptop may need longer (the waits are generous on purpose).
# Every check prints RESULT|<name>|OK or RESULT|<name>|FAIL; the summary at the end counts them.
LOG=${LOG:-/tmp/tc70045e_validate.log}
: > "$LOG"
exec > >(tee -a "$LOG") 2>&1
ok()  { echo "RESULT|$1|OK   ${2:-}"; }
bad() { echo "RESULT|$1|FAIL ${2:-}"; }
cleanup() { [ -n "$SIM" ] && kill -- -"$SIM" 2>/dev/null; kill $(jobs -p) 2>/dev/null; sleep 2; }
trap cleanup EXIT

echo "=== TC70045E kit self-test $(date -u) ==="
. /etc/os-release
source /opt/ros/humble/setup.bash 2>/dev/null || { bad ros_setup "no /opt/ros/humble"; exit 1; }
[ -f /opt/tc70045e_ws/install/setup.bash ] && source /opt/tc70045e_ws/install/setup.bash
[ "$ROS_DISTRO" = humble ] && ok ros_distro "$ROS_DISTRO on $PRETTY_NAME" || bad ros_distro "$ROS_DISTRO"
export ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-7}

echo "--- ROS 2 packages ---"
for p in tc70045e_sim gazebo_ros realsense2_camera depth_image_proc rtabmap_launch slam_toolbox cartographer_ros \
         nav2_bringup nav2_simple_commander robot_localization imu_filter_madgwick pcl_ros cv_bridge \
         camera_calibration octomap_server topic_tools teleop_twist_keyboard rosbag2_storage_mcap; do
  ros2 pkg prefix "$p" >/dev/null 2>&1 && ok "pkg:$p" || bad "pkg:$p" "not found"
done
for e in wheel_odometry magnetometer stereo_depth battery motor_bench virtual_mcu imu_noise_model; do
  ros2 pkg executables tc70045e_sim 2>/dev/null | grep -qw "$e" && ok "exec:tc70045e_sim/$e" || bad "exec:tc70045e_sim/$e"
done

echo "--- Python stack (NumPy must stay below 2 or cv_bridge breaks) ---"
python3 - <<'PY' && ok py:stack "$(python3 -c 'import numpy;print("numpy",numpy.__version__)')" || bad py:stack
import numpy, cv2, scipy, matplotlib, pandas, serial, can, mavsdk
from cv_bridge import CvBridge
assert numpy.__version__ < "2"
PY
for t in ngspice socat; do command -v $t >/dev/null && ok "tool:$t" || bad "tool:$t"; done

echo "--- the simulated lab robot (headless, about 60 s) ---"
if [ -z "$DISPLAY" ]; then Xvfb :77 -screen 0 1280x1024x24 >/dev/null 2>&1 & export DISPLAY=:77; sleep 2; fi
# 424 x 240 camera: at full size a laptop without a GPU renders so slowly that every sensor rate drops with it
setsid ros2 launch tc70045e_sim sim.launch.py gui:=false camera_width:=424 camera_height:=240 > /tmp/tc_sim.log 2>&1 &
SIM=$!
sleep 35
rate() { timeout 10 ros2 topic hz "$1" 2>/dev/null | grep "average rate" | tail -1 | awk '{print $3}'; }
check_rate() {  # topic minimum_hz
  r=$(rate "$1"); if [ -n "$r" ] && awk "BEGIN{exit !($r >= $2)}"; then ok "sim:$1" "$r Hz"; else bad "sim:$1" "${r:-no data} (need >= $2 Hz)"; fi
}
check_rate /scan 5
check_rate /imu/data_raw 80
check_rate /imu/mag 40
check_rate /odom_raw 20
check_rate /ground_truth/odom 40
check_rate /battery 8
check_rate /camera/color/image_raw 2
check_rate /camera/aligned_depth_to_color/image_raw 2
timeout 8 ros2 run tf2_ros tf2_echo odom laser_link 2>&1 | grep -q Translation && ok tf:odom_to_laser || bad tf:odom_to_laser
timeout 6 ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {y: 0.2}}" >/dev/null 2>&1
timeout 5 ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}" >/dev/null 2>&1
y=$(timeout 8 ros2 topic echo --once /ground_truth/odom --field pose.pose.position.y 2>/dev/null | head -1)
awk "BEGIN{exit !(${y:-0} > 0.3)}" && ok sim:moves_sideways "y = $y m" || bad sim:moves_sideways "y = ${y:-?}"

echo "--- EKF, SLAM and navigation start against the simulator ---"
CFG=$(ros2 pkg prefix tc70045e_sim)/share/tc70045e_sim/config
# The wheel odometry already publishes odom -> base_footprint, so the test EKF must not (two publishers of one
# transform make SLAM fail). In the Week 6 lab you start the simulator with odom_tf:=false instead.
ros2 launch slam_toolbox online_async_launch.py slam_params_file:=$CFG/slam_toolbox.yaml use_sim_time:=true > /tmp/tc_slam.log 2>&1 &
ros2 run imu_filter_madgwick imu_filter_madgwick_node --ros-args -p use_mag:=false -p publish_tf:=false -p use_sim_time:=true > /tmp/tc_madg.log 2>&1 &
ros2 run robot_localization ekf_node --ros-args --params-file $CFG/ekf.yaml -p publish_tf:=false -r odometry/filtered:=/odom_ekf_test > /tmp/tc_ekf.log 2>&1 &
sleep 30
timeout 30 ros2 topic echo --once /odom_ekf_test --field header.frame_id >/dev/null 2>&1 && ok ekf:publishes || bad ekf:publishes "$(tail -2 /tmp/tc_ekf.log | tr '\n' ' ')"
timeout 40 ros2 topic echo --once /map --field info.resolution >/dev/null 2>&1 && ok slam:map || bad slam:map "$(tail -2 /tmp/tc_slam.log | tr '\n' ' ')"
timeout 120 ros2 launch nav2_bringup navigation_launch.py params_file:=$CFG/nav2_params.yaml use_sim_time:=true --show-args >/dev/null 2>&1 \
  && ok nav2:launch_resolves || bad nav2:launch_resolves

echo "=== finished $(date -u) ==="
echo "SUMMARY: OK=$(grep -c '|OK' $LOG) FAIL=$(grep -c '|FAIL' $LOG)   (log: $LOG)"
grep '|FAIL' "$LOG" || echo "no failures - the kit is ready"
