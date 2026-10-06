import asyncio
from mavsdk import System

async def main():
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("connected"); break
    async for h in drone.telemetry.health():
        print("global position ok:", h.is_global_position_ok); break
    async for b in drone.telemetry.battery():
        print("battery %.2f V" % b.voltage_v); break

asyncio.run(main())
