#!/usr/bin/env python3
"""orb_features.py - ORB keypoints and frame-to-frame matching on the (simulated) D455 colour stream.

For every colour frame: detect ORB keypoints (FAST + Harris ranking, 8-level pyramid), compute the 256-bit
descriptors, match them to the previous frame by Hamming distance with Lowe's ratio test, then keep the
matches that agree with one epipolar geometry (fundamental matrix, RANSAC). Prints once a second and a
summary at Ctrl+C. Optionally saves one annotated keypoint image.

Usage (simulator running with camera:=true)
  python3 ~/labs/week10/scripts/orb_features.py --ros-args -p use_sim_time:=true
  ... -p nfeatures:=1000 -p ratio:=0.75 -p save:=orb.png

Expected output (lab world, robot still on its start mark, camera_width:=424 camera_height:=240, ~7 Hz)
  kp  239  ratio-test matches  239  RANSAC inliers  239  median Hamming    0  ORB   2 ms  match   1 ms
  summary over 170 frames: keypoints mean 239 min 239 | good matches mean 239 | inliers 100.0 % | median Hamming 0 | ...
  (rendered frames of a still scene are identical, so Hamming 0; turning at 0.3 rad/s gives ~156 matches, Hamming ~9;
   in front of the plain grey wall of the range world: keypoints mean 0)
"""
import time
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class OrbFeatures(Node):
    def __init__(self):
        super().__init__('orb_features')
        p = self.declare_parameter
        self.orb = cv2.ORB_create(nfeatures=p('nfeatures', 1000).value)
        self.ratio = p('ratio', 0.75).value
        self.save = p('save', '').value
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        self.prev, self.stats, self.last_print = None, [], 0.0
        self.create_subscription(Image, '/camera/color/image_raw', self.cb, 5)

    def cb(self, msg):
        img = np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.width, -1)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        t0 = time.perf_counter()
        kp, des = self.orb.detectAndCompute(gray, None)
        t1 = time.perf_counter()
        good, inl, ham = 0, 0, float('nan')
        if self.prev is not None and des is not None and self.prev[1] is not None and len(kp) > 8:
            pairs = self.bf.knnMatch(self.prev[1], des, k=2)
            m = [a for a, *b in pairs if b and a.distance < self.ratio * b[0].distance]   # Lowe ratio test
            good = len(m)
            if good >= 8:
                ham = float(np.median([x.distance for x in m]))
                p0 = np.float32([self.prev[0][x.queryIdx].pt for x in m])
                p1 = np.float32([kp[x.trainIdx].pt for x in m])
                _, mask = cv2.findFundamentalMat(p0, p1, cv2.FM_RANSAC, 1.0, 0.99)
                inl = int(mask.sum()) if mask is not None else 0
        t2 = time.perf_counter()
        self.prev = (kp, des)
        self.stats.append((len(kp), good, inl, ham, 1e3 * (t1 - t0), 1e3 * (t2 - t1)))
        if self.save and len(self.stats) == 5:
            cv2.imwrite(self.save, cv2.drawKeypoints(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), kp, None, (0, 255, 0)))
            self.get_logger().info('saved ' + self.save)
        if time.time() - self.last_print > 1.0:
            self.last_print = time.time()
            print('kp %4d  ratio-test matches %4d  RANSAC inliers %4d  median Hamming %4.0f  ORB %3.0f ms  match %3.0f ms'
                  % self.stats[-1], flush=True)

    def summary(self):
        s = np.array(self.stats[1:], float)
        if len(s) == 0:
            print('no frames received - is the simulator running with camera:=true?')
            return
        ham = s[~np.isnan(s[:, 3]), 3]                     # no matches at all -> no Hamming distances
        print('summary over %d frames: keypoints mean %.0f min %.0f | good matches mean %.0f | inliers %.1f %% '
              '| median Hamming %s | ORB %.1f ms, matching %.1f ms per frame'
              % (len(s), s[:, 0].mean(), s[:, 0].min(), s[:, 1].mean(), 100 * s[:, 2].sum() / max(1, s[:, 1].sum()),
                 '%.0f' % np.median(ham) if len(ham) else 'n/a', s[:, 4].mean(), s[:, 5].mean()))


def main():
    rclpy.init()
    node = OrbFeatures()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.summary()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
