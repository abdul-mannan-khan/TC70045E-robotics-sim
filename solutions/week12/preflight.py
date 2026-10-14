#!/usr/bin/env python3
"""preflight.py - a go / no-go check before the survey mission flies (Week 12, SOLUTION).

The same script checks the simulated autopilot (SITL, in the drone container) and the real Pixhawk 6C (HIL, from the
Jetson): only the MAVLink address changes.

Start the simulator first:   drone-sim start --world blocks
Then run:                    python3 ~/labs/week12/scripts/preflight.py --alt 20 --length 60 --width 60
On the Jetson (HIL):         python3 preflight.py --url serial:///dev/ttyTHS0:921600 ...

What it checks (for --seconds, default 10 s of telemetry)
  1. link       position messages arrive often enough (at least --min-rate per second)            (TODO 3)
  2. sensors    the autopilot's own health flags: gyro, accelerometer, magnetometer, local/global position, home
  3. GPS        a 3D fix (or better) and at least --min-sats satellites                            (TODO 1)
  4. battery    enough charge for the planned survey plus a reserve                                  (TODO 2)
Then one line per check (PASS / FAIL and the measured value) and a verdict: GO (exit code 0) or NO-GO (exit code 1),
so a shell can run   python3 preflight.py ... && python3 ~/labs/week09/scripts/mission.py ...
"""
import argparse
import asyncio
import math
import os
import sys
import time

import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
from mavsdk import System  # noqa: E402
from mavsdk.telemetry import FixType  # noqa: E402

CAMERA_FOV_DEG = 90.0
SPEED = 5.0                 # m/s, roughly what the survey flies between waypoints
USE_PER_MIN = 2.5           # % of battery per minute of flight (measure it for your drone: SITL drains slowly)


def survey_minutes(length, width, alt, overlap):
    """Flight time of the Week 9 lawn-mower survey, estimated from its length and SPEED (plus take-off and landing)."""
    footprint = 2.0 * alt * math.tan(math.radians(CAMERA_FOV_DEG / 2.0))
    spacing = footprint * (1.0 - overlap)
    rows = max(1, math.ceil(width / spacing) + 1)
    dist = rows * length + width + math.hypot(length, width)          # rows + steps between them + the way home
    return (dist / SPEED + 2 * alt / 2.0 + 30.0) / 60.0                # + climb and descent at 2 m/s + 30 s margin


async def collect(drone, seconds):
    """Listen for `seconds` and keep the newest health, GPS and battery message and the number of position messages."""
    seen = {'health': None, 'gps': None, 'battery': None, 'positions': 0}

    async def keep(stream, key):
        async for msg in stream:
            seen[key] = msg

    async def count():
        async for _ in drone.telemetry.position():
            seen['positions'] += 1

    tasks = [asyncio.ensure_future(c) for c in (keep(drone.telemetry.health(), 'health'),
                                                keep(drone.telemetry.gps_info(), 'gps'),
                                                keep(drone.telemetry.battery(), 'battery'), count())]
    await asyncio.sleep(seconds)
    for t in tasks:
        t.cancel()
    return seen


async def run(a):
    drone = System()
    await drone.connect(system_address=a.url)
    print('waiting for the autopilot on', a.url, flush=True)
    t0 = time.monotonic()
    async for s in drone.core.connection_state():
        if s.is_connected:
            break
        if time.monotonic() - t0 > 60:
            print('NO-GO: no autopilot found')
            return False, drone
    await asyncio.sleep(2.0)                                          # let the telemetry streams start
    seen = await collect(drone, a.seconds)
    checks = []

    # 1 link - SOLUTION TODO 3: position messages per second, against --min-rate
    rate = seen['positions'] / a.seconds
    checks.append(('link: position messages', rate >= a.min_rate, '%.1f per s (need %.0f)' % (rate, a.min_rate)))

    # 2 sensors - the autopilot's own health flags (given)
    h = seen['health']
    flags = ['is_gyrometer_calibration_ok', 'is_accelerometer_calibration_ok', 'is_magnetometer_calibration_ok',
             'is_local_position_ok', 'is_global_position_ok', 'is_home_position_ok']
    bad = [f[3:-3] for f in flags if h is None or not getattr(h, f)]
    checks.append(('sensors: autopilot health', not bad, 'all ok' if not bad else 'not ok: ' + ', '.join(bad)))

    # 3 GPS - SOLUTION TODO 1: a 3D fix or better, and enough satellites
    g = seen['gps']
    good_fix = g is not None and g.fix_type in (FixType.FIX_3D, FixType.FIX_DGPS, FixType.RTK_FLOAT, FixType.RTK_FIXED)
    sats = g.num_satellites if g is not None else 0
    checks.append(('GPS: fix and satellites', good_fix and sats >= a.min_sats,
                   '%s, %d satellites (need 3D fix, %d)' % (g.fix_type if g else 'no data', sats, a.min_sats)))

    # 4 battery - SOLUTION TODO 2: enough for the survey plus the reserve
    b = seen['battery']
    need = survey_minutes(a.length, a.width, a.alt, a.overlap) * USE_PER_MIN + a.reserve
    have = b.remaining_percent if b is not None else 0.0
    have = have * 100.0 if have <= 1.0 else have                      # older MAVSDK versions report 0-1
    checks.append(('battery: survey + reserve', have >= need,
                   '%.0f %% (need %.0f %%: %.1f min survey + %.0f %% reserve)'
                   % (have, need, survey_minutes(a.length, a.width, a.alt, a.overlap), a.reserve)))

    for name, ok, value in checks:
        print('%-28s %s   %s' % (name, 'PASS' if ok else 'FAIL', value), flush=True)
    go = all(ok for _, ok, _ in checks)
    print('VERDICT %s' % ('GO' if go else 'NO-GO'), flush=True)
    return go, drone


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default='udpin://0.0.0.0:14550', help='MAVLink address of the autopilot')
    ap.add_argument('--seconds', type=float, default=10.0, help='how long to listen')
    ap.add_argument('--alt', type=float, default=20.0)
    ap.add_argument('--length', type=float, default=60.0)
    ap.add_argument('--width', type=float, default=60.0)
    ap.add_argument('--overlap', type=float, default=0.2)
    ap.add_argument('--min-rate', type=float, default=5.0, help='position messages per second')
    ap.add_argument('--min-sats', type=int, default=8)
    ap.add_argument('--reserve', type=float, default=30.0, help='battery %% left on landing')
    go, drone = asyncio.new_event_loop().run_until_complete(run(ap.parse_args()))
    # exit at once: after a NO-GO some telemetry streams never send again, and a normal exit waits for them for ever
    stop = getattr(drone, '_stop_mavsdk_server', None)
    if stop:
        stop()
    sys.stdout.flush()
    os._exit(0 if go else 1)
