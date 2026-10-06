# Week 03 – Making It Move: Integrating Motors, Drivers and Encoders

Integrate a drive system the way you would with bought parts: bring up one motor, tune its speed controller,
check the wheel patterns, then fix a motor driver whose configuration file has three mistakes.
**Watch the demo video first** (`TC70045E_Week03_demo.mp4` on Blackboard) – it shows every command below.

```bash
cd ../docker && docker compose up -d ros2      # then http://localhost:6080, open terminals there
```

## The files

| File | What it is |
|---|---|
| [`scripts/base_driver.py`](scripts/base_driver.py) | the ROS 2 driver of a (pretend) motor-controller board: `/cmd_vel_in` → kinematics + config → `/cmd_vel`, `/driver/wheel_cmd`; command watchdog |
| [`config/base_driver.yaml`](config/base_driver.yaml) | its config "as delivered" – **three mistakes** (Activity 4). Copy it to `my_driver.yaml` and fix your copy |
| [`config/base_driver_good.yaml`](config/base_driver_good.yaml) | the corrected config (used in Activity 3; it is also the answer to Activity 4) |
| [`scripts/motion_test.py`](scripts/motion_test.py) | acceptance test: forward 1 m, left 1 m, turn 90°, watchdog – PASS/FAIL against ground truth |
| [`scripts/bench_run.sh`](scripts/bench_run.sh), [`scripts/pid_speed.py`](scripts/pid_speed.py) | one closed-loop run of the single-motor bench with your PID knobs, and its metrics |
| [`scripts/step_test.py`](scripts/step_test.py) | optional: automatic open-loop test of the motor bench (dead zone, gain, time constant) |
| [`scripts/kinematics_check.py`](scripts/kinematics_check.py) | optional: checks the mecanum kinematics against ground truth |

## Activities

```bash
# A1 one motor on the bench
ros2 run tc70045e_sim motor_bench
ros2 topic echo /motor/speed
ros2 topic pub -r 10 /motor/duty std_msgs/msg/Float32 "{data: 30.0}"

# A2 tune the knobs (each run starts a fresh bench; prints overshoot, settling, error, load dip)
bash ~/labs/week03/scripts/bench_run.sh -p kp:=148.0 -p ki:=1290.0 -p out:=pi_good

# A3 wheel patterns with a correctly configured driver
ros2 launch ~/labs/week02/launch/lego.launch.py
python3 ~/labs/week03/scripts/base_driver.py --ros-args --params-file ~/labs/week03/config/base_driver_good.yaml
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_in
ros2 topic echo /driver/wheel_cmd --field velocity

# A4 integration clinic
cp ~/labs/week03/config/base_driver.yaml ~/labs/week03/config/my_driver.yaml
python3 ~/labs/week03/scripts/base_driver.py --ros-args --params-file ~/labs/week03/config/my_driver.yaml
ros2 service call /reset_world std_srvs/srv/Empty
python3 ~/labs/week03/scripts/motion_test.py
```

## Measured on the reference laptop (ROS 2 Humble, 6 Oct 2026)

| Test | Result |
|---|---|
| A2 P only, kp 60 / 250 | 78 % / 38 % short of the target speed, never recovers from the load |
| A2 PI 238 / 2070 | 13.5 % overshoot, settles in 0.32 s, load dip 14 % recovered in 0.36 s |
| A2 PI 148 / 1290 | 1.4 % overshoot, settles in 0.30 s, load dip 16 % recovered in 0.34 s |
| A4 config as delivered | 0 of 4 tests pass (robot spins instead of driving straight, never stops by itself) |
| A4 after the three fixes | 4 of 4: forward 1.00 m, left 1.00 m, turn 90.2°, 0.00 m moved in 1.5 s of silence |

`previous_edition/` holds the earlier Week 3 notes (motor identification, PID derivation, KiCad layout).
