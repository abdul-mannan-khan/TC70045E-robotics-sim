#!/usr/bin/env python3
"""SBUS (radio-control receiver protocol): pack and unpack 16 x 11-bit channels, flags, and the line-level bits.

Purpose  Week 2, Laboratory C. Write sbus_channels() yourself first; then run this file to check yours.
Usage    python3 ~/labs/week02/scripts/sbus_decode.py
Frame    0x0F | 22 bytes = 16 channels x 11 bits, LSB first | flags | 0x00   (25 bytes)
         flags: bit0 ch17, bit1 ch18, bit2 frame lost, bit3 failsafe
Line     100 000 baud, 8 data bits + EVEN parity + 2 stop bits = 12 bit times per byte, logic INVERTED
Output   1) the all-zero test, 2) a known frame decoded, 3) a 1000-frame random round-trip test,
         4) the first byte as it appears on the wire (inverted 8E2), 5) frame time and worst-case latency.
"""
import random


def sbus_channels(frame):
    """25-byte SBUS frame -> list of 16 channel values (0...2047) and the flags byte."""
    assert len(frame) == 25 and frame[0] == 0x0F and frame[24] == 0x00
    bits, nbits, ch = 0, 0, []
    for b in frame[1:23]:
        bits |= b << nbits                      # LSB first: new byte goes ABOVE the bits we still hold
        nbits += 8
        while nbits >= 11:
            ch.append(bits & 0x7FF)
            bits >>= 11
            nbits -= 11
    return ch, frame[23]


def sbus_frame(ch, flags=0):
    """16 channel values -> 25-byte frame (the inverse of sbus_channels)."""
    acc = 0
    for i, v in enumerate(ch):
        acc |= (v & 0x7FF) << (11 * i)
    return bytes([0x0F]) + acc.to_bytes(22, 'little') + bytes([flags, 0x00])


def line_bits(byte, inverted=True):
    """One byte as transmitted: start, 8 data bits LSB first, even parity, 2 stop bits (idle = 1)."""
    data = [(byte >> i) & 1 for i in range(8)]
    bits = [0] + data + [sum(data) % 2] + [1, 1]
    return [1 - b for b in bits] if inverted else bits


def main():
    print('1) all-zero frame  ->', sbus_channels(bytes([0x0F] + [0] * 22 + [0, 0]))[0])
    known = [172, 992, 1811, 992] + [992] * 12             # typical stick values: min, centre, max, centre
    ch, flags = sbus_channels(sbus_frame(known, flags=0x08))
    print('2) known frame     ->', ch[:6], '...  flags 0x%02X: failsafe=%d frame_lost=%d'
          % (flags, flags >> 3 & 1, flags >> 2 & 1))
    ok = all(sbus_channels(sbus_frame(c))[0] == c
             for c in ([random.randrange(2048) for _ in range(16)] for _ in range(1000)))
    print('3) 1000 random frames round-trip:', 'PASS' if ok else 'FAIL')
    print('4) header 0x0F on the wire (inverted 8E2, start..stop):', ''.join(map(str, line_bits(0x0F))))
    byte_t = 12 / 100000
    print('5) byte %.0f us, frame %.1f ms; with a 14 ms period worst-case latency = %.0f ms (7 ms mode: %.0f ms)'
          % (byte_t * 1e6, 25 * byte_t * 1e3, 14 + 25 * byte_t * 1e3, 7 + 25 * byte_t * 1e3))


if __name__ == '__main__':
    main()
