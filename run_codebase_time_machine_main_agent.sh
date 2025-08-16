#!/bin/bash
# Auto-generated script for project: Codebase_Time_Machine

echo "🚀 Starting main.py multi-agent system for project: Codebase_Time_Machine"
echo "📁 Project output directory: /home/jyuc/Buildathon/projects"
echo "🔧 Multi-agent path: /home/jyuc/Buildathon/multi_agent"
echo "🎯 Project: Codebase_Time_Machine"
echo "📝 Description: Codebase Time Machine Description: Navigate any codebase through time, understanding evolution of fe..."
echo "============================================================"

# Set environment variables for project processing
export PROJECT_OUTPUT_DIR="/home/jyuc/Buildathon/projects"
export PROJECT_NAME="Codebase_Time_Machine"

# Change to the multi-agent directory
cd "/home/jyuc/Buildathon/multi_agent"

# Create a temporary CSV file with just this project using Python for proper escaping
python3 << 'PYTHON_CSV_EOF'
import csv
import sys

# Project data
project_name = "Codebase_Time_Machine"
project_prompt = """Codebase Time Machine Description: Navigate any codebase through time, understanding evolution of features and architectural decisions. Requirements: • Clone repo and analyze full git history • Build semantic understanding of code changes over time • Answer questions like ""Why was this pattern introduced?"" or ""Show me how auth evolved"" • Visualize code ownership and complexity trends • Link commits to business features/decisions"""

# Write to CSV file with proper escaping
with open("temp_project_3.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["project_name", "prompt"])
    writer.writerow([project_name, project_prompt])

print(f"✅ Created temp CSV for project: {project_name}")
PYTHON_CSV_EOF

# Create a simple Python script to run the single project
cat > run_single_project.py << 'PYTHON_EOF'
import sys
import os
import csv

# Import the main processing functions
sys.path.insert(0, os.getcwd())
from main import process_single_project

def run_single_project_from_csv(csv_file):
    """Run a single project from a CSV file."""
    with open(csv_file, newline="", encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            project_name = row["project_name"]
            project_prompt = row["prompt"]
            
            print(f"\n🚀 Processing project: {project_name}")
            print(f"📝 Description: {project_prompt[:200]}...")
            
            try:
                result = process_single_project(project_name, project_prompt, 0, 1)
                if result['status'] == 'completed':
                    print(f"\n✅ Project completed successfully!")
                    print(f"📁 Project folder: {result.get('project_folder', 'Unknown')}")
                else:
                    print(f"\n❌ Project failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"\n💥 Error processing project: {e}")
                import traceback
                traceback.print_exc()
            break  # Process only the first (and only) project

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "temp_project_3.csv"
    run_single_project_from_csv(csv_file)
PYTHON_EOF

# Run the single project processor
python3 run_single_project.py "temp_project_3.csv"

# Clean up temporary files
rm -f "temp_project_3.csv" run_single_project.py

echo "============================================================"
echo "✅ Completed processing for project: Codebase_Time_Machine"
echo "📁 Check the project folder created by main.py"
echo "📊 Review the generated files for detailed results"
read -p "Press Enter to close this terminal..."
