#!/usr/bin/env python3
"""
Test script for combine_videos.py functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'combine_utils'))

from combine_videos import determine_grid_layout, get_quality_settings, build_ffmpeg_command

def test_grid_layout():
    """Test grid layout determination"""
    print("Testing grid layout determination...")
    
    # Test auto layouts
    assert determine_grid_layout(1, 'auto') == (1, 1), "Failed: 1 video should be 1x1"
    assert determine_grid_layout(2, 'auto') == (1, 2), "Failed: 2 videos should be 1x2"
    assert determine_grid_layout(3, 'auto') == (1, 3), "Failed: 3 videos should be 1x3"
    assert determine_grid_layout(4, 'auto') == (2, 2), "Failed: 4 videos should be 2x2"
    assert determine_grid_layout(6, 'auto') == (2, 3), "Failed: 6 videos should be 2x3"
    
    # Test specified layouts
    assert determine_grid_layout(2, '2x1') == (2, 1), "Failed: 2 videos in 2x1 layout"
    assert determine_grid_layout(4, '2x2') == (2, 2), "Failed: 4 videos in 2x2 layout"
    
    print("✓ Grid layout tests passed")

def test_quality_settings():
    """Test quality settings"""
    print("Testing quality settings...")
    
    low_settings = get_quality_settings('low')
    assert low_settings['crf'] == '28', "Failed: Low quality CRF should be 28"
    assert low_settings['preset'] == 'fast', "Failed: Low quality preset should be fast"
    
    medium_settings = get_quality_settings('medium')
    assert medium_settings['crf'] == '23', "Failed: Medium quality CRF should be 23"
    assert medium_settings['preset'] == 'medium', "Failed: Medium quality preset should be medium"
    
    high_settings = get_quality_settings('high')
    assert high_settings['crf'] == '18', "Failed: High quality CRF should be 18"
    assert high_settings['preset'] == 'slow', "Failed: High quality preset should be slow"
    
    print("✓ Quality settings tests passed")

def test_ffmpeg_command_building():
    """Test ffmpeg command building"""
    print("Testing ffmpeg command building...")
    
    input_videos = ['video1.avi', 'video2.avi']
    output_file = 'combined.mp4'
    rows, cols = 1, 2  # Side by side
    scale_width = 640
    quality = 'high'
    
    cmd = build_ffmpeg_command(input_videos, output_file, rows, cols, scale_width, quality)
    
    # Check basic command structure
    assert 'ffmpeg' in cmd, "Failed: Command should start with ffmpeg"
    assert '-i' in cmd, "Failed: Command should include input files"
    assert output_file in cmd, "Failed: Command should include output file"
    assert '-filter_complex' in cmd, "Failed: Command should include filter_complex"
    assert 'scale=640' in ' '.join(cmd), "Failed: Command should include scaling"
    assert 'hstack' in ' '.join(cmd), "Failed: Command should include hstack for side-by-side layout"
    
    print("✓ FFmpeg command building tests passed")

def test_file_validation():
    """Test file validation functionality"""
    print("Testing file validation...")
    
    from combine_videos import validate_input_files
    
    # Test with non-existent file
    assert not validate_input_files(['nonexistent.avi']), "Failed: Should validate non-existent file"
    
    # Test with existing directory (not file)
    assert validate_input_files(['/tmp']), "Failed: Should validate existing readable file/directory"
    
    print("✓ File validation tests passed")

def main():
    """Run all tests"""
    print("Running combine_videos.py tests...\n")
    
    try:
        test_grid_layout()
        test_quality_settings()
        test_ffmpeg_command_building()
        test_file_validation()
        
        print("\n✓ All tests passed! The combine_videos.py functionality is working correctly.")
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error during testing: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
