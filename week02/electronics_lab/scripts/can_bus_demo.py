#!/usr/bin/env python3
"""Two CAN nodes on python-can's virtual bus: periodic traffic, an acceptance filter, and bus-load arithmetic.

Purpose  Week 2, Laboratory C. The software half of a CAN node: frame IDs as priorities, a receive filter
         (the thing that, left unconfigured on a microcontroller, silently discards every frame), and the bus load
         the same traffic would put on a real 1 Mbit/s bus. python-can's 'virtual' interface passes frames
         between Bus objects in one process; it does NOT model bit timing or arbitration (can_frame.py does).
Usage    python3 ~/labs/week02/scripts/can_bus_demo.py            # 2 s of traffic
Output   frames sent per ID, frames received by an unfiltered and by a filtered receiver, and the bus load.
"""
import time

import can

from can_frame import frame_bits                           # same folder: exact stuffed frame lengths

TRAFFIC = {0x080: ('emergency stop', 1, 10.0),            # ID: (meaning, data bytes, frames per second)
           0x101: ('wheel speeds', 8, 100.0),
           0x102: ('motor currents', 8, 100.0),
           0x300: ('battery status', 4, 1.0)}


def main():
    tx = can.Bus(interface='virtual', channel='lab', receive_own_messages=False)
    rx_all = can.Bus(interface='virtual', channel='lab')
    # accept only 0x100-0x10F: the drive node's IDs (match when (id & mask) == (can_id & mask))
    rx_drive = can.Bus(interface='virtual', channel='lab', can_filters=[{'can_id': 0x100, 'can_mask': 0x7F0}])
    sent = {i: 0 for i in TRAFFIC}
    t0 = time.monotonic()
    next_t = {i: t0 for i in TRAFFIC}
    while time.monotonic() - t0 < 2.0:
        now = time.monotonic()
        for i, (_, n, rate) in TRAFFIC.items():
            if now >= next_t[i]:
                tx.send(can.Message(arbitration_id=i, data=bytes(range(n)), is_extended_id=False))
                sent[i] += 1
                next_t[i] += 1.0 / rate
        time.sleep(0.0005)
    got_all, got_drive = {}, {}
    for bus, got in ((rx_all, got_all), (rx_drive, got_drive)):
        while (m := bus.recv(timeout=0.05)) is not None:
            got[m.arbitration_id] = got.get(m.arbitration_id, 0) + 1
    print('%-6s %-15s %5s %9s %14s %8s' % ('ID', 'meaning', 'sent', 'rx (all)', 'rx (filtered)', 'bits'))
    load = 0.0
    for i, (name, n, rate) in TRAFFIC.items():
        bits = len(frame_bits(i, bytes(range(n)))[0])
        load += bits * rate
        print('0x%03X  %-15s %5d %9d %14d %8d' % (i, name, sent[i], got_all.get(i, 0), got_drive.get(i, 0), bits))
    print('bus load at 1 Mbit/s: %.0f bit/s = %.2f %%   (at 125 kbit/s: %.1f %%)' % (load, load / 1e4, load / 1250))
    for b in (tx, rx_all, rx_drive):
        b.shutdown()


if __name__ == '__main__':
    main()
