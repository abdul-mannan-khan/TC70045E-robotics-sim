# Week 02 (previous edition) – Expansion-Board Electronics and Embedded Interfaces

> **Note.** This was Week 2 before October 2026. It is kept as an optional extra lab (buck ripple, I²C,
> UART bridge, CAN, SBUS). Paths below now start with `week02/electronics_lab/`. The current Week 2 is in `../README.md`.

Laboratories A–C run in the module's ROS 2 Humble container (ngspice, pyserial and python-can are installed there).
The Gazebo simulator is **not** needed this week – stop it if it is still running, because Lab B also uses `/cmd_vel`.
Laboratory D (KiCad) runs natively on your laptop.

```bash
cd ../docker && docker compose up -d ros2     # then open http://localhost:6080 and a terminal in that desktop
```

| What | Where | Run it (inside the container) | Expected output (21 Sep 2026) |
|---|---|---|---|
| Buck converter netlist (Lab A) | [`spice/buck.cir`](spice/buck.cir) | `ngspice -b ~/labs/week02/electronics_lab/spice/buck.cir \| grep -E "^(vout_avg\|vripple\|iripple\|iload)"` | 12 → 5 V, 500 kHz, 22 µH, 100 µF / 30 mΩ: Vout 4.964 V, ripple 7.92 mV (hand sum 8.6 mV), ΔI_L 0.265 A |
| Ripple against component choice | [`scripts/buck_sweep.py`](scripts/buck_sweep.py) | `python3 ~/labs/week02/electronics_lab/scripts/buck_sweep.py` (or add `esr=10m cval=47u`) | 7 cases, ~30 s: doubling C 7.92 mV (no change), half ESR 4.00 mV, ceramic 0.98 mV, ceramic + 5 nH ESL 3.58 mV, 1 MHz 3.96 mV |
| I²C rise-time netlist | [`spice/i2c_rise.cir`](spice/i2c_rise.cir) | `ngspice -b ~/labs/week02/electronics_lab/spice/i2c_rise.cir \| grep -E "^(vlow\|t30\|t70\|trise)"` | 4.7 kΩ, 200 pF: t_r = 797 ns (0.8473 R C = 796 ns) |
| Rise-time sweep and your own bus | [`scripts/i2c_rise.py`](scripts/i2c_rise.py) | `python3 ~/labs/week02/electronics_lab/scripts/i2c_rise.py`, `--probe 10p`, `--mystery <student number>`, `--reveal` | 16-row table with fast/standard/sink verdicts; a 10 pF probe adds 40 ns at 4.7 kΩ; e.g. bus 21012345: Rp 3.3 kΩ, t_r 483.9 ns → C_b 173 pF |
| UART bridge to the virtual microcontroller (Lab B) | [`scripts/mcu_bridge.py`](scripts/mcu_bridge.py) | terminal 1: `ros2 run tc70045e_sim virtual_mcu`; terminal 2: `python3 ~/labs/week02/electronics_lab/scripts/mcu_bridge.py` | topics `/mcu/imu` (50.0 Hz), `/mcu/vel`, `/mcu/encoders` (25 Hz), `/mcu/voltage` (1 Hz); report every 5 s: 1657 B/s = 14.4 % of the link |
| CAN frames and arbitration (Lab C) | [`scripts/can_frame.py`](scripts/can_frame.py) | `python3 ~/labs/week02/electronics_lab/scripts/can_frame.py` (or `0x123:1122 0x120:00 0x7FF: --bitrate 500000`) | 8-byte frame 121 bits (10 stuff bits), 121 µs at 1 Mbit/s; 0x120 wins |
| CAN bit timing | [`scripts/can_bittiming.py`](scripts/can_bittiming.py) | `python3 ~/labs/week02/electronics_lab/scripts/can_bittiming.py` (`--bitrate 500e3 --sp 0.75`) | 36 MHz, 1 Mbit/s: BRP 2/3/4 with 18/12/9 quanta; 40 m at a 75 % sample point |
| Virtual CAN bus with a filter | [`scripts/can_bus_demo.py`](scripts/can_bus_demo.py) | `python3 ~/labs/week02/electronics_lab/scripts/can_bus_demo.py` | filter 0x100/0x7F0 passes 0x101, 0x102 only; bus load 2.49 % at 1 Mbit/s, 19.9 % at 125 kbit/s |
| SBUS decoder | [`scripts/sbus_decode.py`](scripts/sbus_decode.py) | write your own `sbus_channels()` first, then `python3 ~/labs/week02/electronics_lab/scripts/sbus_decode.py` | zeros, the known frame [172, 992, 1811, ...], 1000 round trips PASS, 17 ms worst-case latency |

## Lab B – raw bytes and error injection

```bash
timeout 1 cat /tmp/ttyMCU | od -An -tx1 | head -6      # before starting the bridge: one reader per port
ros2 topic pub -r 5 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: 0.5}}"
# Ctrl-C the bridge and virtual_mcu, then restart both with errors injected:
ros2 run tc70045e_sim virtual_mcu --ros-args -p bit_error_rate:=1e-3
python3 ~/labs/week02/electronics_lab/scripts/mcu_bridge.py
```

Measured over 60 s with a 5 Hz `/cmd_vel` stream: at 1e-3, 624 bad checksums, frame rates SPEED 23 / IMU 46 /
ENCODER 21 per second (theory (1-p)^(8N): 22.9 / 43.6 / 21.1); at 1e-2, 2977 bad checksums and **7 corrupted SPEED
frames accepted** plus frames with non-existent FUNC codes 0x03/0x08/0x0F – the 8-bit additive checksum's blind spot.
After restarting `virtual_mcu`, restart the bridge too: `/tmp/ttyMCU` then points to a new pseudo-terminal.

`commands.md` lists the lecture's commands in order.
