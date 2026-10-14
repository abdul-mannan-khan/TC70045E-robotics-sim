#!/usr/bin/env python3
"""box_finder.py - find the coloured boxes with the D455 and mark them on the SLAM map (Week 6, SOLUTION).

For every colour image:
  1. colour   HSV threshold -> mask -> largest blob -> centroid pixel (u, v)              (TODO 1: the green range)
  2. depth    median of the aligned depth image inside the blob -> Z [m] (the box's near face)
  3. 3-D      pinhole model: back-project (u, v, Z) -> point (X, Y, Z) in camera_color_optical_frame  (TODO 2)
  4. map      TF camera_color_optical_frame -> map: the point in the map                                (TODO 3)
  5. publish  /boxes (visualization_msgs/MarkerArray: a cube + label per box, median of all detections)
              /box_finder/mask (sensor_msgs/Image: what the colour threshold sees - show it in RViz)
On Ctrl+C it prints, for each box, the mean position, the spread and the error against the true box.

Usage (perception.launch.py running, in a second terminal):
  python3 ~/labs/week06/scripts/box_finder.py --ros-args -p use_sim_time:=true
Expected (end of the tour, measured): see the README's table - both boxes within about 0.1 m
"""
import math
import signal

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import PointStamped
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import CameraInfo, Image
from tf2_geometry_msgs import do_transform_point
from tf2_ros import Buffer, TransformListener
from visualization_msgs.msg import Marker, MarkerArray

# HSV ranges (OpenCV: H 0-179, S 0-255, V 0-255). Red wraps round H = 0, so it needs two ranges.
# S >= 200 rejects the brick walls (S up to ~180); H <= 4 rejects the wooden crates and posters (H 6-17).
COLOURS = {
    'red':   [((0, 200, 60), (4, 255, 255)), ((175, 200, 60), (179, 255, 255))],
    'green': [((50, 200, 60), (70, 255, 255))],                  # SOLUTION TODO 1: Gazebo/Green is H = 60
}
BOX_HALF = 0.15                     # the boxes are 0.3 m cubes: the centre is 0.15 m behind the face the camera sees
TRUTH_MAP = {'red': (1.5, -2.4), 'green': (7.2, -0.4)}   # true box centres in the map frame (world - spawn)
MIN_AREA = 80                       # pixels: ignore specks
MAX_RANGE = 3.5                     # m: farther away the blob is small and the depth noisy (sigma ~ Z^2)


