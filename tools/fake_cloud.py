#!/usr/bin/env python3
# Publishes a synthetic 640x480-sized organised-ish cloud so cloud_filter.py can be tested without a camera.
import numpy as np, rclpy
from rclpy.node import Node
from std_msgs.msg import Header
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2 as pc2

class Fake(Node):
    def __init__(self):
        super().__init__('fake_cloud')
        self.pub = self.create_publisher(PointCloud2, '/camera/depth/color/points', 10)
        self.timer = self.create_timer(0.2, self.tick)
        rng = np.random.default_rng(0)
        self.pts = np.column_stack([rng.uniform(-1, 1, 307200),
                                    rng.uniform(-1, 1, 307200),
                                    rng.uniform(0.0, 6.0, 307200)]).astype(np.float32)
    def tick(self):
        h = Header(); h.frame_id = 'camera_depth_optical_frame'
        h.stamp = self.get_clock().now().to_msg()
        self.pub.publish(pc2.create_cloud_xyz32(h, self.pts.tolist()))

def main():
    rclpy.init(); n = Fake()
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    finally: n.destroy_node(); rclpy.shutdown()

if __name__ == '__main__':
    main()
