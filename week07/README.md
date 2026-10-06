# Week 07 RealSense D455 Depth Sensing

Scripts for this week's laboratory. Everything runs in the module's ROS 2 Humble container on your laptop, against the
simulated lab robot (`tc70045e_sim`), whose D455-style camera publishes the same topics as the real `realsense2_camera`
driver launched with `camera_namespace:=/`. The scripts therefore also run on a real D455.

Start the environment first - nothing here needs ROS 2 installed on your own machine:

```bash
cd ../docker && docker compose up -d ros2     # then open http://localhost:6080 in your browser
```

In a terminal on that desktop, start the range world (robot at the origin, facing a flat wall at x = 6.95 m):

```bash
ros2 launch tc70045e_sim sim.launch.py world:=range x:=0 y:=0 gui:=false
```

| Script | What it does | Run it with | Expected output (measured 2026-09-21) |
|---|---|---|---|
| [`scripts/depth_probe.py`](scripts/depth_probe.py) | live mean, sigma and fill rate of a 21 x 21 patch (14 rows above the centre) of `/camera/aligned_depth_to_color/image_raw` | `python3 ~/labs/week07/scripts/depth_probe.py` | at the origin: `Z_mean = 6810 mm  sigma = 88 mm  valid = 363/441 (fill 0.82)` |
| [`scripts/move_to.py`](scripts/move_to.py) | drives the robot to (x, y) in the world frame using `/ground_truth/odom` (holonomic, yaw held at 0), then stops | `python3 ~/labs/week07/scripts/move_to.py 0.0 3.3` | `reached x=0.000 y=3.296 (target 0.000 3.300) ... robot stopped` |
| [`scripts/range_test.py`](scripts/range_test.py) | Activity B: drives to camera-to-wall ranges 1, 2, 3, 4, 6 m, takes 20 frames at each, writes `range_test.csv` | `cd ~/labs/week07 && python3 scripts/range_test.py` (about 4 min) | `Z_true 3.996 m  mean 3996.2 mm  bias 0.2 mm  sigma 30.0 mm  fill 0.933` |
| [`scripts/depth_fit.py`](scripts/depth_fit.py) | fits sigma = k Z^2, prints Table 1, k, sigma_d = k f b, saves `fig1_sigma_vs_range.png` | `python3 scripts/depth_fit.py range_test.csv` | `k = 1.895e-03 1/m`, `sigma_d = 0.080 px` |
| [`scripts/plane_fit.py`](scripts/plane_fit.py) | Activity C: deprojects a region of interest, fits a plane (SVD): tilt, plane RMS, naive sigma, fill | `python3 move_to.py 0.0 3.3` then `python3 plane_fit.py` | 30 deg target: `tilt 30.1 deg  Z 1.337 m  plane RMS 2.9 mm  naive patch sigma 45.1 mm` |

`move_to.py` must stay in the same folder as `range_test.py` (it is imported). A matplotlib warning about `Axes3D`
is harmless. Other useful commands from the lecture:

```bash
python3 scripts/range_test.py --ranges 0.45 0.60 --frames 5 --out minz.csv   # MinZ check: fill 0.000 at 0.45 m
ros2 param get /stereo_depth subpixel_noise_px                               # the known answer: 0.08
ros2 topic delay -s /camera/aligned_depth_to_color/image_raw                 # -s = simulated time (about 0.47 s)
```

Honest limits: the simulated camera runs at about 7 Hz (software rendering; nominal 15 Hz, real D455 30 Hz), has no
systematic error, no incidence-angle or surface effects and no occlusion shadows. Label every result from it as
simulated. Commands that need a real D455 (`rs_launch.py`, `rs-enumerate-devices`) are in the lecture's optional boxes.

The simulated base has no command timeout. Every script stops the robot on exit; if one is killed, stop the robot with
`ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"`.
