#!/usr/bin/env python3
"""inject_fault.py - make a sensor of the simulated autopilot fail, to test that preflight.py says NO-GO (Week 12, A3).

PX4 can simulate sensor failures for testing (it must be allowed first: parameter SYS_FAILURE_EN = 1).
Use it only in simulation - never on a drone that is going to fly.

Start the simulator first:   drone-sim start --world blocks
Then run:                    python3 ~/labs/week12/scripts/inject_fault.py --sensor gps --type off
Undo:                        python3 ~/labs/week12/scripts/inject_fault.py --sensor gps --type ok     (or restart the simulator)
"""
import argparse
import asyncio

import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
from mavsdk import System  # noqa: E402
from mavsdk.failure import FailureType, FailureUnit  # noqa: E402
from mavsdk.param import ParamError  # noqa: E402

SENSORS = {'gps': FailureUnit.SENSOR_GPS, 'gyro': FailureUnit.SENSOR_GYRO, 'accel': FailureUnit.SENSOR_ACCEL,
           'mag': FailureUnit.SENSOR_MAG, 'baro': FailureUnit.SENSOR_BARO, 'battery': FailureUnit.SYSTEM_BATTERY}
TYPES = {'ok': FailureType.OK, 'off': FailureType.OFF, 'stuck': FailureType.STUCK, 'garbage': FailureType.GARBAGE,
         'wrong': FailureType.WRONG}


async def run(a):
    drone = System()
    await drone.connect(system_address=a.url)
    async for s in drone.core.connection_state():
        if s.is_connected:
            break
    for attempt in range(1, 4):           # a busy simulator sometimes misses the first parameter request
        try:
            await drone.param.set_param_int('SYS_FAILURE_EN', 1)
            break
        except ParamError as e:
            print('setting SYS_FAILURE_EN failed (%s), attempt %d of 3' % (e._result.result, attempt), flush=True)
            await asyncio.sleep(2)
    else:
        raise SystemExit('could not enable failure injection - is PX4 running? (drone-sim status)')
    await drone.failure.inject(SENSORS[a.sensor], TYPES[a.type], 0)
    print('injected: %s %s (PX4 failure injection, simulation only)' % (a.sensor, a.type), flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--sensor', choices=sorted(SENSORS), default='gps')
    ap.add_argument('--type', choices=sorted(TYPES), default='off')
    ap.add_argument('--url', default='udpin://0.0.0.0:14550')
    asyncio.run(run(ap.parse_args()))