class BoxFinder(Node):
    def __init__(self):
        super().__init__('box_finder')
        self.bridge, self.K, self.depth = CvBridge(), None, None
        self.found = {c: [] for c in COLOURS}
        self.tf = Buffer(cache_time=Duration(seconds=30))
        TransformListener(self.tf, self, spin_thread=True)   # TF arrives even while a callback waits for it
        self.create_subscription(CameraInfo, '/camera/color/camera_info', self.on_info, 5)
        self.create_subscription(Image, '/camera/aligned_depth_to_color/image_raw', self.on_depth, 5)
        self.create_subscription(Image, '/camera/color/image_raw', self.on_image, 5)
        self.pub_marks = self.create_publisher(MarkerArray, '/boxes', 5)
        self.pub_mask = self.create_publisher(Image, '/box_finder/mask', 5)
        self.get_logger().info('looking for: %s' % ', '.join(COLOURS))

    def on_info(self, m):
        self.K = np.array(m.k).reshape(3, 3)

    def on_depth(self, m):
        self.depth = (m.header.stamp, self.bridge.imgmsg_to_cv2(m, 'passthrough'))

    def on_image(self, m):
        if self.K is None or self.depth is None:
            return
        img = self.bridge.imgmsg_to_cv2(m, 'bgr8')
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        depth = self.depth[1]
        all_masks = np.zeros(hsv.shape[:2], np.uint8)
        for colour, ranges in COLOURS.items():
            mask = np.zeros(hsv.shape[:2], np.uint8)
            for lo, hi in ranges:
                mask |= cv2.inRange(hsv, lo, hi)
            all_masks |= mask
            n, lab, stats, cent = cv2.connectedComponentsWithStats(mask)
            if n < 2 or stats[1:, cv2.CC_STAT_AREA].max() < MIN_AREA:
                continue
            k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            u, v = cent[k]
            if depth.shape != mask.shape:
                continue
            z = depth[lab == k]
            z = z[z > 0]                                   # 0 = no depth at that pixel
            if z.size < 20:
                continue
            Z = float(np.median(z)) * 1e-3 + BOX_HALF     # mm -> m, then from the near face to the centre
            if Z > MAX_RANGE:
                continue
            # SOLUTION TODO 2: pinhole back-projection, (u, v) pixel + depth Z -> metres in the optical frame
            fx, fy, cx, cy = self.K[0, 0], self.K[1, 1], self.K[0, 2], self.K[1, 2]
            X = (u - cx) * Z / fx
            Y = (v - cy) * Z / fy
            p = PointStamped()
            p.header = m.header                            # frame camera_color_optical_frame, stamp = image time
            p.point.x, p.point.y, p.point.z = X, Y, Z
            try:                                           # the camera's pose in the map (the latest one TF has)
                tr = self.tf.lookup_transform('map', m.header.frame_id, rclpy.time.Time(),
                                              timeout=Duration(seconds=1.0))
            except Exception as e:                         # TF not there yet (SLAM starting)
                self.get_logger().warn('no TF map <- camera: %s' % e, throttle_duration_sec=5.0)
                continue
            # SOLUTION TODO 3: from the camera's optical frame into the map
            q = do_transform_point(p, tr).point
            # (Extension, lecture slide 5: while the robot turns fast, ask for the camera's pose at the image time:
            #  self.tf.lookup_transform_full('map', rclpy.time.Time(), m.header.frame_id,
            #      rclpy.time.Time.from_msg(m.header.stamp), 'odom', timeout=Duration(seconds=3.0)) )
            self.found[colour].append((q.x, q.y))
            if len(self.found[colour]) in (1, 10, 50) or len(self.found[colour]) % 100 == 0:
                mx, my = np.median(self.found[colour], axis=0)
                self.get_logger().info('%-5s box at (%.2f, %.2f) in the map  [%d detections, %.1f m away]'
                                       % (colour, mx, my, len(self.found[colour]), Z))
        self.pub_mask.publish(self.bridge.cv2_to_imgmsg(all_masks, 'mono8', header=m.header))
        self.publish_markers(m.header.stamp)

    def publish_markers(self, stamp):
        arr = MarkerArray()
        for i, (colour, pts) in enumerate(self.found.items()):
            if not pts:
                continue
            mx, my = np.median(pts, axis=0)        # the median: one wrong detection cannot drag it
            rgb = {'red': (1.0, 0.1, 0.1), 'green': (0.1, 0.8, 0.1)}.get(colour, (1.0, 1.0, 0.0))
            for j, kind in enumerate((Marker.CUBE, Marker.TEXT_VIEW_FACING)):
                mk = Marker()
                mk.header.frame_id, mk.header.stamp = 'map', stamp
                mk.ns, mk.id, mk.type = colour, j, kind
                mk.pose.position.x, mk.pose.position.y = float(mx), float(my)
                mk.pose.position.z = 0.15 if kind == Marker.CUBE else 0.6
                mk.pose.orientation.w = 1.0
                mk.scale.x = mk.scale.y = mk.scale.z = 0.3
                mk.color.r, mk.color.g, mk.color.b, mk.color.a = (*rgb, 0.8)
                if kind == Marker.TEXT_VIEW_FACING:
                    mk.text = '%s (%.2f, %.2f)' % (colour, mx, my)
                    mk.color.r = mk.color.g = mk.color.b = 1.0
                arr.markers.append(mk)
        self.pub_marks.publish(arr)

    def summary(self):
        print('box     detections   median x, y [m]   true x, y      error [m]   90 % of detections within [m]')
        for colour, pts in self.found.items():
            if not pts:
                print('%-7s 0            (not found)' % colour)
                continue
            a = np.array(pts)
            mx, my = np.median(a, axis=0)
            tx, ty = TRUTH_MAP[colour]
            p90 = float(np.percentile(np.hypot(a[:, 0] - tx, a[:, 1] - ty), 90))   # the worst detections show here
            print('%-7s %-12d (%5.2f, %5.2f)      (%.2f, %.2f)   %.3f       %.3f'
                  % (colour, len(a), mx, my, tx, ty, math.hypot(mx - tx, my - ty), p90), flush=True)


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)    # Ctrl+C: stop spinning, then print the summary
    signal.signal(signal.SIGINT, signal.default_int_handler)
    node = BoxFinder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.summary()
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
