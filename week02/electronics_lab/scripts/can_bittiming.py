#!/usr/bin/env python3
"""CAN bit timing: every legal prescaler / time-quantum split for a clock and a bit rate, and the bus length it allows.

Purpose  Week 2, Laboratory C. Reproduces what a microcontroller configurator (e.g. STM32CubeMX for bxCAN) solves:
         bit time = (1 + TSEG1 + TSEG2) time quanta, t_q = BRP / f_clk, sample point = (1 + TSEG1) / N.
Usage    python3 ~/labs/week02/scripts/can_bittiming.py                          # 36 MHz, 1 Mbit/s, SP 87.5 %
         python3 ~/labs/week02/scripts/can_bittiming.py --clock 36e6 --bitrate 500e3 --sp 0.75
Output   one row per prescaler giving an integer number of quanta N (8...25): TSEG1, TSEG2, SJW, the achieved
         sample point, the register values (BRP-1, TS1-1, TS2-1), and the maximum bus length from
         2 L t_prop + 2 t_xcvr <= SP t_bit  with t_prop = 5 ns/m and t_xcvr = 175 ns (one transceiver, each way).
"""
import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clock', type=float, default=36e6, help='CAN peripheral clock (APB1 on an STM32F1)')
    ap.add_argument('--bitrate', type=float, default=1e6)
    ap.add_argument('--sp', type=float, default=0.875, help='target sample point (CiA recommends 87.5 %)')
    a = ap.parse_args()
    t_bit = 1.0 / a.bitrate
    print('clock %.1f MHz, bit rate %.0f kbit/s, t_bit = %.0f ns, target sample point %.1f %%'
          % (a.clock / 1e6, a.bitrate / 1e3, t_bit * 1e9, a.sp * 100))
    print('%4s %4s %7s %6s %6s %4s %7s | %-18s | %7s' % ('BRP', 'N', 't_q ns', 'TSEG1', 'TSEG2', 'SJW', 'SP %',
                                                       'registers', 'L max'))
    for brp in range(1, 1025):
        n = a.clock / (brp * a.bitrate)
        if abs(n - round(n)) > 1e-9 or not 8 <= round(n) <= 25:
            continue
        n = int(round(n))
        tseg1 = min(max(int(round(a.sp * n)) - 1, 1), 16)     # 1 + TSEG1 quanta before the sample point
        tseg2 = n - 1 - tseg1
        if not 1 <= tseg2 <= 8:
            continue
        sjw = min(4, tseg2)
        sp = (1 + tseg1) / n
        l_max = (sp * t_bit - 2 * 175e-9) / (2 * 5e-9)
        print('%4d %4d %7.1f %6d %6d %4d %7.1f | BRP=%d TS1=%d TS2=%d | %5.0f m'
              % (brp, n, brp / a.clock * 1e9, tseg1, tseg2, sjw, sp * 100, brp - 1, tseg1 - 1, tseg2 - 1, l_max))


if __name__ == '__main__':
    main()
