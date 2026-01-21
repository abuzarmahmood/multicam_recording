#!/usr/bin/env python3
"""
Test script to verify camera synchronization functionality in parallel_2_video.sh
"""

import subprocess
import time
import os
import sys
import tempfile
import shutil
from datetime import datetime

def test_synchronization_function_exists():
    """Test that the synchronization function is properly defined"""
    print("Testing synchronization function definition...")
    
    # Read the script and check if the function exists
    with open('parallel_2_video.sh', 'r') as f:
        script_content = f.read()
    
    assert 'start_streamer_at_time()' in script_content, "Failed: start_streamer_at_time function not found"
    assert 'export -f start_streamer_at_time' in script_content, "Failed: Function not exported for parallel"
    assert 'start_time=$(($(date +%s) + 3))' in script_content, "Failed: Start time calculation not found"
    
    print("✓ Synchronization function properly defined")

def test_script_syntax():
    """Test that the bash script has valid syntax"""
    print("Testing script syntax...")
    
    try:
        result = subprocess.run(['bash', '-n', 'parallel_2_video.sh'], 
                              capture_output=True, text=True, check=True)
        print("✓ Bash script syntax is valid")
    except subprocess.CalledProcessError as e:
        print(f"✗ Syntax error in script: {e.stderr}")
        raise

def test_start_time_calculation():
    """Test that start time calculation works correctly"""
    print("Testing start time calculation...")
    
    # Test the time calculation logic used in the script
    test_script = '''
    #!/bin/bash
    current_time=$(date +%s)
    start_time=$(($(date +%s) + 3))
    echo "$start_time"
    '''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(test_script)
        temp_script = f.name
    
    try:
        os.chmod(temp_script, 0o755)
        result = subprocess.run(['bash', temp_script], 
                              capture_output=True, text=True, check=True)
        
        calculated_time = int(result.stdout.strip())
        expected_time = int(time.time()) + 3
        
        # Allow 1 second tolerance for timing
        assert abs(calculated_time - expected_time) <= 1, f"Failed: Time calculation off by more than 1 second"
        
        print("✓ Start time calculation works correctly")
    finally:
        os.unlink(temp_script)

def test_simulation_timing():
    """Simulate the timing behavior to verify synchronization logic"""
    print("Testing timing simulation...")
    
    # Create a test script that simulates the timing behavior
    test_script = '''
    #!/bin/bash
    
    start_streamer_at_time() {
        local camera_id=$1
        local target_time=$2
        
        current_time=$(date +%s)
        if [ $current_time -lt $target_time ]; then
            sleep $((target_time - current_time))
        fi
        
        echo "Camera $camera_id started at $(date +%s)"
    }
    
    export -f start_streamer_at_time
    
    # Calculate a target time 2 seconds in the future
    target_time=$(($(date +%s) + 2))
    
    # Start two "cameras" in parallel
    seq 1 2 | parallel -j 2 start_streamer_at_time {} $target_time
    '''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(test_script)
        temp_script = f.name
    
    try:
        os.chmod(temp_script, 0o755)
        start_time = time.time()
        result = subprocess.run(['bash', temp_script], 
                              capture_output=True, text=True, check=True)
        
        lines = result.stdout.strip().split('\n')
        
        # Extract start times from output
        start_times = []
        for line in lines:
            if "started at" in line:
                time_str = line.split("started at ")[1]
                start_times.append(int(time_str))
        
        if len(start_times) == 2:
            # Both cameras should start at the same time (within 1 second)
            time_diff = abs(start_times[0] - start_times[1])
            assert time_diff <= 1, f"Failed: Cameras started {time_diff} seconds apart"
            print(f"✓ Simulation test passed - cameras synchronized within {time_diff} seconds")
        else:
            print("✗ Simulation test failed - unexpected output format")
            raise AssertionError("Unexpected output format")
            
    finally:
        os.unlink(temp_script)

def main():
    """Run all synchronization tests"""
    print("Running camera synchronization tests...\n")
    
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        test_synchronization_function_exists()
        test_script_syntax()
        test_start_time_calculation()
        test_simulation_timing()
        
        print("\n✓ All synchronization tests passed! The camera sync fix is working correctly.")
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error during testing: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
