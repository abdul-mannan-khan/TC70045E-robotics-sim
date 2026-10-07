# Week 03 (previous edition) – Actuators, Motors and Control

> **Note.** The October 2026 Week 3 is in `../README.md`. The scripts it mentions are still in `../scripts/`.

Everything here runs in the module's ROS 2 Humble container on your laptop (KiCad runs natively).
Start the environment first:

```bash
cd ../docker && docker compose up -d ros2     # then open http://localhost:6080 in your browser
```

In the container this folder is `~/labs/week03`. Work in `~/labs/week03/results` so your CSV files and plots
are saved in your repository (`mkdir -p ~/labs/week03/results && cd ~/labs/week03/results`).
All numbers are from a simulator - label them "simulated" in your report.

| What | Where | Lab |
|---|---|---|
| Commands from the lecture, in order | [`commands.md`](commands.md) | |
| Open-loop step test: dead zone, K, tau, dead time, speed quantum | [`scripts/step_test.py`](scripts/step_test.py) | A |
| PI(D) speed controller node with anti-windup, logging and metrics | [`scripts/pid_speed.py`](scripts/pid_speed.py) | B |
| One closed-loop run on a fresh bench with a load step | [`scripts/bench_run.sh`](scripts/bench_run.sh) | B |
| Mecanum inverse/forward kinematics against ground truth | [`scripts/kinematics_check.py`](scripts/kinematics_check.py) | C |

## Lab A - system identification (motor test bench, no Gazebo)

```bash
ros2 run tc70045e_sim motor_bench                    # terminal 1, leave running
python3 ~/labs/week03/making_it_move/scripts/step_test.py           # terminal 2, about 20 s
```
Writes `step_test.csv` and `step_test.png`. Expected (measured 21 Sep 2026): speed quantum 0.0096 m/s,
wheel first turns at 7 % duty, incremental K = 0.0084 (m/s)/% (30 -> 60 %), apparent K = 0.0067 (0 -> 30 %),
tau = 0.115 s, dead time Td = 0.032-0.039 s, dead zone from the intercept 6.0 %.
Stop the bench with Ctrl+C before Lab B.

## Lab B - closed-loop speed control

```bash
bash ~/labs/week03/making_it_move/scripts/bench_run.sh -p kp:=148.0 -p ki:=1290.0 -p out:=simc
LOAD=0.0 bash ~/labs/week03/making_it_move/scripts/bench_run.sh -p setpoint:=0.9 -p setpoint2:=0.3 \
    -p t_step2:=4.0 -p duration:=8.0 -p anti_windup:=false -p out:=aw_off
```
`bench_run.sh` starts a fresh bench (load step 0.1 m/s at 8 s, stops itself after 16 s) and runs `pid_speed.py`
with your parameters. Expected for SIMC gains 148/1290: overshoot 1.4 %, 2 % settling about 0.37 s,
steady-state error about 0 %, load dip 0.044 m/s (15 %), recovery 0.34-0.40 s. Plain IMC 238/2070 (dead time
ignored): 14-15 % overshoot. P only (ki 0): 52 % steady-state error. Wind-up: recovery 0.36-0.39 s with
anti-windup, 1.13-1.17 s without. Measured 21 Sep 2026 (motor_bench with a 40 ms dead time).

## Lab C - mecanum kinematics (simulated robot)

```bash
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false     # terminal 1, wait ~30 s
python3 ~/labs/week03/making_it_move/scripts/kinematics_check.py                    # terminal 2, ~30 s sim time
```
Drives 1 m forward, 1 m left and one turn on the spot (needs 1.2 m free ahead and to the left - restart the
simulator to return to the spawn point) and ALWAYS finishes with a zero Twist - the simulated base has no
command timeout. Expected: translation under-reads by 1.1-1.5 % (scale correction about 1.012-1.015),
rotation over-reads by 2.8-3.0 % (correction about 0.972), slip residual |mean| < 0.015 rad/s.

If the robot keeps moving after a crash: `ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"`.
