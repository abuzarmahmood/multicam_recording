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

def check_disk_space(config_path="config.json", check_path="."):
    """
    Check if there's enough disk space for recording
    
    Args:
        config_path: Path to configuration file
        check_path: Path to check for disk space (default: current directory)
    
    Returns:
        bool: True if enough space, False otherwise
    """
    config = load_config(config_path)
    disk_config = config.get("disk_space", {})
    
    # Get minimum free space requirement
    min_free_space_gb = disk_config.get("min_free_space_gb", 10)
    
    # Get actual free space
    free_space_gb = get_free_disk_space(check_path)
    
    print(f"Disk space check for path: {os.path.abspath(check_path)}")
    print(f"Available free space: {free_space_gb:.2f} GB")
    print(f"Minimum required free space: {min_free_space_gb:.2f} GB")
    
    # Check if we have enough space
    if free_space_gb < min_free_space_gb:
        print(f"\n❌ ERROR: Insufficient disk space!")
        print(f"Required: {min_free_space_gb:.2f} GB")
        print(f"Available: {free_space_gb:.2f} GB")
        print(f"Shortage: {min_free_space_gb - free_space_gb:.2f} GB")
        return False
    
    print(f"\n✅ Disk space check passed!")
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
    args = parser.parse_args()
    
    success = check_disk_space(args.config, args.path)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
