# Run the course simulations on your own computer

Everything runs in Docker containers that already contain the simulators, ROS 2 and the course code. Nothing
else is installed on your computer.

| Image | For | Needs | Download |
|---|---|---|---|
| `abdulmannan617/tc70045e-ros2:humble` | mobile robot: Gazebo, RViz, ROS 2 (Weeks 1-9, 12) | any 64-bit laptop, 8 GB RAM, 25 GB disk | 3.5 GB |
| `abdulmannan617/tc70045e-drone:latest` | drone: AirSim + PX4 + ROS 2 (Week 11) | Linux + NVIDIA GPU (6 GB+), 60 GB disk | 10.7 GB (7 GB if you already have the mobile-robot image) |
| `abdulmannan617/tc70045e-carla:latest` | self-driving car: CARLA + ROS 2 (Week 10) | Linux + NVIDIA GPU (8 GB+), 80 GB disk | 10.8 GB (7 GB if you already have the mobile-robot image) |

No NVIDIA GPU, or Windows/macOS for the drone and car? Use a rented GPU computer: [RUN_ON_VAST.md](RUN_ON_VAST.md).
(The drone and car images share their lower layers with the mobile-robot image, so they download faster once
you have it.)

## 1. Install Docker (once)

* **Windows / macOS**: install *Docker Desktop* and start it. On Windows it uses WSL 2 (the installer offers it).
* **Linux**: install Docker Engine (<https://docs.docker.com/engine/install/>). For the GPU images also install
  the NVIDIA driver and the *NVIDIA Container Toolkit*
  (<https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html>), then check:
  `docker run --rm --gpus all ubuntu nvidia-smi` must print your GPU.

## 2. Start a container

**Simplest (one command, nothing else needed):**

```bash
docker run -d --name tc70045e -p 6080:80 --shm-size 2g --security-opt seccomp=unconfined \
    -e USER=ubuntu -e RESOLUTION=1600x900 abdulmannan617/tc70045e-ros2:humble
```

GPU images: add `--gpus all` and change the image name, for example

```bash
docker run -d --name tc70045e-drone --gpus all -p 6081:80 --shm-size 4g --security-opt seccomp=unconfined \
    -e USER=ubuntu -e RESOLUTION=1600x900 abdulmannan617/tc70045e-drone:latest
```

**With a clone of the repository (keeps your edits on your own disk):**

```bash
git clone https://github.com/abdul-mannan-khan/TC70045E-robotics-sim.git
cd TC70045E-robotics-sim/docker
docker compose up -d ros2                       # mobile robot
docker compose --profile gpu up -d drone        # drone       (NVIDIA GPU)
docker compose --profile gpu up -d carla        # car         (NVIDIA GPU)
```

## 3. Open the desktop

Browser: **<http://localhost:6080>** (drone 6081, car 6082 with compose). Password `ubuntu`. Open a terminal from
the desktop. The course code is at `~/labs`; each week's README says what to run.

## 4. Stop and start again

```bash
docker stop tc70045e        # your files inside the container are kept
docker start tc70045e       # continue later
docker rm -f tc70045e       # delete the container (files inside it are lost - see Week 1)
```

With compose: `docker compose --profile gpu down` (your work in the cloned folder stays).
