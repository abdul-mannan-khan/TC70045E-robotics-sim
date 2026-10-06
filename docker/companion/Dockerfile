# TC70045E companion-computer image for the NVIDIA Jetson Orin Nano Super (JetPack 6 = Ubuntu 22.04, arm64).
# It also runs on any amd64 PC, so the same commands can be tried without a Jetson.
#
# What it does in the hardware-in-the-loop (HIL) set-up (docs/HIL_JETSON_PIXHAWK.md):
#   hil-relay      Pixhawk 6C USB (HIL messages)  <-- TCP -->  AirSim in the drone container (lab PC or Vast.ai)
#   mission code   MAVSDK over the Pixhawk TELEM2 UART, AirSim camera images over the network, optional ROS 2
#
# Build (both architectures) from the repository root:
#   docker buildx build --platform linux/arm64,linux/amd64 -f docker/companion/Dockerfile \
#       -t abdulmannan617/tc70045e-companion:latest --push .
FROM ros:humble-ros-base

SHELL ["/bin/bash", "-c"]
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      python3-pip socat wget nano iputils-ping usbutils \
      ros-humble-cv-bridge ros-humble-tf2-ros ros-humble-nav-msgs ros-humble-std-srvs \
 && rm -rf /var/lib/apt/lists/*

# MAVSDK-Python (<4: the gRPC API used in the course), the AirSim Python client (v1.8.1, same as the simulator)
RUN pip3 install --no-cache-dir "mavsdk<4" msgpack-rpc-python "numpy<2" scipy opencv-python-headless pyserial \
 && mkdir -p /tmp/as && cd /tmp/as \
 && wget -q https://github.com/microsoft/AirSim/archive/refs/tags/v1.8.1.tar.gz \
 && tar xzf v1.8.1.tar.gz --strip-components=1 AirSim-1.8.1/PythonClient \
 && cp -r PythonClient/airsim "$(python3 -c 'import site; print(site.getsitepackages()[0])')/airsim" \
 && rm -rf /tmp/as \
 && python3 -c "import airsim, mavsdk, cv2; print('companion python ok')"

COPY examples/airsim /opt/tc70045e/examples/airsim
COPY docker/companion/hil-relay /usr/local/bin/hil-relay
RUN chmod 755 /usr/local/bin/hil-relay \
 && echo 'source /opt/ros/humble/setup.bash' >> /etc/bash.bashrc
WORKDIR /opt/tc70045e/examples/airsim

LABEL org.opencontainers.image.title="TC70045E companion computer (Jetson Orin Nano Super + Pixhawk 6C HIL)" \
      org.opencontainers.image.source="https://github.com/abdul-mannan-khan/TC70045E-robotics-sim"
CMD ["bash"]
