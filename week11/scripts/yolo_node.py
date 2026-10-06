#!/usr/bin/env python3
"""yolo_node.py - YOLO11n (ONNX Runtime, CPU) as a ROS 2 node on the simulated camera (Week 11, Lab B).

Subscribes /camera/color/image_raw (queue depth 1: always the newest frame, never a backlog),
publishes vision_msgs/Detection2DArray on /yolo/detections with the CAMERA header (so the stamp is the
shutter time and `ros2 topic delay` measures the whole chain), and an annotated image on /yolo/image.
Usage (in the folder with the .onnx files; simulator running with the camera on):
  python3 ~/labs/week11/scripts/yolo_node.py --model yolo11n.onnx --threads 4
  ros2 topic hz /yolo/detections        ros2 topic delay /yolo/detections
Every 50 frames it prints the in-node inference time and the frame age (simulated time).
"""
import argparse
import os
import sys
import time

import cv2
import numpy as np
import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.executors import ExternalShutdownException
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2D, Detection2DArray, ObjectHypothesisWithPose

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yolo_common import decode, letterbox, make_backend  # noqa: E402


class YoloNode(Node):
    def __init__(self, a):
        super().__init__('yolo_node', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', value=True)])
        self.run, self.bridge, self.stats = make_backend(a.model, a.threads), CvBridge(), []
        self.pub = self.create_publisher(Detection2DArray, '/yolo/detections', 5)
        self.pub_img = self.create_publisher(Image, '/yolo/image', 1)
        self.create_subscription(Image, '/camera/color/image_raw', self.on_image, 1)

    def on_image(self, msg):
        img = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        t0 = time.perf_counter()
        x, s, left, top = letterbox(img)
        dets = decode(self.run(x), s, left, top)
        ms = (time.perf_counter() - t0) * 1e3
        out = Detection2DArray(header=msg.header)            # keep the shutter stamp
        for c, score, x1, y1, x2, y2 in dets:
            d = Detection2D(header=msg.header)
            d.bbox.center.position.x, d.bbox.center.position.y = (x1 + x2) / 2, (y1 + y2) / 2
            d.bbox.size_x, d.bbox.size_y = x2 - x1, y2 - y1
            h = ObjectHypothesisWithPose()
            h.hypothesis.class_id, h.hypothesis.score = str(c), score
            d.results.append(h)
            out.detections.append(d)
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.putText(img, f'{c}:{score:.2f}', (int(x1), int(y1) - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))
        self.pub.publish(out)
        annotated = self.bridge.cv2_to_imgmsg(img, 'bgr8')
        annotated.header = msg.header
        self.pub_img.publish(annotated)
        age = (self.get_clock().now() - rclpy.time.Time.from_msg(msg.header.stamp)).nanoseconds * 1e-6
        self.stats.append((ms, age))
        if len(self.stats) % 50 == 0:
            a = np.array(self.stats[-50:])
            self.get_logger().info(f'last 50: pre+inf+nms p50 {np.median(a[:, 0]):.0f} ms, '
                                   f'frame age at output p50 {np.median(a[:, 1]):.0f} ms '
                                   f'p95 {np.percentile(a[:, 1], 95):.0f} ms, {len(dets)} boxes now')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='yolo11n.onnx')
    ap.add_argument('--threads', type=int, default=4)
    a, ros_args = ap.parse_known_args()
    rclpy.init(args=ros_args, signal_handler_options=SignalHandlerOptions.NO)
    try:
        rclpy.spin(YoloNode(a))
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
