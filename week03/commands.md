# Week 03 – commands and code from the lecture, in order

Generated from the lecture (Week 3: Making It Move – Integrating Motors, Drivers and Encoders – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 

```bash
ros2 run tc70045e_sim motor_bench                                             # T1: one motor, driver and encoder
ros2 topic echo /motor/speed                                                  # T2: the encoder
ros2 topic pub -r 10 /motor/duty std_msgs/msg/Float32 "{data: 5.0}"           # T3: try 5, 7, 10, 30, -30 %
```

```bash
cd ~/labs/week03 && mkdir -p results && cd results
bash ~/labs/week03/scripts/bench_run.sh -p kp:=60.0  -p ki:=0.0    -p out:=p_low
bash ~/labs/week03/scripts/bench_run.sh -p kp:=250.0 -p ki:=0.0    -p out:=p_high
bash ~/labs/week03/scripts/bench_run.sh -p kp:=238.0 -p ki:=2070.0 -p out:=pi_fast
bash ~/labs/week03/scripts/bench_run.sh -p kp:=148.0 -p ki:=1290.0 -p out:=pi_good
```

```bash
ros2 launch ~/labs/week02/launch/lego.launch.py                                                    # T1
python3 ~/labs/week03/scripts/base_driver.py --ros-args \
    --params-file ~/labs/week03/config/base_driver_good.yaml                                       # T2
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_in             # T3
ros2 topic echo /driver/wheel_cmd --field velocity                                                 # T4
```

```bash
cp ~/labs/week03/config/base_driver.yaml ~/labs/week03/config/my_driver.yaml     # work on your copy
python3 ~/labs/week03/scripts/base_driver.py --ros-args \
    --params-file ~/labs/week03/config/my_driver.yaml                             # T2 (Ctrl+C, edit, restart)
ros2 service call /reset_world std_srvs/srv/Empty                                 # T3: back to the start
python3 ~/labs/week03/scripts/motion_test.py                                      # T3: 4 tests, ~25 s
```
