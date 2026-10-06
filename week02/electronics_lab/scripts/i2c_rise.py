#!/usr/bin/env python3
"""I2C rise time against pull-up and bus capacitance, simulated in ngspice - and a bus-capacitance 'measurement'.

Purpose  Week 2, Laboratory A. Checks t_r = 0.8473 Rp Cb against a circuit simulation, shows which pull-up values
         meet standard mode (t_r <= 1000 ns) and fast mode (t_r <= 300 ns) and the 3 mA sink limit, and gives each
         student an unknown bus to measure: you get Rp and t_r, you infer Cb.
Usage    python3 ~/labs/week02/scripts/i2c_rise.py                        # sweep table
         python3 ~/labs/week02/scripts/i2c_rise.py --probe 10p            # same, with a 10 pF scope probe on SCL
         python3 ~/labs/week02/scripts/i2c_rise.py --mystery 21012345     # YOUR bus (use your student number)
         python3 ~/labs/week02/scripts/i2c_rise.py --mystery 21012345 --reveal   # after you have worked it out
Needs    ngspice and ~/labs/week02/spice/i2c_rise.cir.
"""
import argparse
import hashlib
import os
import re
import subprocess
import tempfile

NETLIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'spice', 'i2c_rise.cir')


def simulate(rp, cb, cprobe=0.0, vdd=3.3):
    text = open(NETLIST).read()
    text = re.sub(r'^\.param vdd=.*$', '.param vdd=%g rp=%g cb=%g cprobe=%g' % (vdd, rp, cb, cprobe),
                  text, count=1, flags=re.M)
    with tempfile.NamedTemporaryFile('w', suffix='.cir', delete=False) as f:
        f.write(text)
    out = subprocess.run(['ngspice', '-b', f.name], capture_output=True, text=True).stdout
    os.remove(f.name)
    r = {k: float(v) for k, v in re.findall(r'^(\w+)\s+=\s+([-+0-9.eE]+)', out, re.M)}
    return r['trise'], r['vlow']


def si(s):
    return float(s[:-1]) * {'p': 1e-12, 'n': 1e-9}[s[-1]] if s[-1] in 'pn' else float(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--probe', default='0', help='probe capacitance, e.g. 10p')
    ap.add_argument('--mystery', help='your student number: simulates a bus with a hidden capacitance')
    ap.add_argument('--reveal', action='store_true')
    a = ap.parse_args()
    cprobe = si(a.probe)
    if a.mystery:
        h = int(hashlib.sha256(a.mystery.encode()).hexdigest(), 16)
        rp = [2.2e3, 3.3e3, 4.7e3][h % 3]
        cb = (60 + (h // 3) % 261) * 1e-12                      # 60 ... 320 pF, fixed for your number
        tr, vlow = simulate(rp, cb, cprobe)
        print('bus %s: pull-up Rp = %.1f kohm, VDD = 3.3 V, probe %s F' % (a.mystery, rp / 1e3, a.probe))
        print('measured 30-70 %% rise time t_r = %.1f ns,  low level V_OL = %.1f mV' % (tr * 1e9, vlow * 1e3))
        print('-> now compute C_b = t_r / (0.8473 Rp) and the capacitance budget left under 400 pF')
        if a.reveal:
            print('REVEAL: C_b = %.0f pF (without the probe)' % (cb * 1e12))
        return
    print('probe capacitance: %s F' % a.probe)
    print('%7s %7s | %9s %9s | %7s %6s | %s' % ('Rp', 'Cb', 't_r hand', 't_r sim', 'I_sink', 'V_OL', 'verdict'))
    for rp in (1e3, 2.2e3, 4.7e3, 10e3):
        for cb in (50e-12, 100e-12, 200e-12, 400e-12):
            tr, vlow = simulate(rp, cb, cprobe)
            hand = 0.8473 * rp * cb
            isink = (3.3 - vlow) / rp
            verdict = ('fast mode OK' if tr <= 300e-9 else 'standard only' if tr <= 1000e-9 else 'TOO SLOW')
            if isink > 3e-3:
                verdict += ', sink > 3 mA!'
            print('%5.1fk %5.0fp | %7.0f ns %7.0f ns | %5.2f mA %4.0f mV | %s'
                  % (rp / 1e3, cb * 1e12, hand * 1e9, tr * 1e9, isink * 1e3, vlow * 1e3, verdict))


if __name__ == '__main__':
    main()
