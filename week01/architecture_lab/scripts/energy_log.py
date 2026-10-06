#!/usr/bin/env python3
"""Log the lab robot's battery model and measure its endurance to the 9.6 V alarm (simulated evidence).

Purpose  Week 1, Laboratory B: compare YOUR predicted endurance with the simulator's battery model.
Usage    (1) simulator:          ros2 launch tc70045e_sim sim.launch.py gui:=false camera:=false
         (2) accelerated pack:   ros2 param set /battery time_scale 60.0
         (3) this logger:        python3 ~/labs/week01/scripts/energy_log.py --time-scale 60
         (4) duty cycle:         python3 ~/labs/week01/scripts/drive_pattern.py
         (--ns selects a battery node started in its own namespace, e.g. --ns /endurance.)
Output   a status line every 10 simulated seconds, ~/labs/week01/energy_log.csv, and on reaching the alarm voltage
         (or Ctrl-C) a summary: mean pack current and power, energy delivered, and endurance in 'battery time'
         (= simulated time x time_scale), with a projection from the mean current.
"""
import argparse
import os

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import BatteryState


class EnergyLog(Node):
    def __init__(self, a):
        super().__init__('energy_log', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.a, self.rows, self.done = a, [], False
        self.create_subscription(BatteryState, a.ns.rstrip('/') + '/battery', self.on_batt, 10)
        self.f = open(a.csv, 'w')
        self.f.write('t_sim_s,t_battery_h,voltage_V,current_A,power_W,soc\n')

    def on_batt(self, m):
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        if t == 0.0 or self.done:
            return
        i = -m.current                                        # BatteryState: negative = discharging
        self.rows.append((t, m.voltage, i, m.percentage))
        tb = (t - self.rows[0][0]) * self.a.time_scale / 3600.0
        self.f.write('%.2f,%.4f,%.3f,%.3f,%.2f,%.4f\n' % (t, tb, m.voltage, i, m.voltage * i, m.percentage))
        if len(self.rows) % 100 == 0:                         # 10 Hz -> every 10 s of simulated time
            self.get_logger().info('battery time %5.2f h   V %6.3f   I %5.2f A   P %5.1f W   SoC %5.1f %%'
                                   % (tb, m.voltage, i, m.voltage * i, 100 * m.percentage))
        if m.voltage < self.a.alarm:
            self.done = True
            raise SystemExit

    def summary(self):
        if len(self.rows) < 20:
            print('not enough data - is %s/battery being published?' % self.a.ns)
            return
        r = np.array(self.rows)
        tb = (r[:, 0] - r[0, 0]) * self.a.time_scale            # seconds of battery time
        i, p = r[:, 2], r[:, 1] * r[:, 2]
        q_ah = np.trapz(i, tb) / 3600.0
        e_wh = np.trapz(p, tb) / 3600.0
        print('\n--- energy summary (SIMULATED battery model, time_scale %g) ---' % self.a.time_scale)
        print('logged            %.1f s simulated = %.2f h battery time' % (r[-1, 0] - r[0, 0], tb[-1] / 3600))
        print('pack voltage      %.2f V -> %.2f V' % (r[0, 1], r[-1, 1]))
        print('state of charge   %.1f %% -> %.1f %%' % (100 * r[0, 3], 100 * r[-1, 3]))
        print('mean current      %.2f A   (min %.2f, max %.2f)' % (i.mean(), i.min(), i.max()))
        print('mean power        %.1f W' % p.mean())
        print('charge delivered  %.2f Ah   energy %.1f Wh' % (q_ah, e_wh))
        if self.done:
            print('ENDURANCE to the %.1f V alarm: %.2f h = %.0f min (from %.0f %% SoC)'
                  % (self.a.alarm, tb[-1] / 3600, tb[-1] / 60, 100 * r[0, 3]))
        else:
            soc_rate = (r[0, 3] - r[-1, 3]) / tb[-1]                # SoC per second of battery time
            print('alarm not reached; linear projection to 0 %% SoC: %.2f h more' % (r[-1, 3] / soc_rate / 3600))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ns', default='', help="namespace of the battery node, e.g. /endurance ('' = the launch one)")
    ap.add_argument('--time-scale', type=float, default=1.0, help='must equal the battery node time_scale')
    ap.add_argument('--alarm', type=float, default=9.6)
    ap.add_argument('--csv', default=os.path.expanduser('~/labs/week01/energy_log.csv'))
    a = ap.parse_args()
    rclpy.init()
    node = EnergyLog(a)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    node.f.close()
    node.summary()
    print('CSV written to', a.csv)
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
