#!/usr/bin/env python3
"""gzview.py EX EY EZ TX TY TZ - put the Gazebo window's camera at eye E looking at target T (demo videos)."""
import math, subprocess, sys
ex, ey, ez, tx, ty, tz = map(float, sys.argv[1:7])
dx, dy, dz = tx - ex, ty - ey, tz - ez
yaw = math.atan2(dy, dx); pitch = math.atan2(-dz, math.hypot(dx, dy))
cy, sy, cp, sp = math.cos(yaw / 2), math.sin(yaw / 2), math.cos(pitch / 2), math.sin(pitch / 2)
q = (cy * cp, -sy * sp, cy * sp, sy * cp)   # w x y z for roll 0
msg = 'position {x: %g y: %g z: %g} orientation {w: %g x: %g y: %g z: %g}' % (ex, ey, ez, *q)
world = sys.argv[7] if len(sys.argv) > 7 else 'tc70045e_lab'
subprocess.run(['gz', 'topic', '-p', '/gazebo/%s/user_camera/joy_pose' % world, '-m', msg], check=False)
