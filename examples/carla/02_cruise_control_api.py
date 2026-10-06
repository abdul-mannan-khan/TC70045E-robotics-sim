#!/usr/bin/env python3
"""CARLA WITHOUT ROS 2 - step 2: your own controller drives the car (cruise control).

Start the simulator first:   carla-sim start --town Town04          (Town04 has long straight motorways)
Then run:                    python3 ~/labs/examples/carla/02_cruise_control_api.py [--target 50] [--seconds 40]

A PI controller sets throttle and brake to hold the target speed; the steering keeps the car in its lane by
following the road's waypoints (pure pursuit). Writes ~/cruise_api.csv (time, speed, throttle, brake) and prints
the settling result.

Pipeline:   CARLA --speed--> your PI controller --throttle/brake/steer (VehicleControl)--> CARLA     (20 Hz, synchronous)
"""
import argparse
import math
import os

import carla


def lane_steer(car, cmap, lookahead=8.0):
    """Pure pursuit on the lane centre line: steer towards a waypoint 'lookahead' metres ahead."""
    tf = car.get_transform()
    wp = cmap.get_waypoint(tf.location).next(lookahead)[0].transform.location
    yaw = math.radians(tf.rotation.yaw)
    dx, dy = wp.x - tf.location.x, wp.y - tf.location.y
    lateral = -math.sin(yaw) * dx + math.cos(yaw) * dy           # how far left/right the target point is
    return max(-1.0, min(1.0, 2.0 * 2.9 * lateral / (lookahead ** 2)))   # 2.9 m wheelbase


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', type=float, default=50.0, help='target speed in km/h')
    ap.add_argument('--seconds', type=float, default=40.0)
    ap.add_argument('--kp', type=float, default=0.15)
    ap.add_argument('--ki', type=float, default=0.02)
    a = ap.parse_args()

    client = carla.Client('127.0.0.1', 2000)
    client.set_timeout(30)
    world = client.get_world()
    cmap = world.get_map()
    s = world.get_settings()
    s.synchronous_mode, s.fixed_delta_seconds = True, 0.05
    world.apply_settings(s)
    bp = world.get_blueprint_library().find('vehicle.tesla.model3')
    car = None
    for sp in cmap.get_spawn_points():
        car = world.try_spawn_actor(bp, sp)
        if car:
            break
    spectator = world.get_spectator()
    integral, rows = 0.0, []
    try:
        for i in range(int(a.seconds / s.fixed_delta_seconds)):
            world.tick()
            v = car.get_velocity()
            kmh = 3.6 * math.hypot(v.x, v.y)
            err = a.target - kmh
            integral = max(-50.0, min(50.0, integral + err * s.fixed_delta_seconds))   # anti-windup clamp
            u = a.kp * err + a.ki * integral
            throttle, brake = (min(u, 1.0), 0.0) if u >= 0 else (0.0, min(-u, 1.0))
            car.apply_control(carla.VehicleControl(throttle=throttle, brake=brake, steer=lane_steer(car, cmap)))
            tf = car.get_transform()                                            # keep the spectator behind the car
            spectator.set_transform(carla.Transform(tf.transform(carla.Location(x=-8, z=4)),
                                                    carla.Rotation(pitch=-15, yaw=tf.rotation.yaw)))
            rows.append((i * s.fixed_delta_seconds, kmh, throttle, brake))
            if i % 40 == 0:
                print('t=%5.1f s  speed %5.1f km/h  throttle %.2f  brake %.2f' % rows[-1])
    finally:
        car.destroy()
        s.synchronous_mode = False
        world.apply_settings(s)
    with open(os.path.expanduser('~/cruise_api.csv'), 'w') as f:
        f.write('t,speed_kmh,throttle,brake\n')
        f.writelines('%.2f,%.2f,%.3f,%.3f\n' % r for r in rows)
    tail = [r[1] for r in rows if r[0] > a.seconds - 10]
    print('RESULT last 10 s: mean %.1f km/h, max error %.1f km/h (target %.0f) - log ~/cruise_api.csv' %
          (sum(tail) / len(tail), max(abs(x - a.target) for x in tail), a.target))


if __name__ == '__main__':
    main()
