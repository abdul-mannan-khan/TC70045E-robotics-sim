import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, PositionNedYaw

async def run():
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    async for s in drone.core.connection_state():
        if s.is_connected: break
    async for h in drone.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok: break

    await drone.action.arm()
    await drone.action.takeoff()
    await asyncio.sleep(10)

    # PX4 refuses OFFBOARD unless setpoints are ALREADY streaming. This line is the lesson.
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -3.0, 0.0))
    try:
        await drone.offboard.start()
    except OffboardError as e:
        print("offboard start failed:", e._result.result)
        await drone.action.land(); return

    for north, east in ((2.0, 0.0), (2.0, 2.0), (0.0, 2.0), (0.0, 0.0)):
        await drone.offboard.set_position_ned(PositionNedYaw(north, east, -3.0, 0.0))
        await asyncio.sleep(6)

    async for p in drone.telemetry.position_velocity_ned():
        print("n=%.2f e=%.2f d=%.2f" % (p.position.north_m, p.position.east_m, p.position.down_m)); break

    await drone.offboard.stop()
    await drone.action.land()

asyncio.run(run())
