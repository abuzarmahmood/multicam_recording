#!/usr/bin/env python3
"""
Test script for disk_space_check.py functionality
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add current directory to path to import disk_space_check
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from disk_space_check import load_config, get_free_disk_space, check_disk_space

def create_test_config(config_data, temp_dir):
    """Create a temporary config file for testing"""
    config_path = os.path.join(temp_dir, "test_config.json")
    with open(config_path, 'w') as f:
        json.dump(config_data, f)
    return config_path

def test_load_config():
    """Test configuration loading"""
    print("Testing configuration loading...")
    
    # Test valid config
    with tempfile.TemporaryDirectory() as temp_dir:
        test_config = {
            "disk_space": {
                "min_free_space_gb": 5,
                "warning_threshold_gb": 2,
                "estimated_space_per_minute_gb": 0.3
            }
        }
        config_path = create_test_config(test_config, temp_dir)
        
        loaded_config = load_config(config_path)
        assert loaded_config == test_config, "Failed to load valid configuration"
    
    # Test non-existent config
    try:
        load_config("nonexistent_config.json")
        assert False, "Should have raised exception for non-existent config"
    except SystemExit:
        pass  # Expected behavior
    
    print("✓ Configuration loading tests passed")

def test_get_free_disk_space():
    """Test disk space checking"""
    print("Testing disk space checking...")
    
    # Test current directory
    free_space = get_free_disk_space(".")
    assert free_space > 0, "Free space should be positive"
    assert isinstance(free_space, float), "Free space should be a float"
    
    # Test temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        free_space = get_free_disk_space(temp_dir)
        assert free_space > 0, "Free space should be positive for temp directory"
    
    print("✓ Disk space checking tests passed")

def test_check_disk_space_sufficient():
    """Test disk space check with sufficient space"""
    print("Testing disk space check with sufficient space...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create config with very low requirements to ensure test passes
        test_config = {
            "disk_space": {
                "min_free_space_gb": 0.001,  # Very low requirement
                "warning_threshold_gb": 0.0001,
                "estimated_space_per_minute_gb": 0.0001,
                "max_recording_minutes": 1
            },
            "recording": {
                "default_duration_minutes": 1
            }
        }
        
        config_path = create_test_config(test_config, temp_dir)
        result = check_disk_space(config_path, temp_dir, 1)
        assert result == True, "Should pass with sufficient disk space"
    
    print("✓ Sufficient disk space tests passed")

def test_check_disk_space_insufficient():
    """Test disk space check with insufficient space"""
    print("Testing disk space check with insufficient space...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create config with impossibly high requirements
        test_config = {
            "disk_space": {
                "min_free_space_gb": 1000000,  # Impossibly high requirement
                "warning_threshold_gb": 500000,
                "estimated_space_per_minute_gb": 100000,
                "max_recording_minutes": 1000000
            }
        }
        
        config_path = create_test_config(test_config, temp_dir)
        result = check_disk_space(config_path, temp_dir, 1)
        assert result == False, "Should fail with insufficient disk space"
    
    print("✓ Insufficient disk space tests passed")

def test_default_config_values():
    """Test that default config values work correctly"""
    print("Testing default configuration values...")
    
    # Create minimal config
    with tempfile.TemporaryDirectory() as temp_dir:
        test_config = {}  # Empty config should use defaults
        config_path = create_test_config(test_config, temp_dir)
        
        # This should not crash and should use default values
        try:
            check_disk_space(config_path, temp_dir, 1)
        except Exception as e:
            # If it fails, it should be due to insufficient space, not missing config
            assert "disk space" in str(e).lower(), f"Unexpected error: {e}"
    
    print("✓ Default configuration values tests passed")

def test_config_file_exists():
    """Test that the main config file exists and is valid"""
    print("Testing main configuration file...")
    
    config_path = "config.json"
    assert os.path.exists(config_path), "config.json should exist"
    
    # Try to load it
    try:
        config = load_config(config_path)
        assert isinstance(config, dict), "Config should be a dictionary"
        assert "disk_space" in config, "Config should have disk_space section"
        
        disk_config = config["disk_space"]
        required_keys = ["min_free_space_gb", "warning_threshold_gb", 
                        "estimated_space_per_minute_gb", "max_recording_minutes"]
        
        for key in required_keys:
            assert key in disk_config, f"Config should have {key}"
            assert isinstance(disk_config[key], (int, float)), f"{key} should be numeric"
        
    except Exception as e:
        assert False, f"Failed to load main config: {e}"
    
    print("✓ Main configuration file tests passed")

def test_script_integration():
    """Test that the disk space check script can be called from shell scripts"""
    print("Testing script integration...")
    
    # Check that the script exists and is executable
    script_path = "disk_space_check.py"
    assert os.path.exists(script_path), "disk_space_check.py should exist"
    
    # Test that it can be called (should not crash on config error)
    import subprocess
    result = subprocess.run([
        sys.executable, script_path, "--config", "nonexistent.json"
    ], capture_output=True, text=True)
    
    # Should exit with error code for non-existent config
    assert result.returncode != 0, "Should fail with non-existent config"
    # Check both stdout and stderr for the error message
    output = (result.stdout + result.stderr).lower()
    assert "not found" in output, f"Should mention config not found. Got stdout: {result.stdout}, stderr: {result.stderr}"
    
    print("✓ Script integration tests passed")

def main():
    """Run all tests"""
    print("Running disk space check tests...\n")
    
    try:
        test_load_config()
        test_get_free_disk_space()
        test_check_disk_space_sufficient()
        test_check_disk_space_insufficient()
        test_default_config_values()
        test_config_file_exists()
        test_script_integration()
        
        print("\n✓ All tests passed! The disk space checking functionality is working correctly.")
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error during testing: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())