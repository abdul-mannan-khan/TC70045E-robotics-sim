#!/usr/bin/env python3
"""AirSim WITHOUT ROS 2 - step 1: talk to the simulator through its Python API.

Start the simulator first:   drone-sim start --world blocks
Then run:                    python3 ~/labs/examples/airsim/01_hello_airsim.py [--show] [--depth]

Prints the drone state the simulator knows (position, attitude, IMU, GPS) and saves one front camera picture and
with --depth one metric depth picture to ~/airsim_front.png and ~/airsim_depth.png. The depth picture takes
about 5 s in this AirSim version and freezes the simulator meanwhile - do not ask for it while flying. With --show
it opens a live colour camera window (press q to close).

Pipeline:   your script --(AirSim API, TCP 41451)--> AirSim
"""
import os
import sys

import airsim
import cv2
import numpy as np


def grab(client):
    """One colour picture (BGR, uint8) and one depth picture (metres, float32) from the 'front' camera."""
    scene, depth = client.simGetImages([
        airsim.ImageRequest('front', airsim.ImageType.Scene, False, False),
        airsim.ImageRequest('front', airsim.ImageType.DepthPerspective, True, False)])
    bgr = np.frombuffer(scene.image_data_uint8, np.uint8).reshape(scene.height, scene.width, -1)[:, :, :3]
    metres = np.array(depth.image_data_float, np.float32).reshape(depth.height, depth.width)
    return bgr, metres


def main():
    client = airsim.MultirotorClient(ip='127.0.0.1', port=41451)
    client.confirmConnection()

    state = client.getMultirotorState()
    p = state.kinematics_estimated.position
    roll, pitch, yaw = airsim.to_eularian_angles(state.kinematics_estimated.orientation)
    imu = client.getImuData()
    gps = client.getGpsData().gnss.geo_point
    print('position NED   x %.2f  y %.2f  z %.2f m' % (p.x_val, p.y_val, p.z_val))
    print('attitude       roll %.1f  pitch %.1f  yaw %.1f deg' % tuple(np.degrees([roll, pitch, yaw])))
    print('IMU accel      %.2f %.2f %.2f m/s^2' % (imu.linear_acceleration.x_val, imu.linear_acceleration.y_val,
                                                    imu.linear_acceleration.z_val))
    print('GPS            lat %.6f  lon %.6f  alt %.1f m' % (gps.latitude, gps.longitude, gps.altitude))

    home = os.path.expanduser('~')
    if '--depth' in sys.argv:
        bgr, metres = grab(client)
        vis = cv2.applyColorMap(cv2.convertScaleAbs(np.clip(metres, 0, 50), alpha=255 / 50), cv2.COLORMAP_JET)
        cv2.imwrite(os.path.join(home, 'airsim_depth.png'), vis)
        print('depth          centre pixel is %.1f m away - saved ~/airsim_depth.png'
              % metres[metres.shape[0] // 2, metres.shape[1] // 2])
    else:
        scene, = client.simGetImages([airsim.ImageRequest('front', airsim.ImageType.Scene, False, False)])
        bgr = np.frombuffer(scene.image_data_uint8, np.uint8).reshape(scene.height, scene.width, -1)[:, :, :3]
    cv2.imwrite(os.path.join(home, 'airsim_front.png'), bgr)
    print('camera         %dx%d colour picture - saved ~/airsim_front.png' % (bgr.shape[1], bgr.shape[0]))

    if '--show' in sys.argv:
        while True:
            scene, = client.simGetImages([airsim.ImageRequest('front', airsim.ImageType.Scene, False, False)])
            bgr = np.frombuffer(scene.image_data_uint8, np.uint8).reshape(scene.height, scene.width, -1)[:, :, :3]
            cv2.imshow('AirSim front camera (q to quit)', bgr)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


if __name__ == '__main__':
    main()
