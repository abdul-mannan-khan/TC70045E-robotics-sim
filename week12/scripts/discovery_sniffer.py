#!/usr/bin/env python3
"""discovery_sniffer.py - listen to DDS discovery (SPDP) multicast for one ROS domain (Week 12, Lab A).

RTPS participant discovery goes to multicast group 239.255.0.1, port PB + DG*d = 7400 + 250*d.
Every packet starts with 'RTPS', version, vendor id, and the 12-byte GUID prefix of the SENDING
participant - so counting distinct prefixes counts the DDS participants (roughly one per ROS 2 process).
No root rights and no tcpdump needed.
Usage:
  python3 ~/labs/week12/scripts/discovery_sniffer.py                 # your $ROS_DOMAIN_ID, 10 s
  python3 ~/labs/week12/scripts/discovery_sniffer.py --domain 0 --seconds 30
Prints packets/s, bytes/s and the number of participants heard.
"""
import argparse
import os
import socket
import struct
import time

VENDORS = {b'\x01\x0f': 'Fast DDS', b'\x01\x10': 'Cyclone DDS', b'\x01\x01': 'RTI Connext'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--domain', type=int, default=int(os.environ.get('ROS_DOMAIN_ID', 0)))
    ap.add_argument('--seconds', type=float, default=10.0)
    a = ap.parse_args()
    port = 7400 + 250 * a.domain
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', port))
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                 struct.pack('4sl', socket.inet_aton('239.255.0.1'), socket.INADDR_ANY))
    s.settimeout(0.5)
    print(f'domain {a.domain}: listening on 239.255.0.1:{port} for {a.seconds:.0f} s')
    n, nbytes, prefixes, vendors, t0 = 0, 0, set(), set(), time.time()
    while time.time() - t0 < a.seconds:
        try:
            data, _ = s.recvfrom(65535)
        except socket.timeout:
            continue
        if data[:4] != b'RTPS':
            continue
        n, nbytes = n + 1, nbytes + len(data)
        prefixes.add(data[8:20])
        vendors.add(VENDORS.get(data[6:8], data[6:8].hex()))
    dt = time.time() - t0
    print(f'{n} RTPS packets, {n / dt:.1f} packets/s, {nbytes / dt:.0f} B/s, '
          f'{len(prefixes)} participants heard ({", ".join(sorted(vendors)) or "none"})')


if __name__ == '__main__':
    main()
