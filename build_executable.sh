#!/bin/bash
# Auto-generated script to build executable for Codebase_Time_Machine

echo "=== Building Executable for Codebase_Time_Machine ==="
echo "Target file: /home/jyuc/Buildathon/projects/Codebase_Time_Machine/src/1/1.3/1.3.1/integration_test_1_3_1.py"

# Ensure dependencies are installed
echo "Installing dependencies..."
pip install -r "/home/jyuc/Buildathon/projects/Codebase_Time_Machine/requirements.txt"
pip install pyinstaller

# Create the executable with PyInstaller
echo "Building executable with PyInstaller..."
pyinstaller --onefile "/home/jyuc/Buildathon/projects/Codebase_Time_Machine/src/1/1.3/1.3.1/integration_test_1_3_1.py" --name "codebase_time_machine"

echo "=== Build Complete ==="
echo "Executable location: dist/codebase_time_machine"
echo "Run with: ./dist/codebase_time_machine"
