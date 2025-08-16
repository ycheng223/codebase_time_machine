#!/bin/bash
# Docker run script for Codebase_Time_Machine

echo "=== Running Docker Container for Codebase_Time_Machine ==="
echo "Web application will be available at: http://localhost:8080"
docker run -p 8080:8080 codebase_time_machine
