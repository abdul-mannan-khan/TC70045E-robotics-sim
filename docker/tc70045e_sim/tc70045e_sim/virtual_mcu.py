"""Virtual motor/sensor microcontroller on a serial port - the host-to-microcontroller UART link, without hardware.

Creates a pseudo-terminal (a virtual serial port) and links it to /tmp/ttyMCU. Open that with pyserial at 115200 baud
exactly as you would open /dev/ttyUSB0 on a real robot. Bytes are paced at the real 115200 8N1 rate (11.52 kB/s).

Frame format (little-endian):   0xFF 0xFB | LEN | FUNC | PAYLOAD ... | CHECKSUM
  LEN      = number of bytes after LEN, including FUNC and CHECKSUM
  CHECKSUM = (LEN + FUNC + sum(PAYLOAD)) & 0xFF

Reports, microcontroller -> host (25 Hz unless stated):
  0x0A SPEED    3 x int16  vx, vy [mm/s], wz [mrad/s]
  0x0B IMU      6 x int16  gyro x,y,z [0.01 deg/s], accel x,y,z [mg]            (50 Hz)
  0x0C BATTERY  1 x uint16 pack voltage [10 mV]                                  (1 Hz)
  0x0D ENCODER  4 x int32  cumulative counts fl, fr, rl, rr
Commands, host -> microcontroller:
  0x12 MOTION   3 x int16  vx, vy [mm/s], wz [mrad/s]    (the virtual robot then 'moves' and reports accordingly)
  0x02 BEEP     1 x uint16 duration [ms]
Frames with a bad checksum are dropped and counted. bit_error_rate > 0 flips random bits on the way out, so you can
prove that your parser rejects corrupted frames. Run:  ros2 run tc70045e_sim virtual_mcu --ros-args -p bit_error_rate:=1e-4
"""
import math
import os
import pty
import random
import struct
import threading
import time
import tty

import rclpy
from rclpy.node import Node

HEAD = b'\xff\xfb'


def frame(func, payload):
    ln = len(payload) + 2
    cs = (ln + func + sum(payload)) & 0xFF
    return HEAD + bytes([ln, func]) + payload + bytes([cs])


class VirtualMCU(Node):
    def __init__(self):
        super().__init__('virtual_mcu')
        p = self.declare_parameter
        self.link = p('link', '/tmp/ttyMCU').value
        self.baud = p('baud', 115200).value
        self.ber = p('bit_error_rate', 0.0).value
        self.master, slave = pty.openpty()
        tty.setraw(slave)
        name = os.ttyname(slave)
        try:
            if os.path.islink(self.link) or os.path.exists(self.link):
                os.remove(self.link)
            os.symlink(name, self.link)
        except OSError as e:
            self.get_logger().error('cannot create %s: %s' % (self.link, e))
        self.slave = slave
        self.cmd = (0, 0, 0)
        self.counts = [0.0] * 4
        self.voltage = 12.2
        self.rx_ok = self.rx_bad = 0
        self.lock = threading.Lock()
        self.tx_queue = bytearray()
        threading.Thread(target=self.reader, daemon=True).start()
        threading.Thread(target=self.writer, daemon=True).start()
        self.k = 0
        self.create_timer(0.02, self.tick)
        self.get_logger().info('virtual microcontroller on %s -> %s (%d baud 8N1)' % (self.link, name, self.baud))

    def send(self, data):
        if self.ber > 0.0:
            b = bytearray(data)
            for i in range(len(b)):
                for bit in range(8):
                    if random.random() < self.ber:
                        b[i] ^= 1 << bit
            data = bytes(b)
        with self.lock:
            self.tx_queue += data

    def writer(self):
        byte_time = 10.0 / self.baud        # start + 8 data + stop bits
        while rclpy.ok():
            with self.lock:
                chunk = bytes(self.tx_queue[:64])
                del self.tx_queue[:64]
            if chunk:
                os.write(self.master, chunk)
                time.sleep(len(chunk) * byte_time)
            else:
                time.sleep(0.001)

    def reader(self):
        buf = bytearray()
        while rclpy.ok():
            try:
                buf += os.read(self.master, 256)
            except OSError:
                time.sleep(0.01)
                continue
            while True:
                i = buf.find(HEAD)
                if i < 0 or len(buf) < i + 4:
                    break
                ln = buf[i + 2]
                if len(buf) < i + 3 + ln:
                    break
                func, payload, cs = buf[i + 3], bytes(buf[i + 4:i + 2 + ln]), buf[i + 2 + ln]
                del buf[:i + 3 + ln]
                if (ln + func + sum(payload)) & 0xFF != cs:
                    self.rx_bad += 1
                    continue
                self.rx_ok += 1
                if func == 0x12 and len(payload) == 6:
                    self.cmd = struct.unpack('<hhh', payload)
                elif func == 0x02:
                    self.get_logger().info('BEEP')

    def tick(self):
        self.k += 1
        vx, vy, wz = (c / 1000.0 for c in self.cmd)
        L, r, c_rev = 0.18, 0.0375, 2464
        w = [(vx - vy - L * wz) / r, (vx + vy + L * wz) / r, (vx + vy - L * wz) / r, (vx - vy + L * wz) / r]
        for i in range(4):
            self.counts[i] += w[i] * 0.02 * c_rev / (2 * math.pi)
        g = [random.gauss(0, 10) for _ in range(3)]
        g[2] += wz * 180 / math.pi * 100
        a = [random.gauss(0, 15), random.gauss(0, 15), 1000 + random.gauss(0, 15)]
        self.send(frame(0x0B, struct.pack('<6h', *[int(round(v)) for v in g + a])))
        if self.k % 2 == 0:
            spd = [int(round(vx * 1000)), int(round(vy * 1000)), int(round(wz * 1000))]
            self.send(frame(0x0A, struct.pack('<3h', *spd)))
            self.send(frame(0x0D, struct.pack('<4i', *[int(c) for c in self.counts])))
        if self.k % 50 == 0:
            self.voltage -= 0.001 + 0.004 * (abs(vx) + abs(vy))
            self.send(frame(0x0C, struct.pack('<H', int(round(self.voltage * 100)))))
            self.get_logger().info('host frames: %d good, %d bad checksum' % (self.rx_ok, self.rx_bad),
                                   throttle_duration_sec=10.0)


def main():
    rclpy.init()
    node = VirtualMCU()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
