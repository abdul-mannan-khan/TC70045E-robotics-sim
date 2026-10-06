# Week 04 – commands and code from the lecture, in order

Generated from the lecture (Week 04: Inertial Sensing and Measurement – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 💻 Today's laboratory kit

```bash
# terminal 1 (leave running all session; Gazebo needs ~30 s)
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false

# terminal 2
ros2 topic hz /imu/data_raw       # average rate: 100.0 (sim time)
ros2 topic hz /imu/mag            # average rate: ~49.6
ros2 interface show sensor_msgs/msg/Imu | grep -v "^#"
```

## 2.2 Configuration choices – and what they cost you

```text
who_am_i();                         // block until the chip answers
device_reset();  wakeup();
clock_source(1);                    // best available clock
gyro_low_pass_filter(0);            // DLPF setting 0
gyro_sample_rate_divider(0);        // 0 = fastest ODR (1.1 kHz)
gyro_calibration();                 // bias AT POWER-ON
accel_calibration();
gyro_full_scale(2000);              // +/-2000 dps: widest, coarsest
accel_full_scale(16);               // +/-16 g
magnetometer_init(100);             // continuous mode, 100 Hz
```

## 2.4 Noise density, angle random walk and bias instability

```bash
# 1. the stream
ros2 topic hz /imu/data_raw              # ~100 Hz
ros2 topic echo /imu/data_raw --once     # rad/s and m/s^2

# 2. 600 s static capture in the background (log in cap.log)
mkdir -p ~/labs/week04/results && cd ~/labs/week04/results
nohup python3 ~/labs/week04/scripts/imu_capture_static.py \
    --duration 600 --out imu_static.csv > cap.log 2>&1 &
tail -f cap.log                          # Ctrl+C stops tail, not the capture
```

```bash
# 3. two hours of static data with KNOWN parameters, then the analysis
ros2 run tc70045e_sim imu_noise_model --hours 2 --out static_imu.csv
python3 ~/labs/week04/scripts/allan_deviation.py static_imu.csv \
    --col gz --plot allan_model_gz.png

# 5. your own capture, after cap.log says "wrote 59989 samples ..."
python3 ~/labs/week04/scripts/allan_deviation.py imu_static.csv \
    --col gz --plot allan_robot_gz.png
#    ... repeat with --col gx, --col gy and --col az
```

```text
c = np.concatenate(([0.0], np.cumsum(x)))     # running sum
for m in ms:                                   # cluster sizes 1, 2, 3 ...
    y = (c[m::m] - c[:-m:m][:len(c[m::m])]) / m    # cluster means
    rows.append((m * t0, len(x) // m,
                 np.sqrt(0.5 * np.mean(np.diff(y) ** 2))))
```

```text
model values ...: N = 0.0150 deg/s/sqrt(Hz) = 0.900 deg/sqrt(h) ARW,
                  B = 0.0050 deg/s, K = 0.00020 deg/s/sqrt(s)
N = adev(1 s) = 0.01490 deg/s/sqrt(Hz)  = 0.894 deg/sqrt(h) angle random walk
B = min adev/0.664 = 0.00415 deg/s (tau 316.2 s, K 22, +/-15 %) = 14.9 deg/h
K = adev*sqrt(3/tau) at tau = 681 s: 0.000274 deg/s/sqrt(s) (only if rising)
```

```text
gz: 59899 samples, t0 = 0.0100 s -> fs = 100.0 Hz, length 600 s
bias = +0.04357 deg/s   sigma = 0.10929 deg/s
noise density = sigma/sqrt(fs/2) = 0.01546 deg/s/sqrt(Hz)
    1.00      598    0.010667      3%
    4.64      129    0.007835      6%
   46.42       12    0.018169     21%
N = adev(1 s) = 0.01067 deg/s/sqrt(Hz)  = 0.640 deg/sqrt(h) angle random walk
B = min adev/0.664 = 0.01180 deg/s (tau 4.6 s, K 129, +/-6 %) = 42.5 deg/h
```

## 5.3 Sampling, Nyquist and a concrete aliasing failure

```bash
ros2 topic hz /imu/mag                    # ~50 Hz
cd ~/labs/week04/results
python3 ~/labs/week04/scripts/mag_spin_capture.py --turns 2 --wz 0.3
python3 ~/labs/week04/scripts/magnetometer_calibration.py mag_cal.csv \
    --plot mag_cal.png
```

```text
cases = {'raw': h, 'min-max': (h - b_mm) @ G.T, 'ellipse': (h - c_el) @ W.T}
yaw = np.degrees(np.arctan2(hc[:, 0], hc[:, 1]))     # ENU yaw, north = +y
err = (yaw - yaw_true + 180) % 360 - 180
```

```text
turned 720.2 deg, wrote 2097 magnetometer samples to mag_cal.csv
2097 samples, 720 deg of rotation; mz = -42.01 +/- 0.30 uT (unobservable)
min-max : hard iron (5.88, -4.09) uT, soft-iron gains (0.938, 1.071)
ellipse : hard iron (5.99, -4.00) uT, soft iron [[0.934 -0.050] [-0.050 1.073]]
heading error [deg]  mean     RMS  max|err|  radius sd/mean
raw                   0.03   15.72    28.75        25.21 %
min-max              -0.19    2.21     5.96         3.90 %
ellipse              -0.00    0.86     2.87         1.53 %
```

## 7.2 Justifying the I²C pull-up resistor – the calculation for your report

```bash
cd ~/labs/week04/results
python3 ~/labs/week04/scripts/aliasing_demo.py --plot aliasing.png
ngspice -b ~/labs/week04/scripts/i2c_rise.cir | grep " ns "
```

```text
internal rate 1125 Hz, report rate 25.0 Hz (Nyquist 12.5 Hz); ...
    v    f_vib  f_alias |   A pick  B boxcar  C FIR+decim  D pick+2Hz LPF | in D
  0.10     23.8     1.23 |    0.500     0.026        0.000           0.491 | 0.202
  0.20     47.5     2.47 |    0.502     0.026        0.000           0.073 | 0.200
  0.30     71.3     3.70 |    0.500     0.025        0.000           0.002 | 0.201
  0.40     95.1     4.93 |    0.499     0.024        0.000           0.000 | 0.200
  0.50    118.8     6.16 |    0.499     0.024        0.000           0.000 | 0.200
```

```text
   Rp     Cb     tr (ngspice)   0.847 Rp Cb    V_OL
  0.8k   100p   67.783 ns   67.76 ns   0.470418 V
  1k   400p   338.92 ns   338.8 ns   0.387379 V
  2.2k   100p   186.406 ns   186.34 ns   0.188127 V
  2.2k   200p   372.812 ns   372.68 ns   0.188127 V
  4.7k   100p   398.232 ns   398.09 ns   0.0908132 V
```

```text
"I have a 10-minute static log from a simulated MEMS gyroscope.
CSV columns: t (s), gx, gy, gz (deg/s). Sample interval 0.01 s.
1. Compute the non-overlapping Allan deviation for tau = 0.01 s to 100 s,
   with the number of clusters K and the uncertainty 1/sqrt(2(K-1)).
   numpy only, no Allan-variance library.
2. Report N in deg/sqrt(h) and B = adev_min/0.664 in deg/h, and state
   whether N is the one-sided noise density or ND/sqrt(2).
3. From N and B, how long can I integrate before bias dominates?
4. Which of your numbers does my 10-minute record NOT support, and why?"
```
