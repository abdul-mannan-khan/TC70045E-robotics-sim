# Week 01 – commands and code from the lecture, in order

Generated from the lecture (Week 1: Your Robotics Workstation – Linux, Docker, ROS 2 and Claude – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 

```bash
docker pull tiryoh/ros2-desktop-vnc:humble
```

## Windows 10 / 11: WSL 2

```text
# PowerShell as Administrator
wsl --install -d Ubuntu-22.04
# restart when asked, then create a
# Linux user name and password
wsl -l -v      # VERSION must be 2
```

## macOS or Linux

```text
uname -a       # prints the kernel
```

```bash
docker --version
docker run hello-world          # prints "Hello from Docker!"
```

```bash
# Windows PowerShell
docker run -d --name ros2lab `
  -p 6080:80 --shm-size=1g `
  -v "${PWD}:/home/ubuntu/labs" `
  tiryoh/ros2-desktop-vnc:humble
```

```bash
# macOS / Linux / WSL terminal
docker run -d --name ros2lab \
  -p 6080:80 --shm-size=1g \
  -v "$PWD":/home/ubuntu/labs \
  tiryoh/ros2-desktop-vnc:humble
```

```bash
docker ps                 # is it running?
docker stop ros2lab       # pause it  (files kept)
docker start ros2lab      # resume it
docker rm -f ros2lab      # delete it (only ~/labs survives - see Part B)
```

```bash
# terminal 1
ros2 run demo_nodes_cpp talker
```

```bash
# terminal 2
ros2 run demo_nodes_py listener
```

```bash
sudo apt install software-properties-common curl && sudo add-apt-repository universe
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo $VERSION_CODENAME)_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update && sudo apt install ros-humble-desktop ros-dev-tools
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

## Install Claude Code (on your laptop)

```bash
# macOS / Linux / WSL
curl -fsSL https://claude.ai/install.sh | bash

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex

claude --version     # checkpoint
claude doctor        # if anything is wrong
```

## First run

```bash
# T1: the simulator               # T2: drive it with the arrow keys
ros2 run turtlesim turtlesim_node   ros2 run turtlesim turtle_teleop_key
# T3: look inside
ros2 node list
ros2 topic list -t
ros2 topic echo /turtle1/pose
ros2 topic hz /turtle1/pose                  # about 62 Hz
ros2 service call /spawn turtlesim/srv/Spawn "{x: 2.0, y: 2.0, theta: 0.0, name: turtle2}"
ros2 param set /turtlesim background_r 200
ros2 topic pub --once /turtle2/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0}, angular: {z: 1.5}}"
rqt_graph
```

```bash
ros2 launch ~/labs/week01/scripts/thermal_loop.launch.py      # T1: all three nodes
rqt_graph                                                      # T2: see Fig. 11
ros2 topic echo /room/temperature                              # T3: the sensor
ros2 topic hz /room/temperature                                #     5.000 Hz
ros2 param set /fan_controller setpoint 24.0                   #     change the goal
ros2 service call /fan/stop std_srvs/srv/SetBool "{data: true}"   # emergency stop
ros2 service call /fan/stop std_srvs/srv/SetBool "{data: false}"  # release
ros2 bag record -o ~/labs/week01/loop /room/temperature /fan/duty /fan/speed   # Ctrl+C after 30 s
```

```bash
echo hello > /tmp/note.txt                    # in the container
echo hello > ~/labs/week01/my_note.txt
# on the LAPTOP terminal:
docker rm -f ros2lab                           # then run the docker run command again (3.1)
# in the new container:
cat /tmp/note.txt ; cat ~/labs/week01/my_note.txt ; ls ~/labs/week01/loop
```

```bash
docker compose up -d ros2        # 20-40 min; it resumes next week if unfinished
```
