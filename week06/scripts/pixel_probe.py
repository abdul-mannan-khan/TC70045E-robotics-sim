#!/usr/bin/env python3
"""pixel_probe.py - what the D455 sees at one pixel: colour (BGR and HSV) and depth (Week 6, A2 and A3).

Prints once a second for the pixel (u, v) - by default the image centre, marked by the crosshair in RViz's camera
panel when you look at it - the colour as B, G, R and as H, S, V (OpenCV scale: H 0-179, S and V 0-255) and the
depth from the aligned depth image (millimetres; 0 = no depth), averaged over a 5 x 5 patch.

Usage:
  python3 ~/labs/week06/scripts/pixel_probe.py --ros-args -p use_sim_time:=true
  python3 ~/labs/week06/scripts/pixel_probe.py --ros-args -p use_sim_time:=true -p u:=100 -p v:=150
Expected (robot facing the red box from about 1.5 m, centre pixel on the box):
  pixel (212, 120)  BGR (  0,   0, 178)  HSV (  0, 255, 178)  depth 1347 mm (25/25 valid)
"""
import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image


class PixelProbe(Node):
    def __init__(self):
        super().__init__('pixel_probe')
        self.u, self.v = self.declare_parameter('u', -1).value, self.declare_parameter('v', -1).value
        self.bridge, self.img, self.depth = CvBridge(), None, None
        self.create_subscription(Image, '/camera/color/image_raw', lambda m: setattr(self, 'img', m), 5)
        self.create_subscription(Image, '/camera/aligned_depth_to_color/image_raw', lambda m: setattr(self, 'depth', m), 5)
        self.create_timer(1.0, self.report)

    def report(self):
        if self.img is None or self.depth is None:
            self.get_logger().info('waiting for the camera images ...')
            return
        bgr = self.bridge.imgmsg_to_cv2(self.img, 'bgr8')
        d = self.bridge.imgmsg_to_cv2(self.depth, 'passthrough')
        h, w = bgr.shape[:2]
        u = self.u if self.u >= 0 else w // 2
        v = self.v if self.v >= 0 else h // 2
        b, g, r = (int(c) for c in bgr[v, u])
        hh, ss, vv = (int(c) for c in cv2.cvtColor(bgr[v:v + 1, u:u + 1], cv2.COLOR_BGR2HSV)[0, 0])
        patch = d[max(0, v - 2):v + 3, max(0, u - 2):u + 3].astype(float)
        ok = patch[patch > 0]
        z = '%4.0f mm' % ok.mean() if ok.size else '  no depth'
        print('pixel (%d, %d)  BGR (%3d, %3d, %3d)  HSV (%3d, %3d, %3d)  depth %s (%d/%d valid)'
              % (u, v, b, g, r, hh, ss, vv, z, ok.size, patch.size), flush=True)


def main():
    rclpy.init()
    node = PixelProbe()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
