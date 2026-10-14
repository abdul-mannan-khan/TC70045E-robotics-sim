#!/usr/bin/env python3
"""AirSim WITH ROS 2 - the sensor bridge: AirSim's cameras and sensors as ROS 2 topics.

Start the simulator first:   drone-sim start --world blocks
Then run:                    python3 ~/labs/examples/airsim/03_airsim_ros2_bridge.py
Look at it:                  rviz2 -d ~/labs/examples/airsim/airsim.rviz

Publishes (ROS conventions: ENU world frame 'map', FLU body frame 'base_link'):
  /drone/front/image_raw    sensor_msgs/Image        bgr8, about 9 Hz (measured on an RTX A4000)
  /drone/front/camera_info  sensor_msgs/CameraInfo
  /drone/odom               nav_msgs/Odometry        ground-truth pose and velocity from the simulator, about 9 Hz
  /drone/imu                sensor_msgs/Imu          about 9 Hz
  /drone/gps/fix            sensor_msgs/NavSatFix    about 9 Hz
  /tf                       map -> base_link, base_link -> front_camera_optical

Pipeline:   AirSim --(AirSim API, TCP 41451)--> this bridge node --(ROS 2 topics)--> RViz / your nodes
AirSim uses NED/FRD (x north, y east, z down); ROS uses ENU/FLU. The conversion is in to_ros() below.
No depth topic: in this AirSim version one metric (float) depth picture takes about 5 s, which would stall the
bridge. For depth use 01_hello_airsim.py (one picture), or the simulated D455 in the Gazebo weeks.
"""
import math

import airsim
import numpy as np
import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image, Imu, NavSatFix
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster

NED_TO_ENU = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]], float)
FRD_TO_FLU = np.diag([1.0, -1.0, -1.0])


def quat_to_matrix(x, y, z, w):
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def matrix_to_quat(m):
    """Rotation matrix -> quaternion (x, y, z, w)."""
    w = np.sqrt(max(0.0, 1 + m[0, 0] + m[1, 1] + m[2, 2])) / 2
    x = np.copysign(np.sqrt(max(0.0, 1 + m[0, 0] - m[1, 1] - m[2, 2])) / 2, m[2, 1] - m[1, 2])
    y = np.copysign(np.sqrt(max(0.0, 1 - m[0, 0] + m[1, 1] - m[2, 2])) / 2, m[0, 2] - m[2, 0])
    z = np.copysign(np.sqrt(max(0.0, 1 - m[0, 0] - m[1, 1] + m[2, 2])) / 2, m[1, 0] - m[0, 1])
    return np.array([x, y, z, w])


def to_ros(pos, quat):
    """AirSim position (NED) and orientation (NED->FRD) -> ROS position (ENU) and quaternion (ENU->FLU)."""
    p = NED_TO_ENU @ np.array([pos.x_val, pos.y_val, pos.z_val])
    r_ned_frd = quat_to_matrix(quat.x_val, quat.y_val, quat.z_val, quat.w_val)
    r_enu_flu = NED_TO_ENU @ r_ned_frd @ FRD_TO_FLU
    return p, matrix_to_quat(r_enu_flu), r_enu_flu


