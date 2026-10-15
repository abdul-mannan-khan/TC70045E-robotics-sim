#!/usr/bin/env python3
"""acc.py - adaptive cruise control with a radar: keep the speed, keep the gap, never hit the car ahead (Week 11, YOUR ACTIVITY).

Three TODOs (search for TODO); the README explains each one. As given it is a plain P speed controller that
ignores the car ahead - it will run into it when it slows down.

Start the simulator first:   carla-sim start --town Town04
Then run:                    python3 ~/labs/week11/scripts/acc.py [--target 50] [--show]

The scene (CARLA API, synchronous 20 Hz): your car ("ego", Tesla Model 3) and a lead car 40 m ahead in the same lane.
The lead car drives a fixed speed profile: 50 km/h, slows to 25 km/h at t = 25 s, back to 50 km/h at t = 45 s.
Your car carries a forward RADAR (sensor.other.radar: 30 deg x 10 deg, 100 m). Its detections give the gap
(distance to the nearest return in front) and the closing speed (relative radial velocity).

Your controller, every 50 ms:
  1. speed      PI controller on the speed error -> throttle / brake, with an anti-windup clamp      (TODO 1)
  2. gap        if the car ahead is closer than time_gap * own speed, lower the target speed so the gap
                opens again (a P controller on the gap error)                                         (TODO 2)
  3. safety     time-to-collision = gap / closing speed; below 1.5 s, or closer than 5 m: full brake,
                whatever 1 and 2 say                                                                  (TODO 3)
Steering keeps the lane (pure pursuit, given). At the end: speed error, smallest gap, smallest time gap and
smallest time-to-collision, and a CSV (~/acc.csv) for your plots.
"""
import argparse
import math
import os
import queue
import time

os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import carla  # noqa: E402
import numpy as np  # noqa: E402

DT = 0.05
MOUNT_Z = 0.7          # radar height above the road [m]


def lane_steer(car, cmap, max_steer_rad):
    """Pure pursuit on the lane centre line (as in the Week 11 example 02)."""
    tf = car.get_transform()
    v = car.get_velocity()
    lookahead = 5.0 + 0.6 * math.hypot(v.x, v.y)
    yaw = math.radians(tf.rotation.yaw)
    options = cmap.get_waypoint(tf.location).next(lookahead)
    wp = min(options, key=lambda w: abs(math.remainder(math.radians(w.transform.rotation.yaw) - yaw, 2 * math.pi)))
    wp = wp.transform.location
    dx, dy = wp.x - tf.location.x, wp.y - tf.location.y
    lateral = -math.sin(yaw) * dx + math.cos(yaw) * dy
    angle = math.atan(2.0 * 2.9 * lateral / (lookahead ** 2))
    return max(-1.0, min(1.0, angle / max_steer_rad))


def lead_profile(t):
    """Lead car target speed [km/h] against time [s]."""
    return 25.0 if 25.0 <= t < 45.0 else 50.0


