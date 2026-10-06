# Week 07 – commands and code from the lecture, in order

Generated from the lecture (Week 07: RealSense D455 – Depth Sensing and Calibration – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 3.3 Intrinsics, distortion, rectification, extrinsics and alignment

```bash
docker compose up -d ros2        # then open http://localhost:6080 in the browser
```

```bash
ros2 launch tc70045e_sim sim.launch.py world:=range x:=0 y:=0 gui:=false
```

```bash
ros2 topic list | grep camera
```

```bash
ros2 topic echo --once /camera/color/camera_info
ros2 topic echo --once /camera/aligned_depth_to_color/camera_info --field k
```

```bash
ros2 run tf2_ros tf2_echo base_link camera_color_optical_frame
```

```bash
ros2 topic hz /camera/color/image_raw
ros2 topic hz /camera/aligned_depth_to_color/image_raw
```

```bash
ros2 topic bw /camera/color/image_raw
ros2 topic bw /camera/aligned_depth_to_color/image_raw
```

```bash
ros2 topic info /camera/aligned_depth_to_color/image_raw --verbose
```

```bash
ros2 run depth_image_proc point_cloud_xyzrgb_node --ros-args -p use_sim_time:=true \
  -r rgb/image_rect_color:=/camera/color/image_raw \
  -r rgb/camera_info:=/camera/color/camera_info \
  -r depth_registered/image_rect:=/camera/aligned_depth_to_color/image_raw \
  -r points:=/camera/depth/color/points
```

```bash
ros2 topic hz /camera/depth/color/points
ros2 topic bw /camera/depth/color/points
ros2 topic echo --once /camera/depth/color/points --field point_step
ros2 topic info /camera/depth/color/points --verbose
```

```bash
ros2 topic delay -s /camera/aligned_depth_to_color/image_raw
```

```text
Colour, 848 x 480, rgb8 (3 bytes/px)       = 1.221 MB per image
Depth,  848 x 480, 16UC1 (2 bytes/px)      = 0.814 MB per image
Point cloud, 848 x 480 points x 32 bytes   = 13.0  MB per cloud
                        (x,y,z,rgb + padding: point_step = 32)

At a measured simulator rate of 7 Hz:    colour 8.5 MB/s, depth 5.7 MB/s
At the real D455's 30 fps:               colour 36.6 MB/s, depth 24.4 MB/s,
                                         point cloud 391 MB/s   <-- note the units
USB 3.1 Gen 1 link = 5 Gbit/s ~= 625 MB/s theoretical, ~350-400 MB/s in practice
```

```text
lsusb -t | grep -i -A2 uvc          # want 5000M, not 480M (USB2)
rs-enumerate-devices -s             # serial number and firmware, without ROS
ros2 launch realsense2_camera rs_launch.py \
  camera_namespace:=/ \
  depth_module.depth_profile:=848x480x30 \
  rgb_camera.color_profile:=1280x720x30 \
  align_depth.enable:=true pointcloud.enable:=true \
  enable_gyro:=true enable_accel:=true unite_imu_method:=2
```

## 4.1 Troubleshooting table

```bash
python3 ~/labs/week07/scripts/depth_probe.py
```

```text
z = np.frombuffer(msg.data, dtype=np.uint16).reshape(msg.height, msg.width)
cy, cx = msg.height // 2 - ROW_OFFSET, msg.width // 2
patch = z[cy - HALF:cy + HALF + 1, cx - HALF:cx + HALF + 1].astype(np.float64)
good = patch[patch > 0]                    # 0 means "no depth": never average it in
```

```bash
cd ~/labs/week07
python3 scripts/range_test.py
```

```text
node.go(WALL_X - CAM_X - z, 0.0)          # drive until the camera is z metres from the wall
z_true = WALL_X - (node.pose[0] + CAM_X)  # the reference, from /ground_truth/odom
rows = collect(node, a.frames)            # 20 frames stamped 0.5 s after the robot stopped
```

```bash
python3 scripts/depth_fit.py range_test.csv
```

```bash
ros2 param get /stereo_depth subpixel_noise_px
ros2 param get /stereo_depth baseline_m
```

```bash
python3 scripts/range_test.py --ranges 0.45 0.60 --frames 5 --out minz.csv
```

```text
Z_true 1.004 m  mean  1003.9 mm  bias  -0.0 mm  sigma   1.9 mm  fill 0.985  (20 frames)
Z_true 1.996 m  mean  1996.1 mm  bias  -0.0 mm  sigma   7.5 mm  fill 0.979  (20 frames)
Z_true 2.996 m  mean  2995.9 mm  bias  -0.2 mm  sigma  16.7 mm  fill 0.956  (20 frames)
Z_true 3.996 m  mean  3996.0 mm  bias  -0.0 mm  sigma  30.2 mm  fill 0.933  (20 frames)
Z_true 5.996 m  mean  5996.8 mm  bias   0.7 mm  sigma  67.8 mm  fill 0.862  (20 frames)
```

```bash
cd ~/labs/week07/scripts
python3 move_to.py 0.0 2.0
python3 plane_fit.py
```

```bash
python3 move_to.py 0.0 3.3
python3 plane_fit.py
python3 move_to.py 0.0 4.6
python3 plane_fit.py
python3 move_to.py 0.0 0.0
```

```text
P = np.column_stack(((u[ok] - cx) * Z / fx, (v[ok] - cy) * Z / fy, Z))
c = P.mean(axis=0)
_, _, vt = np.linalg.svd(P - c, full_matrices=False)
n = vt[2]                                   # plane normal
resid = (P - c) @ n                         # signed distances from the plane
tilt = np.degrees(np.arccos(abs(n[2])))
```

```bash
ros2 launch tc70045e_sim sim.launch.py gui:=false
ros2 run teleop_twist_keyboard teleop_twist_keyboard          # second terminal
ros2 bag record -o ~/bags/w7_rgbd --storage mcap \
  /camera/color/image_raw /camera/color/camera_info \
  /camera/aligned_depth_to_color/image_raw \
  /camera/aligned_depth_to_color/camera_info \
  /scan /imu/data_raw /odom_raw /tf /tf_static      # third terminal
```

```bash
ros2 bag info ~/bags/w7_rgbd
ros2 bag play ~/bags/w7_rgbd --loop --clock
ros2 topic hz /camera/color/image_raw                   # another terminal
```

```text
"I have a rectified stereo depth camera with focal length 447 pixels and a
 95 mm baseline. Derive the relationship between disparity and depth, then
 propagate a sub-pixel disparity standard deviation of 0.1 px into a range
 standard deviation. Produce a table of predicted range error for Z = 0.5,
 1, 2, 3, 4, 5 and 6 m, in millimetres and as a percentage of range. Show
 every algebraic step and state every assumption you make."
```

```text
"Here is a numpy function that deprojects a 16UC1 depth patch with
 K = [fx 0 cx; 0 fy cy; 0 0 1] and fits a plane by SVD. Check the
 deprojection, the treatment of zero pixels, the choice of singular vector
 and the tilt formula. List defects with line numbers; do not rewrite it."
```
