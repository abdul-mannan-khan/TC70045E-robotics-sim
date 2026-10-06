#!/usr/bin/env python3
# 1) measure the telemetry rate a MAVLink bridge really delivers
# 2) reproduce the deliberate failure the Week 12 lab asks for: offboard.start() with no setpoint streaming
import asyncio, time
from mavsdk import System
from mavsdk.offboard import OffboardError, PositionNedYaw


async def connect():
    d = System()
    await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected:
            break
    return d


async def rate(d, stream, name, n=100):
    t0 = time.time()
    i = 0
    async for _ in stream:
        i += 1
        if i >= n:
            break
    dt = time.time() - t0
    print("RATE|%s|%.1f Hz (%d samples in %.1f s)" % (name, i / dt, i, dt), flush=True)


async def main():
    d = await connect()
    print("CONNECTED", flush=True)
    await rate(d, d.telemetry.imu(), "telemetry.imu")
    await rate(d, d.telemetry.position_velocity_ned(), "telemetry.position_velocity_ned", 50)
    async for b in d.telemetry.battery():
        print("BATTERY|%.2f V" % b.voltage_v, flush=True)
        break
    async for h in d.telemetry.health():
        print("HEALTH|global_pos_ok=%s home_pos_ok=%s" % (h.is_global_position_ok, h.is_home_position_ok), flush=True)
        break

    print("--- deliberate failure: offboard.start() with no setpoint streamed first", flush=True)
    try:
        await d.action.arm()
        await d.offboard.start()
        print("OFFBOARD_NO_SETPOINT|unexpectedly succeeded", flush=True)
    except OffboardError as e:
        print("OFFBOARD_NO_SETPOINT|OffboardError result = %s" % e._result.result, flush=True)
    except Exception as e:
        print("OFFBOARD_NO_SETPOINT|%s: %s" % (type(e).__name__, e), flush=True)
    try:
        await d.action.disarm()
    except Exception:
        pass


asyncio.run(main())