class Radar:
    """Keeps the nearest return straight ahead (|azimuth| < 4 deg, above the road) from the newest radar frame."""
    def __init__(self, world, car, rng):
        bp = world.get_blueprint_library().find('sensor.other.radar')
        bp.set_attribute('horizontal_fov', '30')
        bp.set_attribute('vertical_fov', '10')
        bp.set_attribute('range', '100')
        bp.set_attribute('points_per_second', '4000')
        self.sensor = world.spawn_actor(bp, carla.Transform(carla.Location(x=2.3, z=MOUNT_Z)), attach_to=car)
        self.gap, self.closing = math.inf, 0.0
        self.sensor.listen(self.on_frame)
        self.rng = rng

    def on_frame(self, frame):
        best = (math.inf, 0.0)
        for d in frame:
            height = MOUNT_Z + d.depth * math.sin(d.altitude)  # height of the reflection above the road
            if abs(math.degrees(d.azimuth)) < 4.0 and height > 0.3 and d.depth < best[0]:   # not the road itself
                best = (d.depth, -d.velocity)              # velocity < 0 = coming closer -> closing > 0
        self.gap, self.closing = best

    def destroy(self):
        self.sensor.stop()
        self.sensor.destroy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', type=float, default=50.0, help='set speed [km/h]')
    ap.add_argument('--seconds', type=float, default=70.0)
    ap.add_argument('--kp', type=float, default=0.15)
    ap.add_argument('--ki', type=float, default=0.02)
    ap.add_argument('--time-gap', type=float, default=2.0, help='wanted time gap to the car ahead [s]')
    ap.add_argument('--show', action='store_true', help='chase-camera window')
    a = ap.parse_args()

    client = carla.Client('127.0.0.1', 2000)
    client.set_timeout(30)
    world = client.get_world()
    cmap = world.get_map()
    s = world.get_settings()
    s.synchronous_mode, s.fixed_delta_seconds = True, DT
    world.apply_settings(s)
    lib = world.get_blueprint_library()
    start = carla.Transform(carla.Location(x=-365.9, y=33.6, z=0.8), carla.Rotation(yaw=0.4))   # 600 m straight
    ego = world.spawn_actor(lib.find('vehicle.tesla.model3'), start)
    lead_wp = cmap.get_waypoint(start.location).next(40.0)[0]
    lead_tf = lead_wp.transform
    lead_tf.location.z += 0.5
    lead = world.spawn_actor(lib.find('vehicle.audi.a2'), lead_tf)
    world.tick()
    max_steer = math.radians(ego.get_physics_control().wheels[0].max_steer_angle)
    radar = Radar(world, ego, np.random.default_rng(1))
    spectator = world.get_spectator()
    cam, frames, screen = None, queue.Queue(), None
    if a.show:
        import pygame
        cb = lib.find('sensor.camera.rgb')
        cb.set_attribute('image_size_x', '960')
        cb.set_attribute('image_size_y', '540')
        cam = world.spawn_actor(cb, carla.Transform(carla.Location(x=-6, z=3), carla.Rotation(pitch=-12)), attach_to=ego)
        cam.listen(frames.put)
        pygame.init()
        screen = pygame.display.set_mode((960, 540))
        pygame.display.set_caption('CARLA adaptive cruise control (radar)')
        font = pygame.font.SysFont('monospace', 22)

    integral, lead_int, rows = 0.0, 0.0, []
    try:
        t_start = time.monotonic()
        for i in range(int(a.seconds / DT)):
            world.tick()
            if screen is not None:   # a window to watch: run no faster than real time
                time.sleep(max(0.0, t_start + (i + 1) * DT - time.monotonic()))
            t = i * DT
            # --- the lead car: its own little cruise control on a speed profile (given) ---
            lv = lead.get_velocity()
            lkmh = 3.6 * math.hypot(lv.x, lv.y)
            le = lead_profile(t) - lkmh
            lead_int = max(-50.0, min(50.0, lead_int + le * DT))
            lu = 0.15 * le + 0.02 * lead_int
            lead.apply_control(carla.VehicleControl(throttle=max(0.0, min(lu, 1.0)), brake=max(0.0, min(-lu, 1.0)),
                                                    steer=lane_steer(lead, cmap, max_steer)))
            # --- your car ---
            v = ego.get_velocity()
            kmh = 3.6 * math.hypot(v.x, v.y)
            gap, closing = radar.gap, radar.closing
            target = a.target
            # TODO 2: keep a safe gap. The wanted gap is time_gap x own speed (m/s) + 5 m standing distance. When the car
            #   ahead is closer than that (plus a margin), lower `target` below the set speed - e.g. own speed plus a
            #   gain times (gap - wanted) - so the gap opens again. As given the gap is ignored.
            # TODO 1: a P controller leaves a steady speed error. Add the I term: integral += err * DT, clamped to
            #   [-50, 50] (anti-windup), and u = kp * err + ki * integral.
            err = target - kmh
            u = a.kp * err
            throttle, brake = (min(u, 1.0), 0.0) if u >= 0 else (0.0, min(-u, 1.0))
            ttc = gap / closing if closing > 0.1 else math.inf
            # TODO 3: safety. If the time to collision (ttc, computed above) is below 1.5 s, OR the radar gap is below the
            #   5 m standstill distance: full brake (throttle 0, brake 1) whatever TODO 1 and 2 say - and reset the
            #   integral. (Why the gap too? Close behind a car at the same speed the TTC is 'infinite'.)
            ego.apply_control(carla.VehicleControl(throttle=throttle, brake=brake, steer=lane_steer(ego, cmap, max_steer)))
            true_gap = ego.get_location().distance(lead.get_location()) - 4.5          # minus about one car length
            tf = ego.get_transform()
            spectator.set_transform(carla.Transform(tf.transform(carla.Location(x=-10, z=5)),
                                                    carla.Rotation(pitch=-15, yaw=tf.rotation.yaw)))
            rows.append((t, kmh, lkmh, target, gap if gap < math.inf else -1, true_gap, ttc if ttc < 99 else 99,
                         throttle, brake))
            if screen is not None:
                import pygame
                img = frames.get(timeout=10)
                rgb = np.frombuffer(img.raw_data, np.uint8).reshape(img.height, img.width, 4)[:, :, 2::-1]
                pygame.event.pump()
                screen.blit(pygame.surfarray.make_surface(rgb.swapaxes(0, 1)), (0, 0))
                for k, line in enumerate(('speed %5.1f km/h  set %4.0f  lead %5.1f' % (kmh, a.target, lkmh),
                                          'radar gap %5.1f m  TTC %5.1f s' % (gap, min(ttc, 99)),
                                          'throttle %.2f  brake %.2f' % (throttle, brake))):
                    screen.blit(font.render(line, True, (255, 255, 0)), (12, 10 + 26 * k))
                pygame.display.flip()
            if i % 40 == 0:
                print('t=%5.1f s  speed %5.1f  lead %5.1f km/h  radar gap %5.1f m  TTC %5.1f s  thr %.2f brk %.2f'
                      % (t, kmh, lkmh, gap, min(ttc, 99), throttle, brake), flush=True)
    finally:
        radar.destroy()
        if cam is not None:
            cam.stop()
            cam.destroy()
        ego.destroy()
        lead.destroy()
        s.synchronous_mode = False
        world.apply_settings(s)
    with open(os.path.expanduser('~/acc.csv'), 'w') as f:
        f.write('t,speed_kmh,lead_kmh,target_kmh,radar_gap_m,true_gap_m,ttc_s,throttle,brake\n')
        f.writelines(','.join('%.3f' % x for x in r) + '\n' for r in rows)
    r = np.array(rows)
    moving = r[:, 1] > 5
    tgap = r[moving, 5] / (r[moving, 1] / 3.6)
    early = r[(r[:, 0] > 15) & (r[:, 0] < 25)]
    print('RESULT smallest true gap %.1f m, smallest time gap %.2f s, smallest radar TTC %.1f s, '
          'speed before the slow-down %.1f km/h (lead 50) - log ~/acc.csv'
          % (r[:, 5].min(), tgap.min(), r[:, 6].min(), early[:, 1].mean()), flush=True)


if __name__ == '__main__':
    main()
