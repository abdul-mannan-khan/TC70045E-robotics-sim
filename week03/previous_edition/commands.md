# Week 03 – commands and code from the lecture, in order

Generated from the lecture (Week 03: Actuators, Motors and Control – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 💻 Today's laboratory kit: the ROS 2 Humble Docker container

```bash
# on your laptop, in the student repository (first run pulls the image)
cd docker && docker compose up -d ros2
# open http://localhost:6080 - every command below is typed in a
# terminal on that browser desktop. Your repository is at ~/labs.

printenv ROS_DISTRO                      # humble
ros2 pkg executables tc70045e_sim        # lists motor_bench, wheel_odometry ...

# terminal 1: the simulated lab robot, lightest settings
ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false
# terminal 2: wait ~30 s for Gazebo, then check the encoders
ros2 topic hz /wheel_speeds              # average rate: 24.9
```

## 3.3 Quadrature encoders: ×4 decoding and the speed quantum

```bash
# terminal 1 - the plant (leave it running)
ros2 run tc70045e_sim motor_bench
#   ... motor bench ready ... Speed quantum = 0.0096 m/s

# terminal 2 - poke it by hand
ros2 topic hz /motor/speed                    # average rate: ~100
ros2 topic pub --once /motor/duty std_msgs/msg/Float32 "{data: 30.0}"
ros2 topic echo /motor/speed --once           # data: about 0.2 (a multiple of 0.0096)
ros2 topic pub --once /motor/duty std_msgs/msg/Float32 "{data: 0.0}"
```

```bash
# terminal 2 - the scripted identification (about 20 s)
cd ~/labs/week03 && mkdir -p results && cd results
python3 ~/labs/week03/scripts/step_test.py
#   writes step_test.csv and step_test.png in the current folder
```

```python
def model(t, v0, dv, tau, td):
    """First order plus dead time, step applied at t = 0."""
    return v0 + dv * (1.0 - np.exp(-np.clip(t - td, 0.0, None) / tau))

p, _ = curve_fit(model, ts, vs, p0=[v0, dv, 0.1, 0.03],
                 bounds=([-2, -2, 0.005, 0.0], [2, 2, 2.0, 0.5]))
```

```text
samples 1937 over 22.0 s -> 88.0 Hz
speed quantum: smallest |v| > 0 = 0.0096 m/s (theory 2 pi r/(C_rev Ts) = 0.0096)
dead zone: wheel first turns at 7 % duty (0.0076 m/s)
mean +/- sd over 3 repeats (K in (m/s)/%, tau and Td in s):
  0->30 % K 0.00673 +/- 0.00001  tau 0.116 +/- 0.002  Td 0.034 +/- 0.001
 30->60 % K 0.00841 +/- 0.00001  tau 0.117 +/- 0.000  Td 0.035 +/- 0.003
 60->0  % K 0.00757 +/- 0.00001  tau 0.115 +/- 0.001  Td 0.035 +/- 0.001
dead zone from the intercept: u0 = low - v(low)/K = 6.0 %
```

## 5.2 Anti-windup

```text
u_unsat = self.kp * e + self.i_term + self.ki * e * dt + self.d_term
saturated = abs(u_unsat) > self.u_max and np.sign(u_unsat) == np.sign(e)
if not (self.aw and saturated):                  # conditional integration
    self.i_term += self.ki * e * dt
u = float(np.clip(self.kp * e + self.i_term + self.d_term,
                  -self.u_max, self.u_max))
```

## 5.3 Tuning with numbers, not with a slider

```bash
# each run: a FRESH bench (load step 0.1 m/s at 8 s, stops itself
# after 16 s) plus pid_speed.py with the parameters you give it
cd ~/labs/week03/results
bash ~/labs/week03/scripts/bench_run.sh -p kp:=148.0 -p ki:=1290.0 -p out:=simc
bash ~/labs/week03/scripts/bench_run.sh -p kp:=238.0 -p ki:=2070.0 -p out:=imc
bash ~/labs/week03/scripts/bench_run.sh -p kp:=91.0 -p ki:=790.0 -p out:=gentle
bash ~/labs/week03/scripts/bench_run.sh -p kp:=148.0 -p ki:=0.0 -p out:=p_only
```

```text
# wind-up: no load step (LOAD=0.0), 0.9 m/s then 0.3 m/s at t = 4 s
LOAD=0.0 bash ~/labs/week03/scripts/bench_run.sh -p setpoint:=0.9 \
    -p setpoint2:=0.3 -p t_step2:=4.0 -p duration:=8.0 \
    -p anti_windup:=false -p out:=aw_off       # then true, out:=aw_on
```

```text
kp=148 ki=1290 kd=0 anti_windup=True: 1202 samples, 100 Hz -> simc.csv
step 0 -> 0.30 m/s at t = 1.00 s
  overshoot          1.4 %
  2 % settling time  0.37 s
  steady-state error 0.00 %  (mean of the last 1 s before the load step)
  duty ripple        0.75 % rms in steady state
load step detected at t = 7.99 s
  max speed dip      0.0437 m/s (14.6 % of setpoint)
  recovery to 2 %    0.34 s
```

## 7.1 Set-up and conventions

```text
       front
   FL(+a,+b)   FR(+a,-b)          x (forward)
        +---------+               ^
        |         |               |
        |    o    |        y <----o   (z out of the page)
        |         |
        +---------+
   RL(-a,+b)   RR(-a,-b)
```

## 7.5 Step 4 – the inverse-kinematic Jacobian

```text
          1   |  1   -1   -(a+b) |   | v_x |
  u  =   ---  |  1   +1   +(a+b) | . | v_y |        =  J . xi
          r   |  1   +1   -(a+b) |   | w_z |
              |  1   -1   +(a+b) |
```

## 7.6 Step 5 – forward kinematics and the null space

```bash
# look at one encoder report
ros2 topic echo /wheel_speeds --once     # name: wheel_fl_joint ... velocity: [rad/s]

# drive forward slowly for 3 s, then STOP (publish zero)
timeout 3 ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.1}}"
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"

# the scripted check (needs about 1.2 m free ahead and to the left)
cd ~/labs/week03/results
python3 ~/labs/week03/scripts/kinematics_check.py
```

```text
R, L = 0.0375, 0.18        # nominal geometry (what the robot "believes")
J = np.array([[1, -1, -L], [1, 1, L], [1, 1, -L], [1, -1, L]]) / R
J_PINV = np.linalg.pinv(J)  # wheel speeds -> (vx, vy, wz)
pred = J @ np.array(cmd)                      # inverse kinematics
eps = (w @ np.array([1, 1, -1, -1])) / 4      # null-space residual
xi = w @ J_PINV.T                             # forward map, every report
```

```text
=== X (forward): vx=0.20 vy=0.00 wz=0.00, 151 wheel reports
  wheel       fl       fr       rl       rr   [rad/s]
  predicted    5.333    5.333    5.333    5.333
  measured     5.288    5.285    5.283    5.266
  ratio       0.9914   0.9910   0.9906   0.9875
  slip residual eps: mean +0.0045 sd 0.0651 rad/s
  wheels 0.9982 m, truth 1.0100 m: error -1.17 %, correction 1.0118
=== Y (left): ...  error -1.22 %, correction 1.0124
=== Z (one turn CCW): vx=0.00 vy=0.00 wz=0.50, 340 wheel reports
  predicted   -2.400    2.400   -2.400    2.400
  measured    -2.275    2.276   -2.669    2.656
  wheels 6.4786 rad, truth 6.3000 rad: error +2.83 %, correction 0.9724
```

## 9.2 Layout rules for this board

```text
"I have open-loop step responses from a simulated wheel motor.
CSV columns: t, duty, v_enc, v_true (duty in %, speeds in m/s, 100 Hz).
Steps: 0->30 %, 30->60 %, 60->0 %, three repeats.
1. Fit a first-order-plus-dead-time model to each step and report K, tau
   and the dead time with 95 % confidence intervals. numpy/scipy only.
2. Explain why K from 0->30 % differs from K from 30->60 %.
3. Give PI gains by SIMC for lambda = tau/2, in % per (m/s) and in
   % per (m/s) per s, and the predicted settling time.
4. My encoder quantum is 0.0096 m/s. How much duty ripple will your Kp
   produce, and is a 2 % settling band measurable at 0.3 m/s?"
```
