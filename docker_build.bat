@echo off
REM Docker build script for Codebase_Time_Machine

echo === Building Docker Image for Codebase_Time_Machine ===
docker build -t codebase_time_machine .

echo === Build Complete ===
echo Run the container with: docker_run.bat
