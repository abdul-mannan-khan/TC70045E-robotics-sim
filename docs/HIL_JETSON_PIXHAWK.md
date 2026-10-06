# Hardware in the loop: AirSim + Jetson Orin Nano Super + Pixhawk 6C

In **software in the loop (SITL)** the autopilot is a program inside the drone container. In **hardware in the
loop (HIL)** the autopilot is the real **Pixhawk 6C** flight controller running PX4. AirSim still provides the
world, the physics and the sensors: it sends the Pixhawk simulated IMU, GPS, barometer and magnetometer readings,
and the Pixhawk sends back its motor commands. The **Jetson Orin Nano Super** is the companion computer, as on
a real drone. It runs your mission code and relays the Pixhawk's USB link to AirSim.

> **Status:** the software side (containers, relay, settings, scripts) is built and checked. The complete loop
> with a physical Pixhawk 6C and Jetson has **not been flown yet**. Do the bench test (section 4) first.

## 1. What is connected to what

```
 Jetson Orin Nano Super (container tc70045e-companion)            Computer with a GPU (container tc70045e-drone)
 ┌──────────────────────────────────────────────┐                 ┌───────────────────────────────────────────┐
 │ hil-relay   /dev/ttyACM0 <──── TCP 4570 ────────────────────────>│ socat  ->  /dev/ttyPX4  ->  AirSim (HIL) │
 │ mission     MAVSDK  serial:///dev/ttyTHS0     │   network        │ AirSim API on TCP 41451  (camera images)  │
 │ (optional)  ROS 2 nodes, camera via AirSim API <─── TCP 41451 ───│                                           │
 └──────┬───────────────────────┬───────────────┘                 └───────────────────────────────────────────┘
        │ USB (HIL messages)    │ UART: TELEM2 (MAVLink, mission commands)
 ┌──────┴───────────────────────┴───────┐
 │ Pixhawk 6C  - PX4 v1.14.3, HIL mode    │   no propellers, no motors needed
 └────────────────────────────────────────┘
```

* **USB** Pixhawk → Jetson carries the HIL messages. The Jetson forwards them, unchanged, to the drone container.
* **TELEM2** Pixhawk → Jetson UART carries ordinary MAVLink. The mission code talks to the autopilot through it,
  exactly as on a real drone.
* The GPU computer can be a **lab PC on the same network** (best: low, steady delay) or a **Vast.ai instance**
  (works over the internet; delay of 20-60 ms makes control less smooth).

## 2. One-off set-up of the Pixhawk 6C (QGroundControl on any laptop)

1. Flash PX4 **v1.14.3** (`px4_fmu-v6c_default`): *Vehicle Setup → Firmware*. The course pairs AirSim 1.8.1 with
   PX4 1.14 (the same version as the SITL autopilot in the drone container); keep both the same.
2. *Vehicle Setup → Airframe*: **HIL Quadcopter X** (`SYS_AUTOSTART = 1001`). Reboot.
3. *Safety → HITL Enabled* (`SYS_HITL = 1`). Reboot.
4. TELEM2 for the Jetson: `MAV_1_CONFIG = TELEM 2`, `MAV_1_MODE = Onboard`, `SER_TEL2_BAUD = 921600`. Reboot.
5. Remove the propellers. In HIL mode PX4 does not drive the real motors, but keep this habit.

## 3. Wiring and Jetson preparation

* Pixhawk **USB-C** → Jetson USB port. On the Jetson it appears as `/dev/ttyACM0` (`ls /dev/ttyACM*`).
* Pixhawk **TELEM2** (JST-GH 6-pin: TX, RX, GND) → Jetson 40-pin header UART: TX→pin 10 (RX), RX→pin 8 (TX),
  GND→pin 6. On the Orin Nano developer kit this UART is `/dev/ttyTHS0` (check with `ls /dev/ttyTHS*`), 3.3 V.
* Jetson: JetPack 6 (Ubuntu 22.04). If `docker --version` fails, install it with `sudo apt install docker.io`. Then pull:

```bash
docker pull abdulmannan617/tc70045e-companion:latest       # arm64 image, ROS 2 Humble + MAVSDK + AirSim client
```

## 4. Run it

**A. GPU computer** (lab PC or Vast.ai, see [RUN_ON_VAST.md](RUN_ON_VAST.md)), in the drone desktop terminal:

```bash
drone-sim start --world blocks --mode hil            # AirSim in HIL mode; waits for the Jetson on TCP 4570
```

If the Pixhawk is plugged **directly into the lab PC** instead (no Jetson relay), start the container with
`--device /dev/ttyACM0` and use `drone-sim start --mode hil --serial /dev/ttyACM0`.

**B. Jetson**, two terminals:

```bash
docker run --rm -it --network host --device /dev/ttyACM0 --device /dev/ttyTHS0 \
    abdulmannan617/tc70045e-companion:latest
hil-relay <GPU-computer-address> 4570                 # lab PC: its LAN address; Vast.ai: IP and mapped port of 4570
```

```bash
docker exec -it $(docker ps -q --filter ancestor=abdulmannan617/tc70045e-companion:latest) bash
python3 02_fly_square_mavsdk.py --url serial:///dev/ttyTHS0:921600 --side 5 --alt 5
```

**Bench test, in this order:** (1) `drone-sim status` on the GPU computer shows the relay running; (2) the AirSim
log `/tmp/drone-sim/airsim.log` shows the vehicle connected; (3) QGroundControl (UDP 14550 on the GPU computer)
shows the attitude moving when AirSim's drone is moved; (4) only then arm and fly the square.

## 5. The same code in all three set-ups

| Set-up | Autopilot | Mission code runs on | MAVSDK address |
|---|---|---|---|
| SITL (default course set-up) | PX4 program in the drone container | the drone container | `udpin://0.0.0.0:14540` |
| HIL | Pixhawk 6C | Jetson (companion container) | `serial:///dev/ttyTHS0:921600` |
| Real flight (outside this module) | Pixhawk 6C | Jetson | `serial:///dev/ttyTHS0:921600` |

Only the address changes. Camera images come from the AirSim API in SITL and HIL
(`airsim.MultirotorClient(ip=<GPU computer>)`), and from a real camera in real flight.

## 6. Ports

| Port | Where | What |
|---|---|---|
| 4570/tcp | drone container | HIL relay from the Jetson |
| 41451/tcp | drone container | AirSim API (camera images, simulator state) |
| 14550/udp | drone container → QGroundControl | ground station view of the Pixhawk |

On Vast.ai open them when you create the instance (`-p 4570:4570 -p 41451:41451`) and read the mapped external
ports from the instance's *IP & port* list. The AirSim API has no password, so close the instance when you finish.
