# TC70045E drone image: the module desktop (ROS 2 Humble, RViz, course code) + AirSim 1.8.1 + PX4 v1.14.3 SITL.
# Needs an NVIDIA GPU (AirSim is an Unreal Engine 4 game). Build from the repository root:
#   docker build -f docker/drone/Dockerfile -t abdulmannan617/tc70045e-drone:latest .
#
# From the source images only the AirSim environment folders are taken (Microsoft AirSim v1.8.1 release binaries:
# Blocks, Neighborhood; LandscapeMountains). PX4 v1.14.3 is built from source in its own stage below.
ARG BASE=abdulmannan617/tc70045e-ros2:core
FROM abdulmannan617/airsim-landscape-mountains:latest AS mountains
FROM abdulmannan617/sar-airsim:latest AS airsim_bins

# --- PX4 v1.14.3 software-in-the-loop build (only build/px4_sitl_default is kept) ---
# empy is pinned to 3.3.4: the setup script installs empy 4, whose API PX4 1.14's code generator cannot use
# ("module 'em' has no attribute 'RAW_OPT'").
FROM ubuntu:22.04 AS px4build
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends git sudo ca-certificates lsb-release tzdata \
      python3 python3-pip \
 && git clone --depth 1 --branch v1.14.3 --recurse-submodules --shallow-submodules \
      https://github.com/PX4/PX4-Autopilot.git /opt/PX4-Autopilot \
 && cd /opt/PX4-Autopilot \
 && bash Tools/setup/ubuntu.sh --no-nuttx --no-sim-tools \
 && pip3 install --force-reinstall "empy==3.3.4" \
 && DONT_RUN=1 make px4_sitl_default -j"$(nproc)" \
 && test -x build/px4_sitl_default/bin/px4

FROM ${BASE}

SHELL ["/bin/bash", "-lc"]

# AirSim environments: Blocks (light, test map), Neighborhood (urban), LandscapeMountains (open terrain)
COPY --from=airsim_bins /opt/AirSim/LinuxBlocks1.8.1 /opt/AirSim/Blocks
COPY --from=airsim_bins /opt/AirSim/AirSimNH /opt/AirSim/Neighborhood
COPY --from=mountains   /opt/AirSim/LandscapeMountains /opt/AirSim/Mountains
# PX4 v1.14.3 autopilot, built for software-in-the-loop (px4_sitl_default)
COPY --from=px4build /opt/PX4-Autopilot/build/px4_sitl_default /opt/PX4-Autopilot/build/px4_sitl_default

# Runtime libraries for Unreal Engine (Vulkan/OpenGL through the NVIDIA driver), VirtualGL to show the
# simulator window inside the browser desktop, socat for the hardware-in-the-loop serial relay.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      libvulkan1 vulkan-tools mesa-utils libegl1 libgl1 libglu1-mesa libxrandr2 libxinerama1 libxcursor1 \
      libxi6 libxss1 libasound2 libnss3 socat screen wget \
 && wget -q -O /tmp/vgl.deb https://github.com/VirtualGL/virtualgl/releases/download/3.1.1/virtualgl_3.1.1_amd64.deb \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y /tmp/vgl.deb && rm /tmp/vgl.deb \
 && rm -rf /var/lib/apt/lists/*

# Tell the Vulkan and EGL loaders where the NVIDIA driver is (the driver libraries themselves are mounted
# into the container at run time by the NVIDIA runtime, with NVIDIA_DRIVER_CAPABILITIES=all).
RUN mkdir -p /usr/share/vulkan/icd.d /usr/share/glvnd/egl_vendor.d \
 && printf '{"file_format_version":"1.0.0","ICD":{"library_path":"libGLX_nvidia.so.0","api_version":"1.3"}}\n' \
      > /usr/share/vulkan/icd.d/nvidia_icd.json \
 && printf '{"file_format_version":"1.0.0","ICD":{"library_path":"libEGL_nvidia.so.0"}}\n' \
      > /usr/share/glvnd/egl_vendor.d/10_nvidia.json
ENV NVIDIA_DRIVER_CAPABILITIES=all NVIDIA_VISIBLE_DEVICES=all

# AirSim Python client (from the v1.8.1 source tag, the same version as the binaries) and its RPC library.
# MAVSDK-Python (<4, gRPC API) is already in the base image.
RUN pip3 install --no-cache-dir msgpack-rpc-python "numpy<2" \
 && mkdir -p /tmp/as && cd /tmp/as \
 && wget -q https://github.com/microsoft/AirSim/archive/refs/tags/v1.8.1.tar.gz \
 && tar xzf v1.8.1.tar.gz --strip-components=1 AirSim-1.8.1/PythonClient \
 && cp -r PythonClient/airsim /usr/local/lib/python3.10/dist-packages/airsim \
 && rm -rf /tmp/as \
 && python3 -c "import airsim, mavsdk; print('airsim', airsim.__version__)"

# Unreal refuses to run as root, so the simulator runs as the desktop user (uid 1000). The start script and the
# AirSim settings (SITL and HIL variants) are part of the image.
COPY docker/drone/drone-sim /usr/local/bin/drone-sim
COPY docker/drone/settings /opt/tc70045e/airsim_settings
RUN chmod 755 /usr/local/bin/drone-sim \
 && chmod -R a+rX /opt/AirSim /opt/PX4-Autopilot /opt/tc70045e \
 && find /opt/AirSim -name '*.sh' -exec chmod 755 {} +

# The course code (same as in the mobile-robot image) - last, so code changes do not rebuild the simulator layers.
COPY --chown=1000:1000 . /home/ubuntu/labs

LABEL org.opencontainers.image.title="TC70045E drone simulation (AirSim + PX4 + ROS 2)" \
      org.opencontainers.image.source="https://github.com/abdul-mannan-khan/TC70045E-robotics-sim"
