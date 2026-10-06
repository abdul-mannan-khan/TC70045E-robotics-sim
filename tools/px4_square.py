#!/usr/bin/env python3
# px4_square.py - connect to PX4 SITL, take off, fly a 2 m square in offboard mode, land.
# MAVSDK-Python replaces MAVROS here: there is no ros-humble-mavros binary package.
import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, PositionNedYaw


async def run():
    drone = System()
    await drone.connect(system_address="udp://:14540")

    print("waiting for the vehicle...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("connected")
            break

    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("position estimate OK")
            break

    await drone.action.arm()
    await drone.action.takeoff()
    await asyncio.sleep(8)

    # PX4 refuses OFFBOARD unless setpoints are ALREADY streaming: send some first.
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -3.0, 0.0))
    try:
        await drone.offboard.start()
    except OffboardError as e:
        print("offboard start failed:", e._result.result)
        await drone.action.land()
        return

    for north, east in ((2.0, 0.0), (2.0, 2.0), (0.0, 2.0), (0.0, 0.0)):
        await drone.offboard.set_position_ned(PositionNedYaw(north, east, -3.0, 0.0))
        await asyncio.sleep(6)

    await drone.offboard.stop()
    await drone.action.land()

    async for position in drone.telemetry.position():
        print("alt %.2f m" % position.relative_altitude_m)
        if position.relative_altitude_m < 0.3:
            break


if __name__ == "__main__":
    asyncio.run(run())
