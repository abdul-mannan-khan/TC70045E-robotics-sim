"""Live depth probe: mean, standard deviation and fill rate of a small patch of the depth image, once per frame.

Works unchanged on the simulated camera and on a real D455 (realsense2_camera with camera_namespace:=/).
The patch is 21 x 21 pixels centred ROW_OFFSET rows above the image centre, so that at long range in the
range world it stays on the target wall and does not include the floor (which appears below row ~249).

Usage:
    python3 ~/labs/week07/scripts/depth_probe.py
Expected output (range world, robot at x = 0, camera 6.81 m from the wall):
    [depth_probe]: Z_mean = 6810.4 mm   sigma =  66.9 mm   valid = 363/441 (fill 0.82)
"""
import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import Image

TOPIC = '/camera/aligned_depth_to_color/image_raw'   # 16UC1, millimetres, 0 = no data
HALF = 10                                            # patch half-size: 21 x 21 pixels
ROW_OFFSET = 14                                      # patch centre 14 rows above the image centre


class DepthProbe(Node):
    def __init__(self):
        super().__init__('depth_probe', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.create_subscription(Image, TOPIC, self.cb, 5)

    def cb(self, msg):
        z = np.frombuffer(msg.data, dtype=np.uint16).reshape(msg.height, msg.width)
        cy, cx = msg.height // 2 - ROW_OFFSET, msg.width // 2
        patch = z[cy - HALF:cy + HALF + 1, cx - HALF:cx + HALF + 1].astype(np.float64)
        good = patch[patch > 0]
        if good.size < 2:
            self.get_logger().warn('no valid depth in the patch (closer than MinZ, or nothing there?)')
            return
        self.get_logger().info('Z_mean = %7.1f mm   sigma = %5.1f mm   valid = %d/%d (fill %.2f)'
                               % (good.mean(), good.std(ddof=1), good.size, patch.size, good.size / patch.size))


def main():
    rclpy.init()
    node = DepthProbe()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):   # Ctrl-C, or `timeout` sending SIGTERM
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
