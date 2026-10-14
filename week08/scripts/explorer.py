#!/usr/bin/env python3
"""explorer.py - frontier exploration: the robot maps an unknown building by itself (Week 8, YOUR ACTIVITY).

Three TODOs (search for TODO); the README explains each one. As given, it finds no frontier at all.

Loop (every goal):
  1. map       read /map (slam_toolbox): -1 unknown, 0 free, 100 occupied
  2. frontier  a FREE cell next to an UNKNOWN cell: the edge of what the robot knows      (TODO 1)
  3. clusters  frontier cells that touch form one frontier; ignore tiny ones (< min_size cells)
  4. choose    the frontier with the best score: big and near                            (TODO 2)
  5. go        send its middle cell to Nav2; every goal tried (reached or failed) is remembered: a frontier
               next to one is not chosen again (it may lie behind something the laser cannot see past)  (TODO 3)
  6. repeat    until no frontier is left, or the time limit
At the end it prints the time, the distance driven, the number of goals and the explored area.

Usage (explore.launch.py running, in a second terminal):
  python3 ~/labs/week08/scripts/explorer.py --ros-args -p use_sim_time:=true
  ... -p min_size:=8 -p distance_weight:=1.0 -p time_limit:=600.0
"""
import math
import time

import cv2
import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from nav_msgs.msg import OccupancyGrid
from rclpy.duration import Duration
from tf2_ros import Buffer, TransformListener


class Explorer(BasicNavigator):
    def __init__(self):
        super().__init__('explorer')
        p = self.declare_parameter
        self.min_size = p('min_size', 8).value               # cells (0.05 m): smaller frontiers are noise
        self.k = p('distance_weight', 1.0).value              # score = size_m - k * distance_m
        self.time_limit = p('time_limit', 600.0).value        # s of simulated time
        self.goal_timeout = p('goal_timeout', 60.0).value
        self.map = None
        self.tried = []                                       # goals already sent (reached or failed)
        self.tf = Buffer()
        TransformListener(self.tf, self)
        self.create_subscription(OccupancyGrid, '/map', lambda m: setattr(self, 'map', m), 1)

    # ---------------------------------------------------------------------------------------------------------------
    def frontiers(self):
        """Return a list of (size, x, y) in metres for every frontier of at least min_size cells."""
        m = self.map
        g = np.array(m.data, dtype=np.int16).reshape(m.info.height, m.info.width)
        free = g == 0
        unknown = g == -1
        # TODO 1: a frontier cell is FREE and has an UNKNOWN neighbour (up, down, left or right).
        #   Build a boolean array near_unknown (True where a neighbour is unknown) by shifting `unknown` one cell
        #   in each direction, e.g. near_unknown[1:, :] |= unknown[:-1, :]   (the cell above is unknown).
        frontier = np.zeros_like(free)
        n, lab, stats, _ = cv2.connectedComponentsWithStats(frontier.astype(np.uint8), connectivity=8)
        out = []
        res, ox, oy = m.info.resolution, m.info.origin.position.x, m.info.origin.position.y
        for i in range(1, n):
            if stats[i, cv2.CC_STAT_AREA] < self.min_size:
                continue
            rows, cols = np.nonzero(lab == i)
            k = len(rows) // 2                               # a frontier cell in the middle of the cluster
            order = np.lexsort((cols, rows))
            r, c = rows[order[k]], cols[order[k]]
            out.append((stats[i, cv2.CC_STAT_AREA] * res, ox + (c + 0.5) * res, oy + (r + 0.5) * res))
        return out

    def robot(self, wait=1.0):
        """The robot's position on the map (TF map -> base_footprint), or None if SLAM has not published it yet."""
        try:
            tr = self.tf.lookup_transform('map', 'base_footprint', rclpy.time.Time(), timeout=Duration(seconds=wait))
        except Exception:
            return None
        return tr.transform.translation.x, tr.transform.translation.y

    def choose(self, fronts, rx, ry):
        best, best_score = None, -1e9
        for size, x, y in fronts:
            # TODO 3: skip a frontier within 0.5 m of a goal already tried (self.tried) - otherwise the robot is sent
            #   to the same frontier again and again (one it cannot reach, or one behind something it cannot see past).
            d = math.hypot(x - rx, y - ry)
            score = size                                      # TODO 2: big AND near: use d and self.k
            if score > best_score:
                best, best_score = (x, y), score
        return best

    def explored_area(self):
        g = np.array(self.map.data)
        return np.count_nonzero(g >= 0) * self.map.info.resolution ** 2

    # ---------------------------------------------------------------------------------------------------------------
    def run(self):
        self.waitUntilNav2Active(localizer='controller_server')     # slam_toolbox localises, not AMCL
        last = None
        while self.map is None or last is None:                  # wait for the first map and TF from SLAM
            rclpy.spin_once(self, timeout_sec=0.2)
            last = self.robot(wait=0.5)
        print('map and robot position received - exploring', flush=True)
        t0, goals, dist = self.get_clock().now(), 0, 0.0
        while rclpy.ok():
            if (self.get_clock().now() - t0).nanoseconds * 1e-9 > self.time_limit:
                print('time limit reached', flush=True)
                break
            rclpy.spin_once(self, timeout_sec=0.1)
            here = self.robot()
            if here is None:
                continue
            target = self.choose(self.frontiers(), *here)
            if target is None:
                print('no frontier left: exploration complete', flush=True)
                break
            goals += 1
            p = PoseStamped()
            p.header.frame_id, p.header.stamp = 'map', self.get_clock().now().to_msg()
            p.pose.position.x, p.pose.position.y = target
            p.pose.orientation.w = 1.0
            self.goToPose(p)
            g0 = self.get_clock().now()
            while not self.isTaskComplete():
                rclpy.spin_once(self, timeout_sec=0.1)
                here = self.robot(wait=0.1)
                if here:
                    dist += math.hypot(here[0] - last[0], here[1] - last[1])
                    last = here
                if (self.get_clock().now() - g0).nanoseconds * 1e-9 > self.goal_timeout:
                    self.cancelTask()
            ok = self.getResult() == TaskResult.SUCCEEDED
            self.tried.append(target)
            sec = (self.get_clock().now() - t0).nanoseconds * 1e-9
            print('goal %2d  (%5.2f, %5.2f)  %-9s  t = %4.0f s  explored %5.1f m^2'
                  % (goals, target[0], target[1], 'REACHED' if ok else 'FAILED', sec, self.explored_area()), flush=True)
        sec = (self.get_clock().now() - t0).nanoseconds * 1e-9
        print('RESULT %d goals, %.0f s, %.1f m driven, explored %.1f m^2' % (goals, sec, dist, self.explored_area()),
              flush=True)


def main():
    rclpy.init()
    node = Explorer()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.cancelTask()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
