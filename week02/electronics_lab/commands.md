# Week 02 – commands and code from the lecture, in order

Generated from the lecture (Week 2: Expansion-Board Electronics and Embedded Interfaces – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 2.1 Worked example: the 5 V rail

```text
D      = 5 / 12                     = 0.417
dI_L   = 5 x (1 - 0.417)
         / (22e-6 x 500e3)          = 0.265 A pk-pk
dV_cap = 0.265
         / (8 x 500e3 x 100e-6)     = 0.66 mV
dV_esr = 0.265 x 0.030              = 7.95 mV
                                      ------------
dV_out = 0.66 + 7.95                = 8.6 mV pk-pk
```

## 3.1 Sizing the pull-ups

```text
R_p,min = (3.3 - 0.4) / 0.003        = 967 ohm

Standard mode (100 kHz, t_r <= 1000 ns), C_b = 200 pF
R_p,max = 1000e-9 / (0.8473 x 200e-12)  = 5.90 kohm

Fast mode (400 kHz, t_r <= 300 ns), C_b = 200 pF
R_p,max =  300e-9 / (0.8473 x 200e-12)  = 1.77 kohm

Fast mode, shorter bus, C_b = 100 pF
R_p,max =  300e-9 / (0.8473 x 100e-12)  = 3.54 kohm
```

```bash
# ---- terminal (inside the browser desktop) ----
ngspice -b ~/labs/week02/electronics_lab/spice/buck.cir | grep -E "^(vout_avg|vripple|iripple|iload)"
python3 ~/labs/week02/electronics_lab/scripts/buck_sweep.py
python3 ~/labs/week02/electronics_lab/scripts/buck_sweep.py esr=10m cval=47u
```

```text
vout_avg            =  4.963660e+00 from=  2.980000e-03 to=  3.000000e-03
vripple             =  7.919539e-03 from=  2.980000e-03 to=  3.000000e-03
iripple             =  2.650240e-01 from=  2.980000e-03 to=  3.000000e-03
iload               =  9.928159e-01 from=  2.980000e-03 to=  3.000000e-03
```

```text
case                        dI hand     dV_C   dV_ESR      sum |   dI sim    ripple     Vout
                                  A       mV       mV       mV |        A    mV sim        V
baseline (electrolytic)       0.265     0.66     7.95     8.62 |    0.265      7.92    4.964
double the capacitance        0.265     0.33     7.95     8.29 |    0.265      7.92    4.964
halve the ESR                 0.265     0.66     3.98     4.64 |    0.265      4.00    4.964
ceramic, ESR 3 mOhm           0.265     0.66     0.80     1.46 |    0.265      0.98    4.964
ceramic + 5 nH ESL            0.265     0.66     0.80     1.46 |    0.265      3.58    4.964
fsw = 1 MHz                   0.133     0.17     3.98     4.14 |    0.133      3.96    4.959
light load 0.1 A              0.265     0.66     7.95     8.62 |    0.265      8.13    4.991
```

```bash
# ---- I2C: one run, the sweep, the probe, then YOUR bus ----
ngspice -b ~/labs/week02/electronics_lab/spice/i2c_rise.cir | grep -E "^(vlow|t30|t70|trise)"
python3 ~/labs/week02/electronics_lab/scripts/i2c_rise.py
python3 ~/labs/week02/electronics_lab/scripts/i2c_rise.py --probe 10p
python3 ~/labs/week02/electronics_lab/scripts/i2c_rise.py --mystery 21012345      # your number
python3 ~/labs/week02/electronics_lab/scripts/i2c_rise.py --mystery 21012345 --reveal
```

```text
     Rp      Cb |  t_r hand   t_r sim |  I_sink   V_OL | verdict
  1.0k    200p |     169 ns     169 ns |  3.22 mA   80 mV | fast mode OK, sink > 3 mA!
  2.2k    100p |     186 ns     186 ns |  1.48 mA   37 mV | fast mode OK
  2.2k    200p |     373 ns     373 ns |  1.48 mA   37 mV | standard only
  4.7k    100p |     398 ns     398 ns |  0.70 mA   17 mV | standard only
  4.7k    200p |     796 ns     797 ns |  0.70 mA   17 mV | standard only
  4.7k    400p |    1593 ns    1594 ns |  0.70 mA   17 mV | TOO SLOW
   (extract of 16 rows; with --probe 10p the 4.7k/100p row becomes 438 ns)
bus 21012345: pull-up Rp = 3.3 kohm, VDD = 3.3 V, probe 0 F
measured 30-70 % rise time t_r = 483.9 ns,  low level V_OL = 24.8 mV
```

## 5.1 The clock tree, and why 72 MHz is not arbitrary

```text
HSE 8 MHz crystal
      |
      +-- PLL x9 --> SYSCLK 72 MHz
                        |
                        +-- AHB  /1 --> HCLK 72 MHz
                              |
                              +-- APB2 /1 --> 72 MHz
                              |      USART1, GPIO, ADC
                              |
                              +-- APB1 /2 --> 36 MHz
                                     USART2, CAN, TIM2-4
```

## 6.1 UART: the host link at 115200 8N1

```text
USART1 on APB2 at 72 MHz, target 115200 baud:
  USARTDIV = 72e6 / (16 x 115200) = 39.0625
  mantissa 39, fraction 0.0625 x 16 = 1  -> exact
  actual baud = 115200,   error = 0.00 %

Same target from the 8 MHz internal RC oscillator:
  USARTDIV = 8e6 / (16 x 115200) = 4.3403
  nearest representable 4.3125
  actual = 8e6 / (16 x 4.3125) = 115942   error = +0.64 %
  plus the oscillator's own +/- 1 % over temperature
```

## 6.2 Framing, link budget and error detection

```text
0xFF 0xFB | LEN | FUNC | PAYLOAD ... | CHECKSUM
LEN      = number of bytes after LEN (FUNC + PAYLOAD + CHECKSUM)
CHECKSUM = (LEN + FUNC + sum(PAYLOAD)) mod 256

report     FUNC  payload            bytes  rate    bytes/s
IMU        0x0B  6 x int16            17   50 Hz     850
SPEED      0x0A  3 x int16            11   25 Hz     275
ENCODER    0x0D  4 x int32            21   25 Hz     525
BATTERY    0x0C  1 x uint16            7    1 Hz       7
                                            total   1657 B/s
utilisation = 1657 x 10 bits / 115200 = 14.4 %
```

## 6.3 CAN: 1 Mbit s⁻¹, differential, arbitrated

```text
1 Mbit/s: t_bit = 1 us; sample point 75 % -> 750 ns
minus 2 x 175 ns of transceiver delay -> 400 ns for the cable
twisted pair: about 5 ns/m

   2 x L x 5e-9  <=  400e-9   ->   L <= 40 m
```

## 6.4 SBUS: 100 kbaud, 8E2, inverted

```text
Frame: 0x0F [22 data bytes] [flags] 0x00      = 25 bytes
Channels: 16 x 11 bits = 176 bits = 22 bytes, LSB first
          values 0..2047 (sticks use about 172..1811)
flags: bit 2 frame lost, bit 3 failsafe

Byte time  = 1 start + 8 data + 1 parity + 2 stop
           = 12 bit times = 120 us
Frame time = 25 x 120 us = 3.0 ms
Period 14 ms (7 ms high-speed) -> worst case 17 ms
```

## 6.5 Choosing a bus for a sensor

```bash
# ---- terminal 1: the virtual microcontroller (simulator NOT needed) ----
ros2 run tc70045e_sim virtual_mcu
# ---- terminal 2: one second of raw bytes ----
timeout 1 cat /tmp/ttyMCU | od -An -tx1 | head -6
```

```text
 ff fb 0e 0b 0f 00 0b 00 f6 ff 1e 00 05 00 ca 03
 18 ff fb 0e 0b 02 00 00 00 f6 ff 02 00 00 00 e2
 03 f7 ff fb 08 0a 00 00 00 00 00 00 12 ff fb 12
 0d 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
 00 1f ff fb 0e 0b 0f 00 f1 ff f6 ff fd ff f6 ff
```

```python
def feed(self, data):
    self.buf += data
    frames = []
    while True:
        i = self.buf.find(HEAD)                  # b'\xff\xfb'
        if i < 0:                                # keep last byte: may be 0xFF
            self.skipped += max(len(self.buf) - 1, 0)
            del self.buf[:-1]
            return frames
        self.skipped += i
        del self.buf[:i]
        if len(self.buf) < 3:
            return frames
        ln = self.buf[2]
        if not 2 <= ln <= 40:                    # impossible length: false header
            self.skipped += 1
            del self.buf[:1]
            continue
```

```text
        if len(self.buf) < 3 + ln:
            return frames                        # wait for the rest
        func, payload = self.buf[3], bytes(self.buf[4:2 + ln])
        cs = self.buf[2 + ln]
        if (ln + func + sum(payload)) & 0xFF != cs:
            self.bad += 1
            del self.buf[:1]                     # resync one byte on
            continue
        del self.buf[:3 + ln]
        frames.append((func, payload))
```

```bash
# ---- terminal 2: the bridge ----
python3 ~/labs/week02/electronics_lab/scripts/mcu_bridge.py
# ---- terminal 3: topics, rates, a command ----
ros2 topic list | grep mcu
ros2 topic hz /mcu/imu
ros2 topic echo /mcu/voltage --once
ros2 topic pub -r 5 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: 0.5}}"
# ---- terminal 4, while the command runs ----
ros2 topic echo /mcu/vel --once
ros2 topic echo /mcu/encoders --once
```

```text
[INFO] [...] [mcu_bridge]: SPEED 25.1/s  IMU 50.2/s  BATTERY 1.0/s  ENCODER 25.1/s |
1662 B/s = 14.4 % of the link | bad checksum 0 | skipped bytes 0 |
wrong-but-accepted SPEED 0                       (one report, line-wrapped)
$ ros2 topic hz /mcu/imu
average rate: 49.999
	min: 0.007s max: 0.033s std dev: 0.00155s window: 304
```

```text
$ ros2 topic echo /mcu/vel --once
linear:
  x: 0.2
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.5
---
```

```bash
# ---- error injection: Ctrl-C the bridge and the microcontroller, then ----
ros2 run tc70045e_sim virtual_mcu --ros-args -p bit_error_rate:=1e-3     # terminal 1
python3 ~/labs/week02/electronics_lab/scripts/mcu_bridge.py                              # terminal 2
ros2 topic pub -r 5 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}}"  # terminal 3
#   read two reports, then repeat everything with bit_error_rate:=1e-2
```

```text
last report after 60 s, line-wrapped (the counters are cumulative):
p = 1e-3: SPEED 23.1/s  IMU 45.8/s  BATTERY 1.0/s  ENCODER 21.1/s | 1665 B/s = 14.5 %
          of the link | bad checksum 624 | skipped bytes 11516 | wrong-but-accepted SPEED 0
p = 1e-2: 0x3 0.0/s  0x8 0.2/s  SPEED 10.2/s  IMU 12.5/s  BATTERY 0.6/s  ENCODER 4.4/s
          0xf 0.0/s | 1665 B/s = 14.5 % of the link | bad checksum 2977 |
          skipped bytes 63620 | wrong-but-accepted SPEED 7
```

```bash
python3 ~/labs/week02/electronics_lab/scripts/can_frame.py
python3 ~/labs/week02/electronics_lab/scripts/can_frame.py 0x123:1122 0x120:00 0x7FF: --bitrate 500000
python3 ~/labs/week02/electronics_lab/scripts/can_bittiming.py
python3 ~/labs/week02/electronics_lab/scripts/can_bittiming.py --bitrate 500e3 --sp 0.75
python3 ~/labs/week02/electronics_lab/scripts/can_bus_demo.py
python3 ~/labs/week02/electronics_lab/scripts/sbus_decode.py
```

```text
ID     data                bits  stuff  CRC15     time
0x1A0  0102030405060708     121     10 0x0B77  121.0 us
0x123  ff00                  67      4 0x33EA   67.0 us
0x120  00                    58      3 0x2879   58.0 us
0x7FF  -                     50      3 0x272F   50.0 us

Arbitration (all nodes start at the same SOF; bus level = AND of the transmitted bits):
  bit  1 after SOF: bus=0, node 0x7FF sent 1 -> loses arbitration, becomes a receiver
  bit  4 after SOF: bus=0, node 0x1A0 sent 1 -> loses arbitration, becomes a receiver
  bit 10 after SOF: bus=0, node 0x123 sent 1 -> loses arbitration, becomes a receiver
winner: 0x120  (it never noticed the contest - the frame was not corrupted)
```

```text
 BRP    N  t_q ns  TSEG1  TSEG2  SJW    SP % | registers          |   L max
   2   18    55.6     15      2    2    88.9 | BRP=1 TS1=14 TS2=1 |    54 m
   3   12    83.3      9      2    2    83.3 | BRP=2 TS1=8 TS2=1 |    48 m
   4    9   111.1      7      1    1    88.9 | BRP=3 TS1=6 TS2=0 |    54 m
```

```text
ID     meaning          sent  rx (all)  rx (filtered)     bits
0x080  emergency stop     20        20              0       58
0x101  wheel speeds      200       200            200      121
0x102  motor currents    200       200            200      121
0x300  battery status      2         2              0       86
bus load at 1 Mbit/s: 24866 bit/s = 2.49 %   (at 125 kbit/s: 19.9 %)
```

```text
1) all-zero frame  -> [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
2) known frame     -> [172, 992, 1811, 992, 992, 992] ...  flags 0x08: failsafe=1 frame_lost=0
3) 1000 random frames round-trip: PASS
4) header 0x0F on the wire (inverted 8E2, start..stop): 100001111100
5) byte 120 us, frame 3.0 ms; with a 14 ms period worst-case latency = 17 ms (7 ms mode: 10 ms)
```

## 9.2 Sizing the shunt and the current-sense IC – the derivation you must show

```text
Full scale   I_max = 5 A;   trial shunt R_sh = 0.010 ohm

  V_sh = I_max x R_sh = 5 x 0.010   = 50 mV
     -> inside the +/-320 mV range, using 50/320 = 16 % of it
  P    = I^2 R = 25 x 0.010         = 0.25 W
     -> a 2512 (1 W) part, running warm
  LSB  = I_max / 2^15 = 5 / 32768   = 152.6 uA
     -> round up to 200 uA: 0.2 mA resolution, meets the spec
  CAL  = 0.04096 / (LSB x R_sh)
       = 0.04096 / (200e-6 x 0.010) = 20480
```

## 9.3 The KiCad workflow for today

```text
Schematic checklist
  [ ] every symbol annotated, no duplicate references
  [ ] every symbol has a footprint
  [ ] rails drawn with power symbols, PWR_FLAG where a rail enters by a connector
  [ ] one 100 nF per device supply pin; bulk capacitor at the power entry
  [ ] Kelvin sense connections drawn to the shunt pads
  [ ] I2C addresses chosen, distinct, written on the sheet
  [ ] pull-ups shown, marked fitted or not fitted, and why
  [ ] protection on the user-accessible header
  [ ] title block: name, module code, date, revision
  [ ] ERC: 0 errors
```

## 🤖 AI co-pilot: the "propose, then prove against the datasheet" pattern

```text
You are a hardware engineer reviewing a component choice. Do not assert any
number you cannot tie to a named datasheet parameter; where unsure, say
"check the datasheet" instead of guessing.

DESIGN CONTEXT (my own analysis)
  Host bus: I2C on a mobile-robot microcontroller board, 3.3 V pull-ups
  Pull-up: 3.3 kohm   simulated rise time: ____ ns   C_b: ____ pF
  Rail to monitor: 5 V, 0-5 A continuous, 3.3 A typical
  Constraint: shunt dissipation <= 0.5 W, 2512, two layers, <= 40 x 30 mm

TASK
1. Propose THREE current-sense options (different architectures). For each:
   shunt value, full-scale shunt voltage, dissipation, resolution in mA,
   I2C address range, supply range.
2. Tabulate them against my constraints and name the one you would choose.
3. For that part, show the calibration calculation symbolically, then
   numerically, and name the datasheet section to check it against.
4. List every assumption you made that my context did not give you.

OUTPUT: one table, then at most 150 words. No part number without a manufacturer.
```
