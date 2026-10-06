# Week 04 Inertial Sensing and Measurement

Everything here runs in the module's ROS 2 Humble container on your laptop (KiCad for the design review runs
natively). Start the environment first:

```bash
cd ../docker && docker compose up -d ros2     # then open http://localhost:6080 in your browser
```

In the container this folder is `~/labs/week04`. Work in `~/labs/week04/results`
(`mkdir -p ~/labs/week04/results && cd ~/labs/week04/results`). Do not commit the 57 MB noise-model CSV.
All numbers are from a simulator - label them "simulated" in your report.

| What | Where | Lab |
|---|---|---|
| Commands from the lecture, in order | [`commands.md`](commands.md) | |
| Record a static IMU log (/imu/data_raw -> CSV, deg/s and m/s^2) | [`scripts/imu_capture_static.py`](scripts/imu_capture_static.py) | A |
| Bias, noise density, Allan deviation, N, B, K (+ plot) | [`scripts/allan_deviation.py`](scripts/allan_deviation.py) | A |
| Spin the robot twice and record /imu/mag with the true yaw | [`scripts/mag_spin_capture.py`](scripts/mag_spin_capture.py) | B |
| Min-max and ellipse calibration, heading error before/after | [`scripts/magnetometer_calibration.py`](scripts/magnetometer_calibration.py) | B |
| Aliasing of motor vibration, four decimation strategies | [`scripts/aliasing_demo.py`](scripts/aliasing_demo.py) | C |
| ngspice I2C rise time and V_OL for a grid of Rp and Cb | [`scripts/i2c_rise.cir`](scripts/i2c_rise.cir) | C |

## Lab A - static IMU characterisation

```bash
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false          # terminal 1
nohup python3 ~/labs/week04/scripts/imu_capture_static.py --duration 600 --out imu_static.csv > cap.log 2>&1 &
ros2 run tc70045e_sim imu_noise_model --hours 2 --out static_imu.csv       # known N, B, K
python3 ~/labs/week04/scripts/allan_deviation.py static_imu.csv --col gz --plot allan_model_gz.png
python3 ~/labs/week04/scripts/allan_deviation.py imu_static.csv --col gz --plot allan_robot_gz.png
```
Do not move the robot until `cap.log` says `wrote`. Expected (measured 21 Sep 2026): noise model N = 0.0149
(true 0.015) deg/s/sqrt(Hz), B = 0.0042 deg/s at tau = 316 s (true about 0.005), K = 0.00027 (true 0.0002).
Robot gyro: sigma 0.107-0.116 deg/s, sigma/sqrt(fs/2) = 0.015, Allan N = 0.0107 (= 0.015/sqrt 2) =
0.64 deg/sqrt(h), minimum at tau 3-5 s, B about 0.012 deg/s (about 40 deg/h), then a +1/2 slope.

## Lab B - magnetometer calibration (moves the robot)

```bash
python3 ~/labs/week04/scripts/mag_spin_capture.py --turns 2 --wz 0.3
python3 ~/labs/week04/scripts/magnetometer_calibration.py mag_cal.csv --plot mag_cal.png
```
Expected: hard iron (6.0, -4.0) uT; heading error RMS/max raw 15.7/28.8 deg, min-max 2.2/6.0 deg,
ellipse 0.9/2.9 deg. The script stops the robot at the end.

## Lab C - aliasing and the I2C bus

```bash
python3 ~/labs/week04/scripts/aliasing_demo.py --plot aliasing.png
ngspice -b ~/labs/week04/scripts/i2c_rise.cir | grep " ns "
```
Expected: alias amplitude 0.50 (pick), 0.025 (boxcar), < 0.001 (FIR then decimate); ngspice rise times equal
0.847 Rp Cb (2.2k, 100p: 186 ns); V_OL 0.39 V at 1k, 0.47 V at 0.8k (fails the 0.4 V limit).
