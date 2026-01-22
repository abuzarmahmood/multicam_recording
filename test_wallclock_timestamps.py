#!/usr/bin/env python3
"""
Test script for wall-clock timestamp functionality in parallel2video_ffmpeg.sh
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def test_ffmpeg_wallclock_flag():
    """Test that ffmpeg supports the -use_wallclock_as_timestamps flag"""
    print("Testing ffmpeg wall-clock timestamp flag support...")
    
    try:
        # Test ffmpeg help output for the flag
        result = subprocess.run(['ffmpeg', '-h', 'full'], capture_output=True, text=True, timeout=10)
        if 'use_wallclock_as_timestamps' in result.stdout:
            print("✓ FFmpeg supports -use_wallclock_as_timestamps flag")
            return True
        else:
            print("✗ FFmpeg does not support -use_wallclock_as_timestamps flag")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"✗ Error testing ffmpeg flag: {e}")
        return False

def test_ffmpeg_mkvtimestamp_v2():
    """Test that ffmpeg supports the mkvtimestamp_v2 format"""
    print("Testing ffmpeg mkvtimestamp_v2 format support...")
    
    try:
        # Test ffmpeg help output for the format
        result = subprocess.run(['ffmpeg', '-formats'], capture_output=True, text=True, timeout=10)
        if 'mkvtimestamp_v2' in result.stdout:
            print("✓ FFmpeg supports mkvtimestamp_v2 format")
            return True
        else:
            print("✗ FFmpeg does not support mkvtimestamp_v2 format")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"✗ Error testing ffmpeg format: {e}")
        return False

def test_script_syntax():
    """Test that the modified script has correct bash syntax"""
    print("Testing script syntax...")
    
    script_path = Path(__file__).parent / 'parallel2video_ffmpeg.sh'
    
    try:
        result = subprocess.run(['bash', '-n', str(script_path)], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Script syntax is valid")
            return True
        else:
            print(f"✗ Script syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error testing script syntax: {e}")
        return False

def test_script_contains_wallclock_flag():
    """Test that the script contains the wall-clock timestamp flag"""
    print("Testing script contains wall-clock timestamp flag...")
    
    script_path = Path(__file__).parent / 'parallel2video_ffmpeg.sh'
    
    try:
        with open(script_path, 'r') as f:
            content = f.read()
        
        if '-use_wallclock_as_timestamps 1' in content:
            print("✓ Script contains wall-clock timestamp flag")
            return True
        else:
            print("✗ Script does not contain wall-clock timestamp flag")
            return False
    except Exception as e:
        print(f"✗ Error reading script: {e}")
        return False

def test_script_contains_timestamp_extraction():
    """Test that the script contains timestamp extraction functionality"""
    print("Testing script contains timestamp extraction functionality...")
    
    script_path = Path(__file__).parent / 'parallel2video_ffmpeg.sh'
    
    try:
        with open(script_path, 'r') as f:
            content = f.read()
        
        if 'mkvtimestamp_v2' in content and '_timestamps.txt' in content:
            print("✓ Script contains timestamp extraction functionality")
            return True
        else:
            print("✗ Script does not contain timestamp extraction functionality")
            return False
    except Exception as e:
        print(f"✗ Error reading script: {e}")
        return False

def create_test_video_with_timestamps():
    """Create a test video with wall-clock timestamps for testing extraction"""
    print("Creating test video with wall-clock timestamps...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_video = os.path.join(temp_dir, 'test_video.mp4')
        timestamp_file = os.path.join(temp_dir, 'test_timestamps.txt')
        
        try:
            # Create a short test video with wall-clock timestamps
            cmd = [
                'ffmpeg', '-use_wallclock_as_timestamps', '1',
                '-f', 'lavfi', '-i', 'testsrc=duration=5:size=320x240:rate=30',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
                '-y', test_video
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"✗ Failed to create test video: {result.stderr}")
                return False
            
            # Extract timestamps from the test video
            cmd = ['ffmpeg', '-i', test_video, '-f', 'mkvtimestamp_v2', timestamp_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"✗ Failed to extract timestamps: {result.stderr}")
                return False
            
            # Check if timestamp file was created and has content
            if os.path.exists(timestamp_file) and os.path.getsize(timestamp_file) > 0:
                print("✓ Successfully created test video and extracted timestamps")
                
                # Show a sample of the timestamps
                with open(timestamp_file, 'r') as f:
                    lines = f.readlines()[:5]  # First 5 lines
                    print(f"Sample timestamps: {lines}")
                
                return True
            else:
                print("✗ Timestamp file was not created or is empty")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ Timeout during test video creation")
            return False
        except Exception as e:
            print(f"✗ Error during test video creation: {e}")
            return False

def main():
    """Run all tests for wall-clock timestamp functionality"""
    print("Running wall-clock timestamp functionality tests...\n")
    
    tests = [
        test_ffmpeg_wallclock_flag,
        test_ffmpeg_mkvtimestamp_v2,
        test_script_syntax,
        test_script_contains_wallclock_flag,
        test_script_contains_timestamp_extraction,
        create_test_video_with_timestamps,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}\n")
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Wall-clock timestamp functionality is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
