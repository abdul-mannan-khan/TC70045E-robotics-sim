"""Turn the simulator's ideal depth into D455-style depth: stereo noise, range limits, dropouts, millimetres.

Input (from the Gazebo RGB-D sensor):   camera_sim/ideal/image_raw, camera_sim/ideal/camera_info (colour)
                                        camera_sim/ideal/depth/image_raw (32FC1, metres, ideal)
Output (the same names the realsense2_camera driver uses with camera_namespace:=/ camera_name:=camera):
  camera/color/image_raw, camera/color/camera_info
  camera/depth/image_rect_raw, camera/depth/camera_info                         16UC1, millimetres, 0 = no data
  camera/aligned_depth_to_color/image_raw, camera/aligned_depth_to_color/camera_info
(In simulation colour and depth come from one sensor, so depth is already aligned to colour.)

Stereo error model (active IR stereo, rectified pair):
  Z = f b / d   ->   sigma_Z = Z^2 sigma_d / (f b)
  f from camera_info (447 px for 848 x 480 and 87 deg), b = baseline (0.095 m), sigma_d = sub-pixel disparity noise.
Pixels closer than min_z (the minimum range, MinZ) or beyond max_z are returned as 0, and the chance of a missing
pixel grows with range (weaker dot pattern, fewer matched features), which lowers the fill rate far away.
"""
import numpy as np
import rclpy
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, CameraInfo


OUT_QOS = 5  # outputs RELIABLE, depth 5: matches both reliable (rviz2, rtabmap) and best-effort subscribers


class StereoDepth(Node):
    def __init__(self):
        super().__init__('stereo_depth')
        p = self.declare_parameter
        self.baseline = p('baseline_m', 0.095).value
        self.sigma_d = p('subpixel_noise_px', 0.08).value
        self.min_z = p('min_z_m', 0.52).value
        self.max_z = p('max_z_m', 10.0).value
        self.drop_near = p('dropout_near', 0.01).value
        self.drop_far = p('dropout_far', 0.35).value
        self.enable_noise = p('noise', True).value
        self.rng = np.random.default_rng(p('seed', 7).value)
        self.info = None

        self.pub_color = self.create_publisher(Image, 'camera/color/image_raw', OUT_QOS)
        self.pub_color_info = self.create_publisher(CameraInfo, 'camera/color/camera_info', OUT_QOS)
        self.pub_depth = self.create_publisher(Image, 'camera/depth/image_rect_raw', OUT_QOS)
        self.pub_depth_info = self.create_publisher(CameraInfo, 'camera/depth/camera_info', OUT_QOS)
        self.pub_aligned = self.create_publisher(Image, 'camera/aligned_depth_to_color/image_raw', OUT_QOS)
        self.pub_aligned_info = self.create_publisher(CameraInfo, 'camera/aligned_depth_to_color/camera_info', OUT_QOS)
        # Colour is only relayed; depth needs the noise maths. Separate callback groups on a multi-threaded executor
        # stop a slow depth frame from holding up colour frames (numpy releases the GIL while it computes).
        colour, depth = MutuallyExclusiveCallbackGroup(), MutuallyExclusiveCallbackGroup()
        self.create_subscription(Image, 'camera_sim/ideal/image_raw', self.pub_color.publish, qos_profile_sensor_data,
                                 callback_group=colour)
        self.create_subscription(CameraInfo, 'camera_sim/ideal/camera_info', self.on_info, qos_profile_sensor_data,
                                 callback_group=colour)
        self.create_subscription(Image, 'camera_sim/ideal/depth/image_raw', self.on_depth, qos_profile_sensor_data,
                                 callback_group=depth)

    def on_info(self, msg):
        self.info = msg
        self.pub_color_info.publish(msg)

    def on_depth(self, msg):
        if msg.encoding != '32FC1':
            self.get_logger().warn('unexpected depth encoding %s' % msg.encoding, throttle_duration_sec=5.0)
            return
        z = np.frombuffer(msg.data, dtype=np.float32).reshape(msg.height, msg.width)
        f = np.float32(self.info.k[0] if self.info is not None else 447.0)
        valid = np.isfinite(z) & (z >= self.min_z) & (z <= self.max_z)
        z = np.where(valid, z, np.float32(0.0))           # float32 throughout: this runs on every frame
        if self.enable_noise:
            sigma = z * z * np.float32(self.sigma_d / self.baseline) / f
            z = z + self.rng.standard_normal(z.shape, dtype=np.float32) * sigma
            p_drop = np.float32(self.drop_near) + np.float32(self.drop_far) * np.square(z / np.float32(self.max_z))
            valid &= self.rng.random(z.shape, dtype=np.float32) >= p_drop
        mm = np.where(valid, np.rint(z * np.float32(1000.0)), np.float32(0.0)).clip(0, 65535).astype(np.uint16)

        out = Image()
        out.header = msg.header
        out.height, out.width = msg.height, msg.width
        out.encoding = '16UC1'
        out.is_bigendian = 0
        out.step = msg.width * 2
        out.data = mm.tobytes()
        self.pub_depth.publish(out)
        self.pub_aligned.publish(out)
        if self.info is not None:
            info = CameraInfo()                      # a copy: the colour thread may be using self.info
            info.header = msg.header
            info.height, info.width = self.info.height, self.info.width
            info.distortion_model, info.d = self.info.distortion_model, self.info.d
            info.k, info.r, info.p = self.info.k, self.info.r, self.info.p
            self.pub_depth_info.publish(info)
            self.pub_aligned_info.publish(info)


def main():
    rclpy.init()
    node = StereoDepth()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
