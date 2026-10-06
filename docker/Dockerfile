# TC70045E lab image: ROS 2 Humble desktop in a browser + the simulated lab robot + the packages used in this module.
# Build from the REPOSITORY ROOT (the course code is copied in):  docker build -f docker/Dockerfile -t abdulmannan617/tc70045e-ros2:humble .
# Base image provides a Linux desktop with ROS 2 Humble reachable at http://localhost:6080 (amd64 and arm64).
# Every package below was installed and exercised on a clean ROS 2 Humble container (2026-09-19 and 2026-09-21).
FROM tiryoh/ros2-desktop-vnc:humble AS core

# One BLAS thread per process: on many-core machines every numpy process otherwise starts dozens of threads
# (measured: 64 per process on an 80-core server), which starved the simulator and delayed /cmd_vel by seconds.
ENV OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1

SHELL ["/bin/bash", "-lc"]

# --- ROS 2 packages used by the weekly laboratories -------------------------------------------------
# All weeks  : Gazebo Classic + gazebo_ros (the simulated lab robot, package tc70045e_sim below), xacro
# Weeks 5-6  : ros2 tooling, rosbag2 (MCAP), tf2 tools, robot_localization (EKF), imu_filter_madgwick
# Weeks 7,10 : RealSense driver (for a real D455), depth_image_proc, RTAB-Map, PCL, camera calibration, octomap
# Weeks 8-9  : LiDAR SLAM (slam_toolbox, cartographer) and Nav2
# Week 2     : ngspice (circuit simulation), socat and can-utils (serial and CAN tools)
# Week 12    : MAVSDK-Python for the PX4 drone simulation.
#              NOTE (verified 2026-09-19 against packages.ros.org jammy): there is NO ros-humble-mavros
#              binary package. Installing it here would fail and break the whole image build, so Week 12
#              talks to PX4 SITL with MAVSDK-Python over UDP. MAVROS is taught as theory; anyone who needs
#              it on Humble must build it from source.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ros-humble-gazebo-ros-pkgs ros-humble-xacro ros-humble-joint-state-publisher \
      ros-humble-realsense2-camera \
      ros-humble-realsense2-description \
      ros-humble-rtabmap-ros \
      ros-humble-slam-toolbox \
      ros-humble-cartographer-ros \
      ros-humble-navigation2 ros-humble-nav2-bringup \
      ros-humble-robot-localization \
      ros-humble-imu-filter-madgwick \
      ros-humble-rosbag2-storage-mcap \
      ros-humble-rqt-common-plugins ros-humble-rqt-tf-tree ros-humble-tf2-tools \
      ros-humble-pcl-ros ros-humble-image-pipeline ros-humble-depth-image-proc ros-humble-vision-opencv \
      ros-humble-camera-calibration \
      ros-humble-octomap-server ros-humble-octomap-ros \
      ros-humble-topic-tools ros-humble-teleop-twist-keyboard \
      ros-humble-joy ros-humble-joy-teleop \
      ros-humble-usb-cam \
      python3-colcon-common-extensions python3-pip python3-opencv \
      ros-dev-tools usbutils v4l-utils iputils-ping \
      ngspice socat can-utils xvfb nano \
 && rm -rf /var/lib/apt/lists/*

# Python tools students use for analysis, report figures, the serial/CAN labs and the Week 12 drone laboratory.
# numpy is PINNED BELOW 2.0 on purpose (verified 2026-09-19): pip install numpy pulls 2.x, which breaks
# the system-built cv_bridge with "ImportError: numpy.core.multiarray failed to import" and takes the
# Week 7, 10 and 11 vision laboratories down with it. mavsdk is pinned below 4.0 because that release
# replaces the documented gRPC API (which continues as the package mavsdk-grpc).
RUN pip3 install --no-cache-dir "numpy<2" scipy matplotlib pandas evo "mavsdk<4" python-can pyserial

# Week 11 edge-AI laboratory on the CPU: CPU-only PyTorch (about 1.5 GB instead of about 5 GB with CUDA), Ultralytics YOLO11,
# ONNX and ONNX Runtime. numpy<2 is repeated so this line cannot upgrade it (verified: numpy 1.26.4, torch 2.x+cpu,
# cv_bridge still imports). setuptools<80 because colcon needs it: torch otherwise pulls 84, which breaks
# colcon build --symlink-install of Python packages. The yolo11n.pt weights download over HTTPS on first use.
RUN pip3 install --no-cache-dir "numpy<2" "setuptools<80" --extra-index-url https://download.pytorch.org/whl/cpu \
      torch torchvision ultralytics onnx onnxruntime onnxslim

# --- The simulated lab robot (four-wheel mecanum base, 2D LiDAR, IMU, D455-style RGB-D camera, wheel encoders,
#     battery model, virtual serial microcontroller, motor test bench). Built once into /opt/tc70045e_ws. ---
COPY docker/tc70045e_sim /opt/tc70045e_ws/src/tc70045e_sim
RUN source /opt/ros/humble/setup.bash \
 && cd /opt/tc70045e_ws \
 && colcon build --install-base /opt/tc70045e_ws/install \
 && rm -rf /opt/tc70045e_ws/build /opt/tc70045e_ws/log

# Sensible defaults for the module.
# Written system-wide on purpose. Verified on 2026-09-20: the current tiryoh/ros2-desktop-vnc:humble
# image has NO "ubuntu" user and no /home/ubuntu at build time, so the older
# "echo ... >> /home/ubuntu/.bashrc" form failed the build. /etc/bash.bashrc and /etc/profile.d
# apply to every user (root, the desktop user, and any future one), and uid 1000 is the desktop user.
RUN mkdir -p /home/ubuntu/ws/src /home/ubuntu/ws/maps /home/ubuntu/bags /home/ubuntu/labs \
 && chown -R 1000:1000 /home/ubuntu \
 && { echo 'source /opt/ros/humble/setup.bash'; \
      echo 'source /opt/tc70045e_ws/install/setup.bash'; \
      echo 'export ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-7}'; \
      echo '[ -f $HOME/ws/install/setup.bash ] && source $HOME/ws/install/setup.bash'; \
    } > /etc/profile.d/tc70045e.sh \
 && chmod 0644 /etc/profile.d/tc70045e.sh \
 && cat /etc/profile.d/tc70045e.sh >> /etc/bash.bashrc

# --- The whole course repository is part of the image (self-contained: nothing has to be downloaded or mounted).
#     It lands in ~/labs. When you run the container from a clone with docker compose, the clone is mounted over
#     this copy instead, so your edits are kept on your own disk.
#     'core' (everything above) is also the base of the drone and CARLA images; they copy the course code last too,
#     so a change in the course code never rebuilds the simulators.
FROM core
COPY --chown=1000:1000 . /home/ubuntu/labs
