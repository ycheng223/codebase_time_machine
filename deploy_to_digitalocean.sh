#!/bin/bash
# Deployment script for Codebase_Time_Machine to DigitalOcean App Platform

echo "=== Deploying Codebase_Time_Machine to DigitalOcean App Platform ==="

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "Error: doctl (DigitalOcean CLI) is not installed."
    echo "Please install it from https://github.com/digitalocean/doctl#installing-doctl"
    exit 1
fi

# Check if user is authenticated with DigitalOcean
if ! doctl account get &> /dev/null; then
    echo "You need to authenticate with DigitalOcean first."
    echo "Run: doctl auth init"
    exit 1
fi

# Check if GitHub repo is configured
if grep -q "YOUR_GITHUB_USERNAME/REPO_NAME" .do/app.yaml; then
    echo "⚠️ Please update the GitHub repository in .do/app.yaml"
    echo "Edit the file and replace YOUR_GITHUB_USERNAME/REPO_NAME with your actual GitHub repo"
    echo "For example: yourusername/codebase_time_machine"
    exit 1
fi

# Create the app
echo "Creating app on DigitalOcean App Platform..."
doctl apps create --spec .do/app.yaml

echo "=== Deployment Configuration Complete ==="
echo "Your application will be deployed when you push to your GitHub repository."
echo "You can manage your app from the DigitalOcean dashboard."
