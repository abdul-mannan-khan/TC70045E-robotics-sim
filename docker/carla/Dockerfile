# TC70045E self-driving-car image: the module desktop (ROS 2 Humble, RViz, course code) + the CARLA 0.9.15 simulator
# + the CARLA Python API (no ROS) + the CARLA ROS 2 bridge (ROS 2 route). Needs an NVIDIA GPU (8 GB or more).
# Build from the repository root:
#   docker build -f docker/carla/Dockerfile -t abdulmannan617/tc70045e-carla:latest .
ARG BASE=abdulmannan617/tc70045e-ros2:core
FROM carlasim/carla:0.9.15 AS carla
FROM ${BASE}

SHELL ["/bin/bash", "-lc"]

# CARLA server (Unreal Engine 4 build with Towns 01-05 and 10HD). HDMaps (point-cloud maps) are left out.
COPY --from=carla --chown=1000:1000 /home/carla/CarlaUE4    /opt/carla/CarlaUE4
COPY --from=carla --chown=1000:1000 /home/carla/Engine      /opt/carla/Engine
COPY --from=carla --chown=1000:1000 /home/carla/Plugins     /opt/carla/Plugins
COPY --from=carla --chown=1000:1000 /home/carla/PythonAPI   /opt/carla/PythonAPI
COPY --from=carla --chown=1000:1000 /home/carla/CarlaUE4.sh /home/carla/VERSION /home/carla/LICENSE /opt/carla/

# Vulkan (CARLA renders with Vulkan through the NVIDIA driver, which the NVIDIA runtime mounts in).
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      libvulkan1 vulkan-tools libsdl2-2.0-0 libxrandr2 libxinerama1 libxcursor1 libxi6 libomp5 xdg-user-dirs \
      ros-humble-ackermann-msgs ros-humble-derived-object-msgs ros-humble-pcl-conversions \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /usr/share/vulkan/icd.d \
 && printf '{"file_format_version":"1.0.0","ICD":{"library_path":"libGLX_nvidia.so.0","api_version":"1.3"}}\n' \
      > /usr/share/vulkan/icd.d/nvidia_icd.json
ENV NVIDIA_DRIVER_CAPABILITIES=all NVIDIA_VISIBLE_DEVICES=all

# CARLA Python API for Python 3.10 (the image's CARLA folder only ships 2.7/3.7 wheels; PyPI has the 3.10 one),
# pygame for the viewer windows, and what the example scripts and the ROS 2 bridge import.
RUN pip3 install --no-cache-dir "carla==0.9.15" pygame "numpy<2" networkx shapely transforms3d simple-pid \
 && python3 -c "import carla; print('carla client', carla.__file__)"

# CARLA ROS 2 bridge (official carla-simulator/ros-bridge, built for Humble). Its version check is told that the
# server is 0.9.15. Installed to /opt/carla_ros_bridge and sourced in every terminal.
RUN source /opt/ros/humble/setup.bash \
 && mkdir -p /opt/carla_ros_bridge/src && cd /opt/carla_ros_bridge/src \
 && git clone --depth 1 --recurse-submodules https://github.com/carla-simulator/ros-bridge.git \
 && echo 0.9.15 > ros-bridge/carla_ros_bridge/src/carla_ros_bridge/CARLA_VERSION \
 && rm -rf ros-bridge/carla_ad_demo ros-bridge/carla_ad_agent ros-bridge/rviz_carla_plugin ros-bridge/carla_twist_to_control/test \
      ros-bridge/pcl_recorder \
 && cd /opt/carla_ros_bridge \
 && colcon build --install-base /opt/carla_ros_bridge/install --cmake-args -DCMAKE_BUILD_TYPE=Release \
 && rm -rf build log \
 && echo 'source /opt/carla_ros_bridge/install/setup.bash' >> /etc/profile.d/tc70045e.sh \
 && echo 'source /opt/carla_ros_bridge/install/setup.bash' >> /etc/bash.bashrc

COPY docker/carla/carla-sim /usr/local/bin/carla-sim
RUN chmod 755 /usr/local/bin/carla-sim

# The course code (same as in the mobile-robot image) - last, so code changes do not rebuild the simulator layers.
COPY --chown=1000:1000 . /home/ubuntu/labs

LABEL org.opencontainers.image.title="TC70045E self-driving car simulation (CARLA 0.9.15 + ROS 2)" \
      org.opencontainers.image.source="https://github.com/abdul-mannan-khan/TC70045E-robotics-sim"
