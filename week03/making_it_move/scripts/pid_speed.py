#!/usr/bin/env python3
"""Week 3, Lab B - a discrete PI(D) wheel-speed controller for the motor test bench, with logging and metrics.

Easiest: bash ~/labs/week03/making_it_move/scripts/bench_run.sh -p kp:=148.0 -p ki:=1290.0   (starts a fresh bench for you)
Or by hand - terminal 1 (the plant, with a load step 8 s after it starts - for the disturbance test):
    ros2 run tc70045e_sim motor_bench --ros-args -p load_mps:=0.1 -p load_step_s:=8.0
terminal 2, within 3 s (the controller, gains from your Lab A model):
    python3 ~/labs/week03/making_it_move/scripts/pid_speed.py --ros-args -p kp:=148.0 -p ki:=1290.0
Restart the bench before every run, so that the load step always comes at the same moment.

Parameters: kp [% per m/s], ki [% per m/s per s], kd [% s per m/s], setpoint [m/s], t_step [s],
            setpoint2 [m/s] and t_step2 [s] (optional second step, e.g. for the wind-up test),
            duration [s], u_max [%], anti_windup [true/false], d_filter_s [s], out [CSV name]
Control law, one update per motor/speed sample (100 Hz), positional form:
    e = r - y;  P = kp e;  I += ki e dt (frozen while the output is saturated in the same direction);
    D = -kd dy/dt (derivative of the MEASUREMENT, low-pass filtered);  u = clamp(P + I + D, -u_max, u_max)
Output: <out>.csv (t, r, y, u) and a summary: overshoot, 2 % settling time, steady-state error and,
if the load step happened, the speed dip and the recovery time.
"""
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class PidSpeed(Node):
    def __init__(self):
        super().__init__('pid_speed')
        p = lambda n, v: self.declare_parameter(n, v).value     # noqa: E731
        self.kp, self.ki, self.kd = p('kp', 148.0), p('ki', 1290.0), p('kd', 0.0)
        self.r_set, self.t_step, self.dur = p('setpoint', 0.3), p('t_step', 1.0), p('duration', 12.0)
        self.u_max, self.aw, self.tf = p('u_max', 100.0), p('anti_windup', True), p('d_filter_s', 0.02)
        self.r2, self.t_step2 = p('setpoint2', 0.0), p('t_step2', -1.0)   # optional second step
        self.out = p('out', 'pid_run')
        self.pub = self.create_publisher(Float32, 'motor/duty', 10)
        self.create_subscription(Float32, 'motor/speed', self.on_speed, 50)
        self.t0 = None
        self.i_term = self.d_term = 0.0
        self.y_prev = self.t_prev = None
        self.log = []

    def on_speed(self, msg):
        now = self.get_clock().now().nanoseconds * 1e-9
        self.t0 = now if self.t0 is None else self.t0
        t, y = now - self.t0, msg.data
        r = self.r_set if t >= self.t_step else 0.0
        r = self.r2 if 0.0 <= self.t_step2 <= t else r
        dt = 0.01 if self.t_prev is None else max(now - self.t_prev, 1e-4)
        e = r - y
        if self.y_prev is not None and self.kd > 0.0:            # filtered derivative on measurement
            a = dt / (self.tf + dt)
            self.d_term += a * (-self.kd * (y - self.y_prev) / dt - self.d_term)
        u_unsat = self.kp * e + self.i_term + self.ki * e * dt + self.d_term
        saturated = abs(u_unsat) > self.u_max and np.sign(u_unsat) == np.sign(e)
        if not (self.aw and saturated):                          # conditional integration
            self.i_term += self.ki * e * dt
        u = float(np.clip(self.kp * e + self.i_term + self.d_term, -self.u_max, self.u_max))
        self.pub.publish(Float32(data=u))
        self.log.append((t, r, y, u))
        self.y_prev, self.t_prev = y, now


def metrics(d, t_step, r):
    """Step and disturbance metrics from the log (t, r, y, u). y is smoothed over 5 samples (50 ms)
    because a single encoder sample is quantised in steps of 0.0096 m/s - larger than a 2 % band."""
    t, u = d[:, 0], d[:, 3]
    y = np.convolve(np.pad(d[:, 2], 2, mode='edge'), np.ones(5) / 5, mode='valid')
    band = 0.02 * r
    t_dist = None                                              # load step: a sudden 0.02 m/s drop
    for i in np.where(t > t_step + 1.5)[0]:
        base = y[(t > t[i] - 0.6) & (t < t[i] - 0.1)].mean()
        if y[i] < base - 0.02:
            j = i
            while j > 0 and y[j - 1] < base - 0.005:
                j -= 1
            t_dist = t[j]
            break
    t_end = t_dist if t_dist is not None else t[-1]
    step = (t >= t_step) & (t < t_end)
    ss = (t > t_end - 1.0) & (t < t_end)
    y_ss = y[ss].mean()
    out_band = np.where(step & (np.abs(y - r) > band))[0]
    t_settle = t[out_band[-1]] - t_step if len(out_band) else 0.0
    print('step 0 -> %.2f m/s at t = %.2f s' % (r, t_step))
    print('  overshoot          %.1f %%' % max(0.0, (y[step].max() - r) / r * 100))
    print('  2 %% settling time  %.2f s' % t_settle)
    print('  steady-state error %.2f %%  (mean of the last 1 s before the load step)' % ((r - y_ss) / r * 100))
    print('  duty ripple        %.2f %% rms in steady state' % u[ss].std())
    if t_dist is None:
        print('no load step seen (start the bench with -p load_mps:=0.1 -p load_step_s:=8.0)')
        return
    after = t >= t_dist
    out_band = np.where(after & (np.abs(y - r) > band))[0]
    print('load step detected at t = %.2f s' % t_dist)
    print('  max speed dip      %.4f m/s (%.1f %% of setpoint)' % (r - y[after].min(), (r - y[after].min()) / r * 100))
    if len(out_band) and out_band[-1] > len(t) - 10:
        print('  recovery to 2 %    never (is there integral action?)')
    else:
        print('  recovery to 2 %%    %.2f s' % (t[out_band[-1]] - t_dist if len(out_band) else 0.0))


def main():
    rclpy.init()
    node = PidSpeed()
    try:
        while rclpy.ok() and (node.t0 is None or node.log[-1][0] < node.dur):
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    node.pub.publish(Float32(data=0.0))                        # leave the motor stopped
    d = np.array(node.log)
    node.destroy_node()
    rclpy.try_shutdown()
    if len(d) < 50:
        raise SystemExit('no motor/speed data - is motor_bench running?')
    np.savetxt(node.out + '.csv', d, delimiter=',', fmt='%.5f', header='t,r,y,u', comments='')
    print('kp=%g ki=%g kd=%g anti_windup=%s: %d samples, %.0f Hz -> %s.csv'
          % (node.kp, node.ki, node.kd, node.aw, len(d), (len(d) - 1) / (d[-1, 0] - d[0, 0]), node.out))
    if node.t_step2 >= 0.0:
        d1 = d[d[:, 0] < node.t_step2]
        metrics(d1, node.t_step, node.r_set)
        t, y = d[:, 0], d[:, 2]
        out = np.where((t >= node.t_step2) & (np.abs(y - node.r2) > 0.02 * abs(node.r2) + 0.0096))[0]
        print('second step to %.2f m/s at t = %.2f s: inside 2 %% (+1 quantum) after %.2f s'
              % (node.r2, node.t_step2, t[out[-1]] - node.t_step2 if len(out) else 0.0))
    else:
        metrics(d, node.t_step, node.r_set)


if __name__ == '__main__':
    main()
