#!/bin/bash
# Week 3, Lab B - one closed-loop run: a FRESH motor bench (so the load step always comes at the same
# moment) plus pid_speed.py, then wait until the bench has stopped itself.
#
#   bash ~/labs/week03/making_it_move/scripts/bench_run.sh -p kp:=148.0 -p ki:=1290.0 -p out:=simc
#   LOAD=0.0 bash ~/labs/week03/making_it_move/scripts/bench_run.sh -p setpoint:=0.9 ...      (no load step)
#
# Everything after the script name is passed to pid_speed.py as ROS parameters.
# The bench gets a load step of LOAD m/s (default 0.1) 8 s after it starts and stops itself after 16 s.
timeout 16 ros2 run tc70045e_sim motor_bench --ros-args \
    -p load_mps:="${LOAD:-0.1}" -p load_step_s:=8.0 > /dev/null 2>&1 &
python3 "$(dirname "$0")/pid_speed.py" --ros-args "$@"
wait
