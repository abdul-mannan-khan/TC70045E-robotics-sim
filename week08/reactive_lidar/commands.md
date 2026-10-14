# Week 08 – commands and code from the lecture, in order

Generated from the lecture (Week 08: 2D LiDAR Sensing and Reactive Behaviour – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 2.1 Frames: where is "in front of the robot"?

```python
def wrap_deg(x):
    return (np.asarray(x) + 180.0) % 360.0 - 180.0

in_sector = np.abs(wrap_deg(angle_deg - centre_deg)) <= half_width_deg
```

```bash
ros2 launch tc70045e_sim sim.launch.py world:=range x:=0 y:=0 gui:=false camera:=false
```

```bash
ros2 topic echo --once /scan --field header.frame_id
ros2 topic echo --once /scan --field angle_min
ros2 topic echo --once /scan --field angle_max
ros2 topic echo --once /scan --field angle_increment
ros2 topic echo --once /scan --field time_increment
ros2 topic echo --once /scan --field scan_time
ros2 topic echo --once /scan --field range_min
ros2 topic echo --once /scan --field range_max
ros2 topic info /scan --verbose
```

```bash
ros2 topic hz /scan
```

```bash
ros2 topic delay -s /scan
```

```bash
python3 ~/labs/week08/scripts/scan_probe.py
```

```bash
python3 ~/labs/week08/scripts/scan_probe.py --centre 180 --half 5 --scans 5
python3 ~/labs/week08/scripts/scan_probe.py --centre 53 --half 4 --scans 5
```

```bash
cd ~/labs/week08/scripts
python3 move_to.py 5.93 0.0 && python3 scan_probe.py --scans 40 | tail -1
python3 move_to.py 3.93 0.0 && python3 scan_probe.py --scans 40 | tail -1
python3 move_to.py 1.93 0.0 && python3 scan_probe.py --scans 40 | tail -1
python3 move_to.py 0.0 0.0
```

## 4.1 Deriving the envelope

```text
reaction distance   v * T_total   = 0.30 * 0.450  = 0.135 m
braking distance    v^2 / (2a)    = 0.09 / 2.0    = 0.045 m
LiDAR to front edge r_robot                      = 0.130 m
margin              m                            = 0.100 m
                                                  ---------
minimum detection distance  d_safe               = 0.410 m   (range_min 0.15 m)
```

## 4.2 Three reactive behaviours, and the code you will run

```python
def nearest(s, centre_deg, half_deg):
    r = np.asarray(s.ranges, dtype=np.float64)
    ang = np.degrees(s.angle_min + np.arange(r.size) * s.angle_increment)
    ok = np.isfinite(r) & (r > 0.0) & (r >= s.range_min) & (r <= s.range_max)
    ok &= np.abs(wrap_deg(ang - centre_deg)) <= half_deg
    if not ok.any():
        return math.inf, 0.0
    i = np.flatnonzero(ok)[np.argmin(r[ok])]
    return r[i], float(wrap_deg(ang[i]))
```

```bash
cd ~/labs/week08/scripts
python3 move_to.py 4.93 0.0
python3 reactive.py --mode follow --d 0.8          # Ctrl-C after about 20 s
```

```bash
ros2 topic echo --once /ground_truth/odom --field pose.pose.position
```

```bash
python3 move_to.py 6.45 0.0
python3 reactive.py --mode follow --d 0.8          # Ctrl-C after about 15 s
```

```bash
python3 move_to.py 0.0 0.0
python3 reactive.py --mode guard --d 3.0           # Ctrl-C after about 20 s
ros2 topic echo --once /ground_truth/odom --field pose.pose.orientation
```

```bash
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false
python3 ~/labs/week08/scripts/reactive.py --mode avoid --v 0.2 --d 0.5
```

```text
if r < a.d:                                   # first scan whose front minimum is inside d
    t_dec, read, age, x_dec = t, r, t - stamp, node.pose[0]
...
cmd.linear.x = max(0.0, a.v - a.a * (t - t_dec))   # constant-deceleration ramp, 50 Hz
...
clearance = WALL_X - (node.pose[0] + FRONT_X)      # front edge to wall, from ground truth
```

```bash
cd ~/labs/week08/scripts
python3 stop_test.py --v 0.2 --d 0.6 --a 1.0 --runs 3
python3 stop_test.py --v 0.3 --d 0.6 --a 1.0 --runs 3
python3 stop_test.py --v 0.5 --d 0.6 --a 1.0 --runs 3
```

```bash
python3 stop_test.py --v 0.3 --d 0.6 --a 1.0 --delay 0.2 --runs 3
```

```text
v 0.20 | read 0.588 m (true 0.608) | after decision 0.025 m | clearance 0.453 m
v 0.20 | read 0.600 m (true 0.618) | after decision 0.027 m | clearance 0.461 m
v 0.20 | read 0.592 m (true 0.610) | after decision 0.025 m | clearance 0.455 m
v 0.30 | read 0.592 m (true 0.614) | after decision 0.054 m | clearance 0.430 m
v 0.30 | read 0.542 m (true 0.572) | after decision 0.052 m | clearance 0.390 m
v 0.30 | read 0.561 m (true 0.608) | after decision 0.056 m | clearance 0.423 m
v 0.50 | read 0.594 m (true 0.616) | after decision 0.137 m | clearance 0.349 m
v 0.50 | read 0.551 m (true 0.566) | after decision 0.135 m | clearance 0.301 m
v 0.50 | read 0.541 m (true 0.566) | after decision 0.142 m | clearance 0.294 m
v 0.30 delay 0.20 | read 0.541 m (true 0.509, age 0.200 s) | after 0.052 m | clearance 0.327 m
v 0.30 delay 0.20 | read 0.542 m (true 0.512, age 0.205 s) | after 0.056 m | clearance 0.327 m
v 0.30 delay 0.20 | read 0.536 m (true 0.512, age 0.196 s) | after 0.054 m | clearance 0.328 m
```

```text
"A 2D LiDAR publishes sensor_msgs/LaserScan. I measured a scan rate of
 5.5 Hz, an angle_increment of 0.50 degrees and a data age of 200 ms.
 Derive the minimum distance at which an obstacle must be detected for a
 0.30 m/s robot whose front edge is 0.13 m ahead of the LiDAR, braking at
 1.0 m/s^2, listing every latency term separately. Then state the smallest
 obstacle width this sensor can resolve at 1 m and at 4 m."
```

```text
"Here is a ROS 2 LaserScan callback. Identify every way it can misbehave
 when ranges contain inf, nan or 0.0; when angle_increment is negative;
 and when the sector of interest straddles +/- pi. Do not rewrite it yet:
 list the defects with the line each one is on."
```
