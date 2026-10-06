#!/usr/bin/env python3
"""rtabmap_stats.py - count RTAB-Map loop closures and summarise its per-update statistics.

Subscribes to /rtabmap/info (rtabmap_msgs/Info), published once per map update, and counts
  - loop closures      (loop_closure_id > 0: appearance-based, bag-of-words + geometric check)
  - proximity closures (proximity_detection_id > 0: found by searching near the current pose)
and reports the processing time per update and the working-memory size from the statistics arrays.
Prints each closure as it happens and a summary at Ctrl+C.

Usage (RTAB-Map running with use_sim_time)
  python3 ~/labs/week10/scripts/rtabmap_stats.py --ros-args -p use_sim_time:=true

Expected output
  node 57: LOOP CLOSURE with node 3
  ...
  updates 190 | loop closures 3 | proximity closures 12 | time per update mean 48 ms, max 131 ms | WM 190 nodes
"""
import rclpy
from rclpy.node import Node
from rtabmap_msgs.msg import Info


class RtabStats(Node):
    def __init__(self):
        super().__init__('rtabmap_stats')
        self.n, self.loops, self.prox, self.times, self.wm = 0, [], [], [], 0
        self.create_subscription(Info, '/rtabmap/info', self.cb, 10)

    def cb(self, m):
        self.n += 1
        stats = dict(zip(m.stats_keys, m.stats_values))
        t = stats.get('Timing/Total/ms')
        if t is not None:
            self.times.append(t)
        self.wm = int(stats.get('Memory/Working_memory_size/', self.wm))
        if m.loop_closure_id > 0:
            self.loops.append((m.ref_id, m.loop_closure_id))
            print('node %d: LOOP CLOSURE with node %d' % self.loops[-1], flush=True)
        if m.proximity_detection_id > 0:
            self.prox.append((m.ref_id, m.proximity_detection_id))
            print('node %d: proximity closure with node %d' % self.prox[-1], flush=True)

    def summary(self):
        tm = 'mean %.0f ms, max %.0f ms' % (sum(self.times) / len(self.times), max(self.times)) if self.times else 'n/a'
        print('updates %d | loop closures %d | proximity closures %d | time per update %s | WM %d nodes'
              % (self.n, len(self.loops), len(self.prox), tm, self.wm))


def main():
    rclpy.init()
    node = RtabStats()
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
