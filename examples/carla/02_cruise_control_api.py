#!/usr/bin/env python3
"""CARLA WITHOUT ROS 2 - step 2: your own controller drives the car (cruise control).

Start the simulator first:   carla-sim start --town Town04          (Town04 has long straight motorways)
Then run:                    python3 ~/labs/examples/carla/02_cruise_control_api.py [--target 50] [--seconds 40] [--show]

A PI controller sets throttle and brake to hold the target speed; the steering keeps the car in its lane by
following the road's waypoints (pure pursuit). Writes ~/cruise_api.csv (time, speed, throttle, brake) and prints
the settling result. --show opens a chase-camera window with the speed and the controller output.

Pipeline:   CARLA --speed--> your PI controller --throttle/brake/steer (VehicleControl)--> CARLA     (20 Hz, synchronous)
"""
import argparse
import math
import os

os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')   # no sound card in the container: keep pygame quiet
import queue

import carla
import numpy as np


def lane_steer(car, cmap, max_steer_rad):
    """Pure pursuit on the lane centre line: steer towards a point on the lane a little way ahead.
    The look-ahead grows with speed (5 m + 0.6 s of travel), otherwise the car weaves at motorway speed."""
    tf = car.get_transform()
    v = car.get_velocity()
    lookahead = 5.0 + 0.6 * math.hypot(v.x, v.y)
    yaw = math.radians(tf.rotation.yaw)
    # At a junction next() offers several branches; keep the one closest to the current heading (stay on the road
    # you are on - the first branch may be a tight exit ramp).
    options = cmap.get_waypoint(tf.location).next(lookahead)
    wp = min(options, key=lambda w: abs(math.remainder(math.radians(w.transform.rotation.yaw) - yaw, 2 * math.pi)))
    wp = wp.transform.location
    dx, dy = wp.x - tf.location.x, wp.y - tf.location.y
    lateral = -math.sin(yaw) * dx + math.cos(yaw) * dy           # how far left/right the target point is
    angle = math.atan(2.0 * 2.9 * lateral / (lookahead ** 2))     # 2.9 m wheelbase -> steering angle (rad)
    return max(-1.0, min(1.0, angle / max_steer_rad))            # CARLA wants -1..1 of the maximum angle


def middle_lane_spawn_points(cmap):
    """Spawn points in a MIDDLE lane (driving lanes on both sides): an outer lane can turn into an exit ramp."""
    def driving(w):
        return w is not None and w.lane_type == carla.LaneType.Driving
    out = []
    for sp in cmap.get_spawn_points():
        w = cmap.get_waypoint(sp.location)
        if driving(w.get_left_lane()) and driving(w.get_right_lane()) and not w.is_junction:
            out.append(sp)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', type=float, default=50.0, help='target speed in km/h')
    ap.add_argument('--seconds', type=float, default=40.0)
    ap.add_argument('--kp', type=float, default=0.15)
    ap.add_argument('--ki', type=float, default=0.02)
    ap.add_argument('--show', action='store_true', help='chase-camera window')
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
    for sp in middle_lane_spawn_points(cmap) + cmap.get_spawn_points():
        car = world.try_spawn_actor(bp, sp)
        if car:
            break
    max_steer = math.radians(car.get_physics_control().wheels[0].max_steer_angle)
    spectator = world.get_spectator()
    cam, frames, screen = None, queue.Queue(), None
    if a.show:
        import pygame
        cb = world.get_blueprint_library().find('sensor.camera.rgb')
        cb.set_attribute('image_size_x', '960')
        cb.set_attribute('image_size_y', '540')
        cam = world.spawn_actor(cb, carla.Transform(carla.Location(x=-6, z=3), carla.Rotation(pitch=-12)), attach_to=car)
        cam.listen(frames.put)
        pygame.init()
        screen = pygame.display.set_mode((960, 540))
        pygame.display.set_caption('CARLA cruise control (no ROS)')
        font = pygame.font.SysFont('monospace', 24)
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
            car.apply_control(carla.VehicleControl(throttle=throttle, brake=brake, steer=lane_steer(car, cmap, max_steer)))
            tf = car.get_transform()                                            # keep the spectator behind the car
            spectator.set_transform(carla.Transform(tf.transform(carla.Location(x=-8, z=4)),
                                                    carla.Rotation(pitch=-15, yaw=tf.rotation.yaw)))
            rows.append((i * s.fixed_delta_seconds, kmh, throttle, brake))
            if screen is not None:
                import pygame
                img = frames.get(timeout=10)
                rgb = np.frombuffer(img.raw_data, np.uint8).reshape(img.height, img.width, 4)[:, :, 2::-1]
                pygame.event.pump()
                screen.blit(pygame.surfarray.make_surface(rgb.swapaxes(0, 1)), (0, 0))
                for k, line in enumerate(('speed  %5.1f km/h  (target %.0f)' % (kmh, a.target),
                                          'throttle %.2f   brake %.2f' % (throttle, brake))):
                    screen.blit(font.render(line, True, (255, 255, 0)), (12, 10 + 28 * k))
                pygame.display.flip()
            if i % 40 == 0:
                print('t=%5.1f s  speed %5.1f km/h  throttle %.2f  brake %.2f' % rows[-1])
    finally:
        if cam is not None:
            cam.stop()
            cam.destroy()
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
