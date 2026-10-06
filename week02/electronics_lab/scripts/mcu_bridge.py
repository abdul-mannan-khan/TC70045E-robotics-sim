#!/usr/bin/env python3
"""Host side of the host-to-microcontroller UART link: parse, validate and publish the board's reports.

Purpose  Week 2, Laboratory B. This is the job the 'driver node' does on every robot with a motor/sensor
         microcontroller board: turn a byte stream into ROS 2 topics, and /cmd_vel into command frames.
Usage    terminal 1:  ros2 run tc70045e_sim virtual_mcu                    (creates /tmp/ttyMCU, 115200 8N1)
         terminal 2:  python3 ~/labs/week02/scripts/mcu_bridge.py
         terminal 3:  ros2 topic hz /mcu/imu      ros2 topic echo /mcu/vel
                      ros2 topic pub -r 5 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}}"
Protocol 0xFF 0xFB | LEN | FUNC | PAYLOAD | CHECKSUM,  LEN = bytes after LEN,
         CHECKSUM = (LEN + FUNC + sum(PAYLOAD)) & 0xFF, little-endian payloads (see virtual_mcu --help text).
Output   topics /mcu/vel (Twist), /mcu/imu (Imu), /mcu/voltage (Float32), /mcu/encoders (Int32MultiArray),
         and every 5 s a link report: frames/s per type, bytes/s, link utilisation, checksum failures,
         bytes discarded while resynchronising, and SPEED frames that passed the checksum but are WRONG.
"""
import math
import signal
import struct
import time

import rclpy
import serial
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32, Int32MultiArray

HEAD = b'\xff\xfb'
NAMES = {0x0A: 'SPEED', 0x0B: 'IMU', 0x0C: 'BATTERY', 0x0D: 'ENCODER'}
SIZES = {0x0A: 6, 0x0B: 12, 0x0C: 2, 0x0D: 16}           # expected payload bytes per report


def make_frame(func, payload):
    ln = len(payload) + 2
    return HEAD + bytes([ln, func]) + payload + bytes([(ln + func + sum(payload)) & 0xFF])


class Parser:
    """Byte-stream -> frames. Keeps statistics; never trusts LEN or FUNC until the checksum agrees."""
    def __init__(self):
        self.buf = bytearray()
        self.good, self.bad, self.skipped = {}, 0, 0

    def feed(self, data):
        self.buf += data
        frames = []
        while True:
            i = self.buf.find(HEAD)
            if i < 0:                                        # no header: keep the last byte (could be 0xFF)
                self.skipped += max(len(self.buf) - 1, 0)
                del self.buf[:-1]
                return frames
            self.skipped += i
            del self.buf[:i]
            if len(self.buf) < 3:
                return frames
            ln = self.buf[2]
            if not 2 <= ln <= 40:                             # impossible length: header was a false match
                self.skipped += 1
                del self.buf[:1]
                continue
            if len(self.buf) < 3 + ln:
                return frames                                # wait for the rest of the frame
            func, payload, cs = self.buf[3], bytes(self.buf[4:2 + ln]), self.buf[2 + ln]
            if (ln + func + sum(payload)) & 0xFF != cs:
                self.bad += 1
                del self.buf[:1]                             # resync from the next byte, not after LEN
                continue
            del self.buf[:3 + ln]
            self.good[func] = self.good.get(func, 0) + 1
            frames.append((func, payload))


class Bridge(Node):
    def __init__(self):
        super().__init__('mcu_bridge')
        port = self.declare_parameter('port', '/tmp/ttyMCU').value
        self.baud = self.declare_parameter('baud', 115200).value
        self.ser = serial.Serial(port, self.baud, timeout=0)
        self.p = Parser()
        self.pub_vel = self.create_publisher(Twist, 'mcu/vel', 10)
        self.pub_imu = self.create_publisher(Imu, 'mcu/imu', 10)
        self.pub_v = self.create_publisher(Float32, 'mcu/voltage', 10)
        self.pub_enc = self.create_publisher(Int32MultiArray, 'mcu/encoders', 10)
        self.create_subscription(Twist, 'cmd_vel', self.on_cmd, 10)
        self.cmd, self.t_cmd = (0, 0, 0), time.monotonic()
        self.nbytes, self.wrong, self.t0, self.last = 0, 0, time.monotonic(), {}
        self.create_timer(0.005, self.poll)                  # read the port at 200 Hz
        self.create_timer(5.0, self.report)
        self.get_logger().info('bridge on %s at %d baud' % (port, self.baud))

    def on_cmd(self, m):                                     # /cmd_vel -> MOTION frame (mm/s, mrad/s)
        c = tuple(max(-32768, min(32767, int(round(v * 1000))))
                  for v in (m.linear.x, m.linear.y, m.angular.z))
        if c != self.cmd:
            self.cmd, self.t_cmd = c, time.monotonic()
        self.ser.write(make_frame(0x12, struct.pack('<3h', *c)))

    def poll(self):
        data = self.ser.read(self.ser.in_waiting or 1)
        self.nbytes += len(data)
        for func, pl in self.p.feed(data):
            if len(pl) != SIZES.get(func, -1):
                continue
            if func == 0x0A:
                vx, vy, wz = struct.unpack('<3h', pl)
                if time.monotonic() - self.t_cmd > 0.2 and (vx, vy, wz) != self.cmd:
                    self.wrong += 1                          # checksum passed, content is not what we sent
                t = Twist()
                t.linear.x, t.linear.y, t.angular.z = vx / 1000.0, vy / 1000.0, wz / 1000.0
                self.pub_vel.publish(t)
            elif func == 0x0B:
                g = struct.unpack('<6h', pl)
                m = Imu()
                m.header.stamp, m.header.frame_id = self.get_clock().now().to_msg(), 'imu_link'
                d2r = math.pi / 180.0 / 100.0                # 0.01 deg/s -> rad/s
                m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z = (v * d2r for v in g[:3])
                m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z = \
                    (v * 9.80665e-3 for v in g[3:])          # mg -> m/s^2
                self.pub_imu.publish(m)
            elif func == 0x0C:
                self.pub_v.publish(Float32(data=struct.unpack('<H', pl)[0] / 100.0))
            elif func == 0x0D:
                self.pub_enc.publish(Int32MultiArray(data=list(struct.unpack('<4i', pl))))

    def report(self):
        dt = time.monotonic() - self.t0
        rates = '  '.join('%s %.1f/s' % (NAMES.get(f, hex(f)), (n - self.last.get(f, 0)) / dt)
                          for f, n in sorted(self.p.good.items()))
        bps = self.nbytes / dt
        self.get_logger().info('%s | %.0f B/s = %.1f %% of the link | bad checksum %d | skipped bytes %d | '
                               'wrong-but-accepted SPEED %d' % (rates, bps, 100.0 * bps * 10 / self.baud,
                                                                self.p.bad, self.p.skipped, self.wrong))
        self.last, self.nbytes, self.t0 = dict(self.p.good), 0, time.monotonic()


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    signal.signal(signal.SIGINT, signal.default_int_handler)     # Ctrl-C -> a clean KeyboardInterrupt
    node = Bridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.ser.close()
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
