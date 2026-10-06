#!/usr/bin/env bash
# TC70045E - start the lab environment on macOS or Linux.   Usage:  ./start_mac_linux.sh
set -e
cd "$(dirname "$0")"

echo "Checking Docker..."
docker --version
docker compose version

echo "Starting the ROS 2 lab container (first run downloads several GB)..."
docker compose up -d ros2

cat <<'EOF'

Open this address in your browser:  http://localhost:6080
Inside the desktop, open a terminal and try:  ros2 topic list

Drone simulation (Week 12):   docker compose up -d px4
Stop everything:              docker compose down
EOF
