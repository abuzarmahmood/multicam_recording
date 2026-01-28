#!/usr/bin/env python3
"""
Test script to verify that the downsampling functionality works correctly.
This script tests the ffmpeg command generation to ensure it uses the full sensor
with downsampling instead of fixed resolution capture.
"""

import subprocess
import re
import os

def test_ffmpeg_command_generation():
    """Test that the ffmpeg command includes the scale filter for downsampling."""
    
    # Read the script content
    script_path = "parallel2video_ffmpeg.sh"
    with open(script_path, 'r') as f:
        script_content = f.read()
    
    # Check if the script contains the scale filter
    has_scale_filter = "-vf scale=" in script_content
    has_fixed_resolution = "-s 1280x720" in script_content
    
    print("Testing ffmpeg command generation...")
    print(f"Has scale filter (-vf scale=): {has_scale_filter}")
    print(f"Has fixed resolution (-s 1280x720): {has_fixed_resolution}")
    
    # Extract the exec_string
    exec_string_match = re.search(r'exec_string="([^"]+)"', script_content)
    if exec_string_match:
        exec_string = exec_string_match.group(1)
        print(f"\nGenerated exec_string: {exec_string}")
        
        # Verify the command structure
        expected_parts = [
            "seq 0 1 | parallel -j 2 ffmpeg",
            "-f v4l2",
            "-i /dev/video{}",
            "-r 30",
            "-vf scale=1280x720",  # This is the key change
            "-c:v libx264",
            "-preset ultrafast",
            "-crf 23",
            "-pix_fmt yuv420p",
            "name_cam{}.mp4"
        ]
        
        all_parts_present = all(part in exec_string for part in expected_parts)
        print(f"\nAll expected command parts present: {all_parts_present}")
        
        if has_scale_filter and not has_fixed_resolution and all_parts_present:
            print("✅ Test PASSED: Script correctly uses full sensor with downsampling")
            return True
        else:
            print("❌ Test FAILED: Script does not use correct downsampling approach")
            return False
    else:
        print("❌ Test FAILED: Could not find exec_string in script")
        return False

def test_script_syntax():
    """Test that the bash script has valid syntax."""
    print("\nTesting script syntax...")
    try:
        result = subprocess.run(['bash', '-n', 'parallel2video_ffmpeg.sh'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Script syntax is valid")
            return True
        else:
            print(f"❌ Script syntax error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Could not find bash interpreter")
        return False

def main():
    """Run all tests."""
    print("Running downsampling functionality tests...\n")
    
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    test1_result = test_ffmpeg_command_generation()
    test2_result = test_script_syntax()
    
    print(f"\n{'='*50}")
    if test1_result and test2_result:
        print("🎉 ALL TESTS PASSED")
        print("The script correctly implements full sensor capture with downsampling")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the implementation")
    
    return test1_result and test2_result

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
