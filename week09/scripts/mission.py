#!/usr/bin/env python3
"""mission.py - a survey ("lawn-mower") flight with photographs, without ROS 2 (Week 9, YOUR ACTIVITY).

Three TODOs (search for TODO); the README explains each one.

Start the simulator first:   drone-sim start --world blocks        (or neighborhood, mountains - fly higher there)
                             The survey has NO obstacle avoidance: fly above the tallest obstacle (blocks: 40 m).
Then run:                    python3 ~/labs/week09/scripts/mission.py --alt 40 --length 100 --width 100

What it does
  1. plan      rows across a length x width rectangle north-east of the start; the row spacing follows from the
               down camera's footprint at the flight height and the overlap you ask for            (TODO 1)
  2. fly       MAVSDK (MAVLink -> PX4 autopilot): arm, take off, offboard position set-points,
               one waypoint after the other, each "reached" within --tol metres                   (TODO 2)
  3. photos    at every waypoint one picture from the down camera, through the AirSim API -> ~/survey/
  4. safety    if the mission takes longer than --max-time (the battery reserve) it stops and flies home (TODO 3)
  5. report    flight time, distance flown, photos taken, the worst miss of a waypoint

Pipelines:  this script --(MAVLink, UDP 14550)--> PX4 --> AirSim       (flying)
            this script --(AirSim API, TCP 41451)--> AirSim            (photographs, position check)
"""
import argparse
import asyncio
import math
import os
import time

import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
import airsim  # noqa: E402
import cv2  # noqa: E402
import numpy as np  # noqa: E402
from mavsdk import System  # noqa: E402
from mavsdk.offboard import OffboardError, PositionNedYaw  # noqa: E402

CAMERA_FOV_DEG = 90.0          # the 'down' camera in AirSim's settings: 640 x 480, 90 deg horizontal field of view


def plan(length, width, alt, overlap):
    """Waypoints (north, east) of a lawn-mower pattern over [0, length] x [0, width] metres."""
    # TODO 1: how wide is the strip of ground the down camera sees from `alt` metres (CAMERA_FOV_DEG wide)?
    #   And how far apart must the rows be so that neighbouring strips overlap by `overlap` (e.g. 0.2 = 20 %)?
    footprint = 10.0
    spacing = 10.0
    rows = max(1, math.ceil(width / spacing) + 1)
    pts = []
    for i in range(rows):
        e = min(i * spacing, width)
        ns = (0.0, length) if i % 2 == 0 else (length, 0.0)     # boustrophedon: every other row backwards
        pts += [(ns[0], e), (ns[1], e)]
    return pts, footprint, spacing


def photo(client, folder, n):
    img, = client.simGetImages([airsim.ImageRequest('down', airsim.ImageType.Scene, False, False)])
    bgr = np.frombuffer(img.image_data_uint8, np.uint8).reshape(img.height, img.width, -1)[:, :, :3]
    path = os.path.join(folder, 'wp%02d.png' % n)
    cv2.imwrite(path, bgr)
    return path


async def goto(drone, n, e, alt, tol, timeout=90.0):
    """Fly to (n, e) at alt; return how far away the drone was when it counted as there (or timed out)."""
    await drone.offboard.set_position_ned(PositionNedYaw(n, e, -alt, 0.0))
    t0 = time.monotonic()
    async for pv in drone.telemetry.position_velocity_ned():
        p = pv.position
        d = math.hypot(p.north_m - n, p.east_m - e)
        # TODO 2: when has the drone reached the waypoint? As given it "arrives" at once - so every photo is taken
        #   on the way. Use d (the horizontal distance to the waypoint), tol, and the timeout.
        if True:
            return d, (p.north_m, p.east_m)


async def run(a):
    pts, footprint, spacing = plan(a.length, a.width, a.alt, a.overlap)
    print('plan: footprint %.1f m, row spacing %.1f m, %d waypoints' % (footprint, spacing, len(pts)), flush=True)
    folder = os.path.expanduser('~/survey')
    os.makedirs(folder, exist_ok=True)
    client = airsim.MultirotorClient(ip='127.0.0.1', port=41451)
    client.confirmConnection()

    drone = System()
    await drone.connect(system_address=a.url)
    async for s in drone.core.connection_state():
        if s.is_connected:
            break
    t0 = time.monotonic()
    async for h in drone.telemetry.health():
        if (h.is_global_position_ok and h.is_home_position_ok) or h.is_armable or time.monotonic() - t0 > 90:
            break
    await drone.action.set_takeoff_altitude(a.alt)
    await drone.action.arm()
    await drone.action.takeoff()
    async for pos in drone.telemetry.position():
        if pos.relative_altitude_m > 0.9 * a.alt or time.monotonic() - t0 > 60:
            break
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -a.alt, 0.0))
    try:
        await drone.offboard.start()
    except OffboardError as e:
        print('offboard failed:', e._result.result)
        await drone.action.land()
        return

    start = time.monotonic()
    dist, last, worst, photos, aborted = 0.0, (0.0, 0.0), 0.0, 0, False
    for i, (n, e) in enumerate(pts, 1):
        # TODO 3: battery reserve - if the survey has taken longer than a.max_time seconds, stop and fly home.
        if False:
            print('time limit %.0f s reached - stopping the survey and flying home' % a.max_time, flush=True)
            aborted = True
            break
        miss, here = await goto(drone, n, e, a.alt, a.tol)
        dist += math.hypot(here[0] - last[0], here[1] - last[1])
        last = here
        worst = max(worst, miss)
        photo(client, folder, i)
        photos += 1
        print('waypoint %2d/%d  north %6.1f  east %6.1f  %s (%.2f m)  photo saved'
              % (i, len(pts), n, e, 'reached' if miss < a.tol else 'MISSED ', miss), flush=True)
    miss, here = await goto(drone, 0.0, 0.0, a.alt, a.tol)
    dist += math.hypot(here[0] - last[0], here[1] - last[1])
    await drone.offboard.stop()
    await drone.action.land()
    async for in_air in drone.telemetry.in_air():
        if not in_air:
            break
    print('RESULT %s: %.0f s, %.0f m flown, %d photos, worst waypoint miss %.2f m, landed'
          % ('ABORTED (time limit)' if aborted else 'complete', time.monotonic() - start, dist, photos, worst),
          flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--alt', type=float, default=40.0, help='flight height above the start [m]: above every obstacle!')
    ap.add_argument('--length', type=float, default=100.0, help='survey length, north [m]')
    ap.add_argument('--width', type=float, default=100.0, help='survey width, east [m]')
    ap.add_argument('--overlap', type=float, default=0.2, help='side overlap of neighbouring photo strips (0-1)')
    ap.add_argument('--tol', type=float, default=1.0, help='a waypoint counts as reached within this distance [m]')
    ap.add_argument('--max-time', type=float, default=300.0, help='battery reserve: stop the survey after [s]')
    ap.add_argument('--url', default='udpin://0.0.0.0:14550', help='MAVLink address of the autopilot')
    asyncio.run(run(ap.parse_args()))
