#!/usr/bin/env python3
"""
Disk space checking utility for multicam recording
Checks available disk space and validates against configuration requirements
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

def load_config(config_path="config.json"):
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file '{config_path}': {e}")
        sys.exit(1)

def get_free_disk_space(path="."):
    """Get free disk space in GB for the given path"""
    try:
        stat = shutil.disk_usage(path)
        free_gb = stat.free / (1024**3)  # Convert bytes to GB
        return free_gb
    except Exception as e:
        print(f"Error checking disk space for '{path}': {e}")
        sys.exit(1)

def check_disk_space(config_path="config.json", check_path=".", duration_minutes=None):
    """
    Check if there's enough disk space for recording
    
    Args:
        config_path: Path to configuration file
        check_path: Path to check for disk space (default: current directory)
        duration_minutes: Expected recording duration in minutes (optional)
    
    Returns:
        bool: True if enough space, False otherwise
    """
    config = load_config(config_path)
    disk_config = config.get("disk_space", {})
    recording_config = config.get("recording", {})
    
    # Get configuration values
    min_free_space_gb = disk_config.get("min_free_space_gb", 10)
    bitrate_mbps_per_camera = disk_config.get("bitrate_mbps_per_camera", 10)
    num_cameras = recording_config.get("num_cameras", 2)
    max_recording_minutes = disk_config.get("max_recording_minutes", 180)
    
    # Use provided duration or default from config
    if duration_minutes is None:
        duration_minutes = recording_config.get("default_duration_minutes", max_recording_minutes)
    
    # Cap duration to maximum
    duration_minutes = min(duration_minutes, max_recording_minutes)
    
    # Get actual free space
    free_space_gb = get_free_disk_space(check_path)
    
    # Calculate estimated space needed for this recording
    # Formula: (bitrate_mbps * num_cameras * duration_minutes * 60 seconds) / 8 bits per byte / 1024 MB per GB
    estimated_needed_gb = (bitrate_mbps_per_camera * num_cameras * duration_minutes * 60) / 8 / 1024
    
    print(f"Disk space check for path: {os.path.abspath(check_path)}")
    print(f"Available free space: {free_space_gb:.2f} GB")
    print(f"Minimum required free space buffer: {min_free_space_gb:.2f} GB")
    print(f"Recording parameters: {num_cameras} camera(s) @ {bitrate_mbps_per_camera} Mbps each")
    print(f"Estimated space needed for {duration_minutes} minutes: {estimated_needed_gb:.2f} GB")
    
    # Check if we have enough space (estimated needed + minimum buffer)
    total_required_gb = min_free_space_gb + estimated_needed_gb
    
    if free_space_gb < total_required_gb:
        print(f"\n❌ ERROR: Insufficient disk space!")
        print(f"Required: {total_required_gb:.2f} GB ({estimated_needed_gb:.2f} GB for recording + {min_free_space_gb:.2f} GB buffer)")
        print(f"Available: {free_space_gb:.2f} GB")
        print(f"Shortage: {total_required_gb - free_space_gb:.2f} GB")
        return False
    
    # Show remaining space after recording
    remaining_after_recording = free_space_gb - estimated_needed_gb
    
    print(f"\n✅ Disk space check passed!")
    print(f"Space after recording: {remaining_after_recording:.2f} GB")
    return True

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(
        description='Check disk space for multicam recording'
    )
    parser.add_argument(
        '--config', 
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    parser.add_argument(
        '--path', 
        default='.',
        help='Path to check for disk space (default: current directory)'
    )
    parser.add_argument(
        '--duration', 
        type=int,
        help='Expected recording duration in minutes'
    )
    
    args = parser.parse_args()
    
    success = check_disk_space(args.config, args.path, args.duration)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