class AirSimBridge(Node):
    def __init__(self):
        super().__init__('airsim_bridge')
        self.declare_parameter('host', '127.0.0.1')
        self.client = airsim.MultirotorClient(ip=self.get_parameter('host').value, port=41451)
        self.client.confirmConnection()
        self.pub_img = self.create_publisher(Image, '/drone/front/image_raw', 2)
        self.pub_info = self.create_publisher(CameraInfo, '/drone/front/camera_info', 2)
        self.pub_odom = self.create_publisher(Odometry, '/drone/odom', 10)
        self.pub_imu = self.create_publisher(Imu, '/drone/imu', 10)
        self.pub_gps = self.create_publisher(NavSatFix, '/drone/gps/fix', 10)
        self.tf = TransformBroadcaster(self)
        self.static_tf = StaticTransformBroadcaster(self)
        self.publish_camera_mount()
        self.create_timer(1 / 30, self.state_tick)     # state calls take well under 1 ms
        self.create_timer(1 / 10, self.camera_tick)    # one colour picture takes about 30 ms
        self.get_logger().info('AirSim bridge running: /drone/front/image_raw /drone/odom /drone/imu /drone/gps/fix')

    def publish_camera_mount(self):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id, t.child_frame_id = 'base_link', 'front_camera_optical'
        t.transform.translation.x = 0.25
        t.transform.translation.z = 0.1
        # optical frame: z forward, x right, y down (columns: optical x, y, z axes in base_link)
        q = matrix_to_quat(np.array([[0.0, 0.0, 1.0], [-1.0, 0.0, 0.0], [0.0, -1.0, 0.0]]))
        t.transform.rotation.x, t.transform.rotation.y, t.transform.rotation.z, t.transform.rotation.w = q
        self.static_tf.sendTransform(t)

    def state_tick(self):
        now = self.get_clock().now().to_msg()
        k = self.client.getMultirotorState().kinematics_estimated
        p, q, r = to_ros(k.position, k.orientation)
        odom = Odometry()
        odom.header.stamp, odom.header.frame_id, odom.child_frame_id = now, 'map', 'base_link'
        o = odom.pose.pose
        o.position.x, o.position.y, o.position.z = p
        o.orientation.x, o.orientation.y, o.orientation.z, o.orientation.w = q
        v = NED_TO_ENU @ np.array([k.linear_velocity.x_val, k.linear_velocity.y_val, k.linear_velocity.z_val])
        odom.twist.twist.linear.x, odom.twist.twist.linear.y, odom.twist.twist.linear.z = r.T @ v   # body frame
        w = FRD_TO_FLU @ np.array([k.angular_velocity.x_val, k.angular_velocity.y_val, k.angular_velocity.z_val])
        odom.twist.twist.angular.x, odom.twist.twist.angular.y, odom.twist.twist.angular.z = w
        self.pub_odom.publish(odom)

        t = TransformStamped()
        t.header = odom.header
        t.child_frame_id = 'base_link'
        t.transform.translation.x, t.transform.translation.y, t.transform.translation.z = p
        t.transform.rotation = o.orientation
        self.tf.sendTransform(t)

        d = self.client.getImuData()
        imu = Imu()
        imu.header.stamp, imu.header.frame_id = now, 'base_link'
        imu.orientation = o.orientation
        imu.angular_velocity.x, imu.angular_velocity.y, imu.angular_velocity.z = FRD_TO_FLU @ np.array(
            [d.angular_velocity.x_val, d.angular_velocity.y_val, d.angular_velocity.z_val])
        imu.linear_acceleration.x, imu.linear_acceleration.y, imu.linear_acceleration.z = FRD_TO_FLU @ np.array(
            [d.linear_acceleration.x_val, d.linear_acceleration.y_val, d.linear_acceleration.z_val])
        self.pub_imu.publish(imu)

        g = self.client.getGpsData().gnss.geo_point
        fix = NavSatFix()
        fix.header.stamp, fix.header.frame_id = now, 'base_link'
        fix.latitude, fix.longitude, fix.altitude = g.latitude, g.longitude, g.altitude
        self.pub_gps.publish(fix)

    def camera_tick(self):
        scene, = self.client.simGetImages([airsim.ImageRequest('front', airsim.ImageType.Scene, False, False)])
        stamp = self.get_clock().now().to_msg()
        img = Image()
        img.header.stamp, img.header.frame_id = stamp, 'front_camera_optical'
        img.height, img.width, img.encoding = scene.height, scene.width, 'bgr8'
        px = np.frombuffer(scene.image_data_uint8, np.uint8).reshape(scene.height, scene.width, -1)[:, :, :3]
        img.step, img.data = scene.width * 3, np.ascontiguousarray(px).tobytes()
        self.pub_img.publish(img)

        info = CameraInfo()
        info.header = img.header
        info.width, info.height = scene.width, scene.height
        f = scene.width / 2 / math.tan(math.radians(90) / 2)          # 90 degree field of view
        cx, cy = scene.width / 2, scene.height / 2
        info.k = [f, 0.0, cx, 0.0, f, cy, 0.0, 0.0, 1.0]
        info.p = [f, 0.0, cx, 0.0, 0.0, f, cy, 0.0, 0.0, 0.0, 1.0, 0.0]
        info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info.distortion_model = 'plumb_bob'
        info.d = [0.0] * 5
        self.pub_info.publish(info)


def main():
    rclpy.init()
    node = AirSimBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
