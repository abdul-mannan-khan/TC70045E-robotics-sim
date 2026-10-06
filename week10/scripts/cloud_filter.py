#!/usr/bin/env python3
"""cloud_filter.py - pass-through + voxel-grid filter for a PointCloud2, in a few lines of NumPy.

Replaces the pcl_ros filter nodes, which do not exist in the ROS 2 Humble binary release of pcl_ros.
  pass-through: keep points with z_min < z < z_max (camera optical frame: +z is forward)
  voxel grid:   keep one point per occupied cube of side `leaf` (use leaf:=0.001 for pass-through only)
Publishes XYZ (12 bytes per point) on `output` and logs the reduction every 2 s.

Usage (a cloud on /camera/depth/color/points, e.g. from depth_image_proc)
  python3 ~/labs/week10/scripts/cloud_filter.py --ros-args -p use_sim_time:=true     -r input:=/camera/depth/color/points -r output:=/cloud_voxel -p z_min:=0.3 -p z_max:=4.0 -p leaf:=0.05

Expected output
  [cloud_filter]: in 407040 -> out 3000 points (0.7% kept)     (numbers depend on the view)
"""
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2 as pc2


class CloudFilter(Node):
    def __init__(self):
        super().__init__('cloud_filter')
        self.declare_parameter('z_min', 0.3)          # metres, camera optical frame: +z is forward
        self.declare_parameter('z_max', 4.0)
        self.declare_parameter('leaf', 0.05)          # voxel edge length in metres
        self.sub = self.create_subscription(PointCloud2, 'input', self.cb, qos_profile_sensor_data)
        self.pub = self.create_publisher(PointCloud2, 'output', 10)

    def cb(self, msg):
        p = self.get_parameter
        z_min, z_max, leaf = p('z_min').value, p('z_max').value, p('leaf').value
        pts = pc2.read_points_numpy(msg, field_names=('x', 'y', 'z'), skip_nans=True)
        if pts.size == 0:
            return
        keep = (pts[:, 2] > z_min) & (pts[:, 2] < z_max)          # pass-through
        pts = pts[keep]
        if pts.size:
            keys = np.floor(pts / leaf).astype(np.int64)          # voxel grid: one point per occupied voxel
            _, first = np.unique(keys, axis=0, return_index=True)
            pts = pts[np.sort(first)]
        out = pc2.create_cloud_xyz32(msg.header, pts.tolist())
        self.pub.publish(out)
        self.get_logger().info('in %d -> out %d points (%.1f%% kept)'
                               % (msg.width * msg.height, len(pts),
                                  100.0 * len(pts) / max(1, msg.width * msg.height)), throttle_duration_sec=2.0)


def main():
    rclpy.init()
    node = CloudFilter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
