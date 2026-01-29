#!/usr/bin/env python3
"""
Test script for parallel recording scripts functionality
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def test_script_exists():
    """Test that both scripts exist and are executable"""
    print("Testing script existence and executability...")
    
    # Test ffmpeg script
    ffmpeg_script = Path("parallel2video_ffmpeg.sh")
    assert ffmpeg_script.exists(), "parallel2video_ffmpeg.sh should exist"
    assert os.access(ffmpeg_script, os.X_OK), "parallel2video_ffmpeg.sh should be executable"
    
    # Test streamer script
    streamer_script = Path("parallel2video_streamer.sh")
    assert streamer_script.exists(), "parallel2video_streamer.sh should exist"
    assert os.access(streamer_script, os.X_OK), "parallel2video_streamer.sh should be executable"
    
    print("✓ Script existence and executability tests passed")

def test_script_syntax():
    """Test that scripts have valid bash syntax"""
    print("Testing script syntax...")
    
    scripts = ["parallel2video_ffmpeg.sh", "parallel2video_streamer.sh"]
    
    for script in scripts:
        result = subprocess.run(["bash", "-n", script], capture_output=True, text=True)
        assert result.returncode == 0, f"{script} should have valid bash syntax. Error: {result.stderr}"
    
    print("✓ Script syntax tests passed")

def test_ffmpeg_command_structure():
    """Test that ffmpeg script contains proper ffmpeg commands"""
    print("Testing ffmpeg command structure...")
    
    with open("parallel2video_ffmpeg.sh", "r") as f:
        content = f.read()
    
    # Check for key ffmpeg components
    assert "ffmpeg" in content, "Script should contain ffmpeg command"
    assert "-f v4l2" in content, "Script should use v4l2 format for Linux cameras"
    assert "-i {2}" in content, "Script should reference video devices dynamically"
    assert "-s 1280x720" in content, "Script should set video resolution"
    assert "-r 30" in content, "Script should set frame rate"
    assert "libx264" in content, "Script should use H.264 encoding"
    assert "-preset ultrafast" in content, "Script should use ultrafast preset for low latency"
    assert "-crf 23" in content, "Script should set quality level"
    assert "parallel -j $NUM_CAMERAS" in content, "Script should use parallel with dynamic camera count"
    
    print("✓ FFmpeg command structure tests passed")

def test_single_channel_functionality():
    """Test that ffmpeg script supports single channel recording"""
    print("Testing single channel recording functionality...")
    
    with open("parallel2video_ffmpeg.sh", "r") as f:
        content = f.read()
    
    # Check for single channel option prompt
    assert "single channel" in content.lower(), "Script should ask about single channel recording"
    assert "y/n" in content.lower(), "Script should provide y/n option for single channel"
    
    # Check for extractplanes filter
    assert "extractplanes=y" in content, "Script should use extractplanes filter for single channel"
    assert "-pix_fmt gray" in content, "Script should use gray pixel format for single channel"
    
    # Check for conditional logic
    assert "single_channel" in content, "Script should use single_channel variable"
    assert '[[ "$single_channel" =~ ^[Yy]$ ]]' in content, "Script should check for y/Y input"
    
    # Check that both normal and single channel commands exist
    assert "-pix_fmt yuv420p" in content, "Script should support normal yuv420p pixel format"
    assert "Recording full color video" in content, "Script should indicate normal recording mode"
    assert "Recording single channel" in content, "Script should indicate single channel recording mode"
    
    print("✓ Single channel functionality tests passed")

def test_streamer_command_structure():
    """Test that streamer script contains proper streamer commands"""
    print("Testing streamer command structure...")
    
    with open("parallel2video_streamer.sh", "r") as f:
        content = f.read()
    
    # Check for key streamer components
    assert "streamer" in content, "Script should contain streamer command"
    assert "-c {2}" in content, "Script should reference video devices dynamically"
    assert "-s 1280x720" in content, "Script should set video resolution"
    assert "-f jpeg" in content, "Script should use jpeg format"
    assert "-r 30" in content, "Script should set frame rate"
    assert "parallel -j $NUM_CAMERAS" in content, "Script should use parallel with dynamic camera count"
    assert ".avi" in content, "Script should output AVI files"
    
    print("✓ Streamer command structure tests passed")

def test_directory_structure_creation():
    """Test that scripts create proper directory structure"""
    print("Testing directory structure creation logic...")
    
    scripts = ["parallel2video_ffmpeg.sh", "parallel2video_streamer.sh"]
    
    for script in scripts:
        with open(script, "r") as f:
            content = f.read()
        
        # Check for directory creation
        assert 'mkdir -p "$output_dir/$fin_name"' in content, f"{script} should create directory with final name"
        assert 'cd "$output_dir/$fin_name"' in content, f"{script} should change to created directory"
        
        # Check for marker file creation
        assert "markers.txt" in content, f"{script} should create marker file"
        
        # Check for timing functionality
        assert "date +%s.%N" in content, f"{script} should record timestamps"
    
    print("✓ Directory structure creation tests passed")

def test_device_checking():
    """Test that scripts check for video devices from config"""
    print("Testing device checking functionality...")
    
    scripts = ["parallel2video_ffmpeg.sh", "parallel2video_streamer.sh"]
    
    for script in scripts:
        with open(script, "r") as f:
            content = f.read()
        
        # Check for config file reading
        assert "config.json" in content, f"{script} should read from config.json"
        assert "jq" in content, f"{script} should use jq to parse config"
        assert "video_devices" in content, f"{script} should read video_devices from config"
        
        # Check for device existence checking
        assert "AVAILABLE_DEVICES" in content, f"{script} should track available devices"
        assert "MISSING_DEVICES" in content, f"{script} should track missing devices"
        assert '[ -e "$device" ]' in content, f"{script} should check if device exists"
        
        # Check for user prompt on missing devices
        assert "Continue with" in content, f"{script} should prompt user to continue"
        assert "Aborting" in content, f"{script} should allow user to abort"
    
    print("✓ Device checking tests passed")

def test_config_has_video_devices():
    """Test that config.json has video_devices array"""
    print("Testing config.json video_devices...")
    
    import json
    with open("config.json", "r") as f:
        config = json.load(f)
    
    assert "video_devices" in config, "config.json should have video_devices"
    assert isinstance(config["video_devices"], list), "video_devices should be a list"
    assert len(config["video_devices"]) > 0, "video_devices should not be empty"
    
    for device in config["video_devices"]:
        assert device.startswith("/dev/video"), f"Device {device} should be a /dev/video path"
    
    print("✓ Config video_devices tests passed")

def test_script_differences():
    """Test that ffmpeg and streamer scripts have key differences"""
    print("Testing script differences...")
    
    with open("parallel2video_ffmpeg.sh", "r") as f:
        ffmpeg_content = f.read()
    
    with open("parallel2video_streamer.sh", "r") as f:
        streamer_content = f.read()
    
    # FFmpeg script should use ffmpeg, not streamer
    assert "ffmpeg" in ffmpeg_content, "FFmpeg script should use ffmpeg"
    assert "streamer" not in ffmpeg_content, "FFmpeg script should not use streamer"
    
    # Streamer script should use streamer, not ffmpeg
    assert "streamer" in streamer_content, "Streamer script should use streamer"
    assert "ffmpeg" not in streamer_content, "Streamer script should not use ffmpeg"
    
    # FFmpeg script should output MP4, streamer should output AVI
    assert ".mp4" in ffmpeg_content, "FFmpeg script should output MP4 files"
    assert ".avi" in streamer_content, "Streamer script should output AVI files"
    
    print("✓ Script differences tests passed")

def test_readme_updated():
    """Test that README has been updated with new script names"""
    print("Testing README updates...")
    
    with open("README.md", "r") as f:
        readme_content = f.read()
    
    # Check for new script names
    assert "parallel2video_ffmpeg.sh" in readme_content, "README should mention ffmpeg script"
    assert "parallel2video_streamer.sh" in readme_content, "README should mention streamer script"
    
    # Check that old script name is not mentioned
    assert "parallel_2_video.sh" not in readme_content, "README should not mention old script name"
    
    # Check for proper documentation
    assert "Recommended" in readme_content, "README should recommend ffmpeg script"
    assert "Legacy" in readme_content, "README should mark streamer script as legacy"
    
    print("✓ README update tests passed")

def main():
    """Run all tests"""
    print("Running parallel recording scripts tests...\n")
    
    try:
        test_script_exists()
        test_script_syntax()
        test_ffmpeg_command_structure()
        test_single_channel_functionality()
        test_streamer_command_structure()
        test_directory_structure_creation()
        test_device_checking()
        test_config_has_video_devices()
        test_script_differences()
        test_readme_updated()
        
        print("\n✓ All tests passed! The parallel recording scripts are working correctly.")
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error during testing: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
