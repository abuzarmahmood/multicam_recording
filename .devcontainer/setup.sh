#!/bin/bash

# .devcontainer/setup.sh - Setup script for multi-camera recording devcontainer

# Authenticate with GitHub CLI using token (if available)
if [ -n "$GITHUB_TOKEN" ]; then
    echo "$GITHUB_TOKEN" | gh auth login --with-token
    # Verify authentication
    gh auth status
fi

# Update package lists
sudo apt-get update

# Install system dependencies required for multi-camera recording
sudo apt-get install -y ffmpeg streamer parallel zenity figlet

# Install Python dependencies
pip install -r requirements.txt

# Make shell scripts executable
chmod +x parallel2video_ffmpeg.sh
chmod +x parallel2video_streamer.sh
chmod +x convert_files_gui.sh
chmod +x combine_utils/combine_videos_gui.sh

echo "Devcontainer setup complete! Multi-camera recording environment is ready."