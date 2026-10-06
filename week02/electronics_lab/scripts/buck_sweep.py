#!/usr/bin/env python3
"""Run the Week 2 buck converter in ngspice for several capacitor choices and compare with the hand calculation.

Purpose  Week 2, Laboratory A. Shows, with a circuit simulator instead of an oscilloscope, which term dominates
         the output ripple (capacitance, ESR or ESL) and how far the simple hand formula is from the circuit.
Usage    python3 ~/labs/week02/scripts/buck_sweep.py                    # the standard table
         python3 ~/labs/week02/scripts/buck_sweep.py esr=10m cval=47u   # one extra case of your own
Needs    ngspice (in the lab image) and ~/labs/week02/spice/buck.cir (the netlist; run it alone with ngspice -b).
Output   for every case: hand-calculated dI_L and dV (C term + ESR term), simulated dI_L, simulated ripple
         (pk-pk over the last 10 periods) and the simulated mean output voltage. Each case takes ~3 s.
"""
import os
import re
import subprocess
import sys
import tempfile

NETLIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'spice', 'buck.cir')
BASE = dict(vin='12', fsw='500k', duty='{5/12}', lval='22u', cval='100u', esr='30m', esl='0', rload='5')
CASES = [('baseline (electrolytic)', {}),
         ('double the capacitance', dict(cval='200u')),
         ('halve the ESR', dict(esr='15m')),
         ('ceramic, ESR 3 mOhm', dict(esr='3m')),
         ('ceramic + 5 nH ESL', dict(esr='3m', esl='5n')),
         ('fsw = 1 MHz', dict(fsw='1Meg', duty='{5/12}')),
         ('light load 0.1 A', dict(rload='50'))]
SI = {'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3, 'k': 1e3, 'meg': 1e6}


def num(s):
    m = re.fullmatch(r'([-+0-9.eE]+)([a-zA-Z]*)', s)
    return float(m.group(1)) * SI.get(m.group(2).lower(), 1.0)


def run(params):
    text = open(NETLIST).read()
    line = '.param ' + ' '.join('%s=%s' % kv for kv in params.items())
    text = re.sub(r'^\.param vin=.*$', line, text, count=1, flags=re.M)
    with tempfile.NamedTemporaryFile('w', suffix='.cir', delete=False) as f:
        f.write(text)
    out = subprocess.run(['ngspice', '-b', f.name], capture_output=True, text=True).stdout
    os.remove(f.name)
    return {k: float(v) for k, v in re.findall(r'^(\w+)\s+=\s+([-+0-9.eE]+)', out, re.M)}


def hand(p):
    vin, fsw, L, C, esr = num(p['vin']), num(p['fsw']), num(p['lval']), num(p['cval']), num(p['esr'])
    vout = 5.0
    di = vout * (1 - vout / vin) / (L * fsw)
    return di, di / (8 * fsw * C), di * esr


def main():
    cases = CASES
    if len(sys.argv) > 1:
        cases = [('your case: ' + ' '.join(sys.argv[1:]), dict(a.split('=', 1) for a in sys.argv[1:]))]
    print('%-26s %8s %8s %8s %8s | %8s %9s %8s' % ('case', 'dI hand', 'dV_C', 'dV_ESR', 'sum', 'dI sim',
                                                   'ripple', 'Vout'))
    print('%-26s %8s %8s %8s %8s | %8s %9s %8s' % ('', 'A', 'mV', 'mV', 'mV', 'A', 'mV sim', 'V'))
    for name, change in cases:
        p = dict(BASE, **change)
        di, dvc, dve = hand(p)
        r = run(p)
        print('%-26s %8.3f %8.2f %8.2f %8.2f | %8.3f %9.2f %8.3f' % (name, di, dvc * 1e3, dve * 1e3,
              (dvc + dve) * 1e3, r.get('iripple', float('nan')), r.get('vripple', float('nan')) * 1e3,
              r.get('vout_avg', float('nan'))))


if __name__ == '__main__':
    main()
