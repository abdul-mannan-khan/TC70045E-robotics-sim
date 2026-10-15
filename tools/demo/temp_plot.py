"""Live plot of the Week 1 control loop for the demo video (tutor tool): room temperature and fan speed over the last
3 minutes, with the setpoint(s) as dashed lines.
Usage    python3 ~/labs/tools/demo/temp_plot.py 26 24      (the setpoints to draw)
"""
import sys
import threading
import time

import matplotlib.pyplot as plt
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature
from std_msgs.msg import Float32

WINDOW_S = 180.0
for _k in [k for k in plt.rcParams if k.startswith('keymap.')]:
    plt.rcParams[_k] = []          # no keyboard shortcuts: the demo types into other windows


class Recorder(Node):
    def __init__(self):
        super().__init__('temp_plot')
        self.t0 = time.time()
        self.temp, self.fan = [], []
        self.create_subscription(Temperature, '/room/temperature',
                                 lambda m: self.temp.append((time.time() - self.t0, m.temperature)), 10)
        self.create_subscription(Float32, '/fan/speed',
                                 lambda m: self.fan.append((time.time() - self.t0, m.data)), 10)


def main():
    setpoints = [float(a) for a in sys.argv[1:]] or [26.0]
    rclpy.init()
    node = Recorder()
    threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

    fig, (ax_t, ax_f) = plt.subplots(2, 1, sharex=True, figsize=(9.5, 9.5),
                                     gridspec_kw={'height_ratios': [2, 1]})
    fig.canvas.manager.set_window_title('Temperature plot')
    line_t, = ax_t.plot([], [], color='tab:red', lw=2, label='room temperature (sensor)')
    for sp in setpoints:
        ax_t.axhline(sp, color='k', ls='--', lw=1.2, label='setpoint %.0f C' % sp)
    line_f, = ax_f.plot([], [], color='tab:blue', lw=2, label='fan speed (actuator)')
    ax_t.set_ylabel('temperature, C', fontsize=13)
    ax_t.set_ylim(22, 34)
    ax_f.set_ylabel('fan speed, %', fontsize=13)
    ax_f.set_ylim(-5, 105)
    ax_f.set_xlabel('time, s', fontsize=13)
    for ax in (ax_t, ax_f):
        ax.grid(alpha=0.3)
        ax.legend(loc='upper left', fontsize=11)
    fig.tight_layout()
    plt.show(block=False)

    while plt.fignum_exists(fig.number):
        now = time.time() - node.t0
        for line, data in ((line_t, node.temp), (line_f, node.fan)):
            if data:
                xs, ys = zip(*data[-2000:])
                line.set_data(xs, ys)
        ax_f.set_xlim(max(0.0, now - WINDOW_S), max(WINDOW_S, now))
        fig.canvas.draw_idle()
        fig.canvas.flush_events()  # unlike plt.pause(), this does not raise the window or take the keyboard focus
        time.sleep(0.5)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
