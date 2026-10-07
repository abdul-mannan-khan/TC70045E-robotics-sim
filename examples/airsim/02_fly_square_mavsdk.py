#!/usr/bin/env python3
"""AirSim WITHOUT ROS 2 - step 2: fly the drone through its autopilot (PX4) with MAVSDK.

Start the simulator first:   drone-sim start --world blocks          (SITL: PX4 runs in the container)
Then run:                    python3 ~/labs/examples/airsim/02_fly_square_mavsdk.py [--side 5] [--alt 5]

Arms, takes off, flies a square in offboard mode (position set-points), returns and lands.

Pipeline:   your script --(MAVLink, UDP 14550)--> PX4 autopilot --(HIL sensor/actuator messages)--> AirSim
            The autopilot is in charge of stability; your script only sends set-points. In HIL mode the same
            script talks to the real Pixhawk 6C instead (see docs/HIL_JETSON_PIXHAWK.md) - the code does not change.
"""
import argparse
import asyncio

import warnings
warnings.filterwarnings('ignore', category=FutureWarning)   # mavsdk<4 announces its rename to mavsdk-grpc
from mavsdk import System  # noqa: E402
from mavsdk.offboard import OffboardError, PositionNedYaw


async def run(side, alt, url):
    drone = System()
    await drone.connect(system_address=url)
    print('waiting for the autopilot on', url)
    async for s in drone.core.connection_state():
        if s.is_connected:
            break
    print('connected - waiting for a GPS/home position fix')
    t0 = asyncio.get_running_loop().time(); last = t0
    async for h in drone.telemetry.health():
        now = asyncio.get_running_loop().time()
        if (h.is_global_position_ok and h.is_home_position_ok) or h.is_armable or now - t0 > 90:
            break
        if now - last > 10:
            print('  still waiting: global position ok %s, home ok %s, armable %s'
                  % (h.is_global_position_ok, h.is_home_position_ok, h.is_armable))
            last = now

    await drone.action.set_takeoff_altitude(alt)
    await drone.action.arm()
    await drone.action.takeoff()
    print('taking off to %.1f m' % alt)
    t0 = asyncio.get_running_loop().time()            # PX4 often settles a little below the requested height,
    async for pos in drone.telemetry.position():      # so accept 90 % of it (or carry on after 40 s)
        if pos.relative_altitude_m > 0.9 * alt or asyncio.get_running_loop().time() - t0 > 40:
            break
    print('airborne at %.1f m' % pos.relative_altitude_m)

    # Offboard needs a set-point BEFORE it starts (otherwise OffboardError NO_SETPOINT_SET).
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -alt, 0.0))
    try:
        await drone.offboard.start()
    except OffboardError as e:
        print('offboard failed:', e._result.result)
        await drone.action.land()
        return
    corners = [(side, 0.0, 0.0), (side, side, 90.0), (0.0, side, 180.0), (0.0, 0.0, 270.0)]
    for n, e, yaw in corners:
        print('-> corner north %.1f m, east %.1f m' % (n, e))
        await drone.offboard.set_position_ned(PositionNedYaw(n, e, -alt, yaw))
        async for pv in drone.telemetry.position_velocity_ned():
            p = pv.position
            if abs(p.north_m - n) < 0.4 and abs(p.east_m - e) < 0.4:
                break
    await drone.offboard.stop()
    print('square done - landing')
    await drone.action.land()
    async for in_air in drone.telemetry.in_air():
        if not in_air:
            break
    print('landed')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--side', type=float, default=5.0, help='side of the square in metres')
    ap.add_argument('--alt', type=float, default=5.0, help='flight altitude in metres')
    ap.add_argument('--url', default='udpin://0.0.0.0:14550', help='MAVLink address of the autopilot')
    a = ap.parse_args()
    asyncio.run(run(a.side, a.alt, a.url))
