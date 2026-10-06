# TC70045E - start the lab environment on Windows (PowerShell).
# Usage:  right-click -> Run with PowerShell, or:  powershell -ExecutionPolicy Bypass -File start_windows.ps1
$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

Write-Host "Checking Docker..." -ForegroundColor Cyan
docker --version
docker compose version

Write-Host "Starting the ROS 2 lab container (first run downloads several GB)..." -ForegroundColor Cyan
docker compose up -d ros2

Write-Host ""
Write-Host "Open this address in your browser:  http://localhost:6080" -ForegroundColor Green
Write-Host "Inside the desktop, open a terminal and try:  ros2 topic list"
Write-Host ""
Write-Host "Drone simulation (Week 12):   docker compose up -d px4"
Write-Host "Stop everything:              docker compose down"
