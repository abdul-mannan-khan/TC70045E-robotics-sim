#!/usr/bin/env python3
"""carla_view.py - a CARLA window for the demo videos (tutor tool, not a student activity).

The CARLA server has no window of its own. This viewer keeps one camera view of the world on screen the whole time:
it follows your car from above and behind when there is one (role_name 'hero' or 'ego_vehicle', else a Tesla
Model 3, else the newest vehicle) and otherwise looks down on the Town04 motorway.

It only watches: it never ticks the world and never changes its settings. In synchronous mode its picture moves
when the running script ticks; when nothing runs, it waits for the next frame. It reconnects if the server restarts.

    python3 ~/labs/tools/demo/carla_view.py [--width 955 --height 930]
"""
import argparse
import os
import queue
import time

os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import carla
import numpy as np
import pygame

HOME = carla.Transform(carla.Location(x=-330.0, y=33.6, z=60.0), carla.Rotation(pitch=-50.0, yaw=0.4))  # the 600 m straight


def pick_car(world):
    cars = list(world.get_actors().filter('vehicle.*'))
    if not cars:
        return None
    for role in ('hero', 'ego_vehicle'):
        for c in cars:
            if c.attributes.get('role_name') == role:
                return c
    tesla = [c for c in cars if c.type_id == 'vehicle.tesla.model3']
    return min(tesla, key=lambda c: c.id) if tesla else max(cars, key=lambda c: c.id)


def follow(car):
    """A view from above and behind the car, looking forward along its heading."""
    tf = car.get_transform()
    f = tf.get_forward_vector()
    loc = tf.location + carla.Location(x=-16.0 * f.x, y=-16.0 * f.y, z=14.0)
    return carla.Transform(loc, carla.Rotation(pitch=-35.0, yaw=tf.rotation.yaw))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--width', type=int, default=955)
    ap.add_argument('--height', type=int, default=930)
    a = ap.parse_args()
    pygame.init()
    screen = pygame.display.set_mode((a.width, a.height))
    pygame.display.set_caption('CARLA view (follows your car)')
    font = pygame.font.SysFont('monospace', 22)
    while True:
        cam = None
        try:
            client = carla.Client('127.0.0.1', 2000)
            client.set_timeout(10)
            world = client.get_world()
            bp = world.get_blueprint_library().find('sensor.camera.rgb')
            bp.set_attribute('image_size_x', str(a.width))
            bp.set_attribute('image_size_y', str(a.height))
            bp.set_attribute('fov', '90')
            cam = world.spawn_actor(bp, HOME)
            frames = queue.Queue(maxsize=2)

            def keep(img):
                if frames.full():
                    frames.get_nowait()
                frames.put_nowait(img)
            cam.listen(keep)
            t_world = time.monotonic()
            while True:
                if any(e.type == pygame.QUIT for e in pygame.event.get()):
                    return
                car = pick_car(world)
                cam.set_transform(follow(car) if car else HOME)
                try:
                    img = frames.get(timeout=0.2)
                except queue.Empty:
                    if time.monotonic() - t_world > 30:      # no frame for 30 s: check the server is still there
                        world.get_snapshot()
                        t_world = time.monotonic()
                    continue
                t_world = time.monotonic()
                rgb = np.frombuffer(img.raw_data, np.uint8).reshape(img.height, img.width, 4)[:, :, 2::-1]
                screen.blit(pygame.surfarray.make_surface(rgb.swapaxes(0, 1)), (0, 0))
                label = 'following %s' % car.type_id.split('.')[-1] if car else 'Town04 - no car yet'
                screen.blit(font.render(label, True, (255, 255, 0)), (10, a.height - 32))
                pygame.display.flip()
        except RuntimeError:                                      # server not up (yet) or restarting
            screen.fill((30, 41, 59))
            screen.blit(font.render('waiting for the CARLA server ...', True, (226, 232, 240)), (20, a.height // 2))
            pygame.display.flip()
            for _ in range(20):
                pygame.event.pump()
                time.sleep(0.1)
        finally:
            if cam is not None:
                try:
                    cam.stop()
                    cam.destroy()
                except RuntimeError:
                    pass


if __name__ == '__main__':
    main()
