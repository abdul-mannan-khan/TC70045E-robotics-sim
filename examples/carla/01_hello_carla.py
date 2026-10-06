#!/usr/bin/env python3
"""CARLA WITHOUT ROS 2 - step 1: a car, a camera and a window, through the CARLA Python API.

Start the simulator first:   carla-sim start --town Town03
Then run:                    python3 ~/labs/examples/carla/01_hello_carla.py [--seconds 60] [--headless]

Spawns a car with a chase camera, lets CARLA's autopilot drive it, and shows the camera in a pygame window
together with the speed. --headless saves ~/carla_chase.png instead of opening a window.

Pipeline:   your script --(CARLA API, TCP 2000)--> CARLA server (renders on the GPU) --camera images--> your script
"""
import argparse
import math
import os
import queue
import random

import carla
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seconds', type=float, default=60)
    ap.add_argument('--headless', action='store_true')
    a = ap.parse_args()

    client = carla.Client('127.0.0.1', 2000)
    client.set_timeout(30)
    world = client.get_world()
    tm = client.get_trafficmanager(8000)
    settings = world.get_settings()
    settings.synchronous_mode, settings.fixed_delta_seconds = True, 0.05       # 20 Hz, deterministic
    world.apply_settings(settings)
    tm.set_synchronous_mode(True)

    bp = world.get_blueprint_library()
    car_bp = bp.find('vehicle.tesla.model3')
    car_bp.set_attribute('role_name', 'hero')
    car = world.spawn_actor(car_bp, random.choice(world.get_map().get_spawn_points()))
    cam_bp = bp.find('sensor.camera.rgb')
    cam_bp.set_attribute('image_size_x', '960')
    cam_bp.set_attribute('image_size_y', '540')
    cam = world.spawn_actor(cam_bp, carla.Transform(carla.Location(x=-6, z=3), carla.Rotation(pitch=-15)),
                            attach_to=car)
    frames = queue.Queue()
    cam.listen(frames.put)
    car.set_autopilot(True, tm.get_port())
    print('spawned', car.type_id, 'on', world.get_map().name.split('/')[-1], '- autopilot on')

    screen = None
    if not a.headless:
        import pygame
        pygame.init()
        screen = pygame.display.set_mode((960, 540))
        pygame.display.set_caption('CARLA chase camera (close the window to stop)')
        font = pygame.font.SysFont('monospace', 22)
    try:
        for i in range(int(a.seconds / settings.fixed_delta_seconds)):
            world.tick()
            img = frames.get(timeout=10)
            rgb = np.frombuffer(img.raw_data, np.uint8).reshape(img.height, img.width, 4)[:, :, 2::-1]
            v = car.get_velocity()
            kmh = 3.6 * math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)
            if screen is not None:
                import pygame
                if any(e.type == pygame.QUIT for e in pygame.event.get()):
                    break
                screen.blit(pygame.surfarray.make_surface(rgb.swapaxes(0, 1)), (0, 0))
                screen.blit(font.render('%5.1f km/h' % kmh, True, (255, 255, 0)), (10, 10))
                pygame.display.flip()
            if i % 20 == 0:
                print('t=%5.1f s  speed %5.1f km/h' % (i * settings.fixed_delta_seconds, kmh))
        if a.headless:
            import cv2
            cv2.imwrite(os.path.expanduser('~/carla_chase.png'), rgb[:, :, ::-1])
            print('saved ~/carla_chase.png')
    finally:
        cam.stop()
        cam.destroy()
        car.destroy()
        settings.synchronous_mode = False
        world.apply_settings(settings)
        tm.set_synchronous_mode(False)


if __name__ == '__main__':
    main()
