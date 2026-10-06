#!/usr/bin/env python3
"""CAN 2.0A at bit level: build real frames (CRC-15, bit stuffing), time them, and run bitwise arbitration.

Purpose  Week 2, Laboratory C. A software logic analyser for CAN: no transceiver, no bus, the exact bits.
Usage    python3 ~/labs/week02/scripts/can_frame.py                              # the default contest
         python3 ~/labs/week02/scripts/can_frame.py 0x123:1122 0x120:00 0x7FF:   # your own ID:DATA-hex list
         python3 ~/labs/week02/scripts/can_frame.py --bitrate 500000
Output   for each frame: stuffed length in bits, number of stuff bits, CRC-15, duration at the bit rate;
         then the arbitration: which node drops out at which identifier bit, and the winner (lowest ID wins,
         because dominant 0 overwrites recessive 1 on the wired-AND bus).
"""
import argparse


def crc15(bits):
    """CAN CRC-15, polynomial x^15+x^14+x^10+x^8+x^7+x^4+x^3+1 (0x4599), over SOF..end of data."""
    crc = 0
    for b in bits:
        nxt = b ^ ((crc >> 14) & 1)
        crc = (crc << 1) & 0x7FFF
        if nxt:
            crc ^= 0x4599
    return crc


def frame_bits(can_id, data):
    """Return (stuffed bit list, raw length before stuffing, number of stuff bits, crc)."""
    bits = [0]                                              # SOF, dominant
    bits += [(can_id >> (10 - i)) & 1 for i in range(11)]  # identifier, MSB first
    bits += [0, 0, 0]                                       # RTR (data frame), IDE (standard), r0
    bits += [(len(data) >> (3 - i)) & 1 for i in range(4)] # DLC
    for byte in data:
        bits += [(byte >> (7 - i)) & 1 for i in range(8)]
    crc = crc15(bits)
    bits += [(crc >> (14 - i)) & 1 for i in range(15)]
    stuffed, run, last = [], 0, None                       # after 5 equal bits insert the opposite bit
    for b in bits:
        stuffed.append(b)
        run = run + 1 if b == last else 1
        last = b
        if run == 5:
            stuffed.append(1 - b)
            last, run = 1 - b, 1
    tail = [1, 1, 1] + [1] * 7 + [1] * 3                  # CRC delim, ACK slot (sent recessive), ACK delim, EOF, IFS
    return stuffed + tail, len(bits) + len(tail), len(stuffed) - len(bits), crc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('frames', nargs='*', default=['0x1A0:0102030405060708', '0x123:FF00', '0x120:00', '0x7FF:'])
    ap.add_argument('--bitrate', type=float, default=1e6)
    a = ap.parse_args()
    nodes = []
    for f in a.frames:
        i, d = f.split(':')
        nodes.append((int(i, 16), bytes.fromhex(d)))
    print('%-6s %-18s %5s %6s %6s %8s' % ('ID', 'data', 'bits', 'stuff', 'CRC15', 'time'))
    streams = {}
    for can_id, data in nodes:
        s, raw, nst, crc = frame_bits(can_id, data)
        streams[can_id] = s
        print('0x%03X  %-18s %5d %6d 0x%04X %6.1f us' % (can_id, data.hex() or '-', len(s), nst, crc,
                                                        len(s) / a.bitrate * 1e6))
    print('\nArbitration (all nodes start at the same SOF; bus level = AND of the transmitted bits):')
    active = set(streams)
    for k in range(1, 16):                                 # bits after SOF: 11 ID bits, RTR (+ stuff bits)
        if len(active) == 1:
            break
        bus = min(streams[n][k] for n in active)
        lost = sorted(n for n in active if streams[n][k] != bus)
        for n in lost:
            print('  bit %2d after SOF: bus=%d, node 0x%03X sent %d -> loses arbitration, becomes a receiver'
                  % (k, bus, n, streams[n][k]))
        active -= set(lost)
    print('winner: 0x%03X  (it never noticed the contest - the frame was not corrupted)' % min(active))


if __name__ == '__main__':
    main()
