"""LiDAR sector probe: valid beams, dropout, and range statistics in a sector, then the noise of one beam over time.

For every scan it prints the number of beams in the sector, how many are valid (finite, not 0.0, inside
[range_min, range_max]), the dropout percentage, and the mean and spread of the PERPENDICULAR distance r*cos(angle)
(to a flat wall facing the sensor this removes the geometric spread of the off-axis beams).
After --scans scans it prints the temporal mean and standard deviation of the single beam nearest the sector centre:
that is the range noise of the instrument.

Angles: angle 0 = straight ahead of the lab robot (index 360 of 720), +90 = left; the sector may straddle +/-180.
Usage:
    python3 ~/labs/week08/scripts/scan_probe.py                       # forward sector, +/-3 deg, 30 scans
    python3 ~/labs/week08/scripts/scan_probe.py --centre 180 --half 5  # rear sector (wraps around +/-180 deg)
Expected output (range world, robot at x = 0, wall 6.93 m ahead of the LiDAR):
    beams  13  valid  13  dropout   0.0 %  perp mean 6.928 m  sd 0.0093 m
    CENTRE BEAM index 360 (0.0 deg): 30 scans  mean 6.9302 m  sd 0.0100 m  valid 30/30
"""
import argparse
import math

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

ap = argparse.ArgumentParser()
ap.add_argument('--centre', type=float, default=0.0, help='sector centre, degrees (0 = forward)')
ap.add_argument('--half', type=float, default=3.0, help='sector half-width, degrees')
ap.add_argument('--scans', type=int, default=30)
a = ap.parse_args()


def wrap_deg(x):
    """Wrap angles into [-180, 180): the only safe way to compare angles near the +/-180 deg seam."""
    return (np.asarray(x) + 180.0) % 360.0 - 180.0


def valid(r, s):
    """The three traps: inf/nan (not finite), 0.0 (invalid on many drivers), outside the declared window."""
    return np.isfinite(r) & (r > 0.0) & (r >= s.range_min) & (r <= s.range_max)


class ScanProbe(Node):
    def __init__(self):
        super().__init__('scan_probe', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.centre_hist = []
        self.create_subscription(LaserScan, '/scan', self.cb, qos_profile_sensor_data)

    def cb(self, s):
        r = np.asarray(s.ranges, dtype=np.float64)
        ang = np.degrees(s.angle_min + np.arange(r.size) * s.angle_increment)   # index -> angle
        if not self.centre_hist:                                               # first scan: the geometry
            print('N = %d beams, angle_min %.2f deg, increment %.3f deg, angle 0 at index %d, frame %s'
                  % (r.size, math.degrees(s.angle_min), math.degrees(s.angle_increment),
                     int(np.argmin(np.abs(ang))), s.header.frame_id))
        off = wrap_deg(ang - a.centre)                                         # offset from the sector centre
        sel = np.abs(off) <= a.half
        ok = sel & valid(r, s)
        perp = r[ok] * np.cos(np.radians(off[ok]))
        line = 'beams %3d  valid %3d  dropout %5.1f %%' % (sel.sum(), ok.sum(), 100 * (1 - ok.sum() / sel.sum()))
        if ok.sum() > 1:
            line += '  perp mean %.3f m  sd %.4f m' % (perp.mean(), perp.std(ddof=1))
        print(line, flush=True)
        self.ci = int(np.argmin(np.abs(off)))                                   # beam nearest the centre
        self.centre_hist.append(r[self.ci] if valid(r[self.ci:self.ci + 1], s)[0] else math.nan)
        self.centre_deg = ang[self.ci]


def main():
    rclpy.init()
    n = ScanProbe()
    while rclpy.ok() and len(n.centre_hist) < a.scans:
        rclpy.spin_once(n, timeout_sec=0.1)
    h = np.array(n.centre_hist)
    g = h[np.isfinite(h)]
    msg = 'CENTRE BEAM index %d (%.1f deg): %d scans' % (n.ci, n.centre_deg, h.size)
    if g.size > 1:
        msg += '  mean %.4f m  sd %.4f m' % (g.mean(), g.std(ddof=1))
    print(msg + '  valid %d/%d' % (g.size, h.size))
    n.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
