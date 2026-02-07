#!/usr/bin/env python3
"""
Test script for transcode_copy_videos.sh functionality
"""

import os
import sys
import subprocess
import tempfile
import shutil
import json
from pathlib import Path

# Get the parent directory path
script_dir = Path(__file__).parent.parent

def test_script_exists():
    """Test that transcoding scripts exist and are executable"""
    print("Testing script existence and executability...")
    
    # Test main transcoding script
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    assert transcode_script.exists(), "postprocessing/transcode_copy_videos.sh should exist"
    assert os.access(transcode_script, os.X_OK), "postprocessing/transcode_copy_videos.sh should be executable"
    
    # Test GUI script
    gui_script = script_dir / "postprocessing" / "transcode_copy_videos_gui.sh"
    assert gui_script.exists(), "postprocessing/transcode_copy_videos_gui.sh should exist"
    assert os.access(gui_script, os.X_OK), "postprocessing/transcode_copy_videos_gui.sh should be executable"
    
    print("✓ Script existence and executability tests passed")

def test_script_syntax():
    """Test that scripts have valid bash syntax"""
    print("Testing script syntax...")
    
    scripts = [
        script_dir / "postprocessing" / "transcode_copy_videos.sh", 
        script_dir / "postprocessing" / "transcode_copy_videos_gui.sh"
    ]
    
    for script in scripts:
        result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        assert result.returncode == 0, f"{script} should have valid bash syntax. Error: {result.stderr}"
    
    print("✓ Script syntax tests passed")

def test_help_functionality():
    """Test that help functionality works correctly"""
    print("Testing help functionality...")
    
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    
    # Test help flag
    result = subprocess.run([str(transcode_script), "--help"], capture_output=True, text=True)
    assert result.returncode == 0, "Help should return exit code 0"
    assert "Usage:" in result.stdout, "Help should show usage information"
    assert "OPTIONS:" in result.stdout, "Help should show options"
    assert "QUALITY PRESETS:" in result.stdout, "Help should show quality presets"
    assert "-h, --help" in result.stdout, "Help should mention help flag"
    assert "--gui" in result.stdout, "Help should mention GUI flag"
    
    print("✓ Help functionality tests passed")

def test_quality_presets():
    """Test that quality presets are properly defined"""
    print("Testing quality presets...")
    
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    
    with open(transcode_script, "r") as f:
        content = f.read()
    
    # Check for quality presets array
    assert 'QUALITY_PRESETS=(' in content, "Script should define quality presets array"
    assert '"low"]=' in content, "Script should define low quality preset"
    assert '"medium"]=' in content, "Script should define medium quality preset"
    assert '"high"]=' in content, "Script should define high quality preset"
    assert '"ultra"]=' in content, "Script should define ultra quality preset"
    
    # Check for CRF values in presets
    assert '28' in content, "Script should include CRF 28 for low quality"
    assert '23' in content, "Script should include CRF 23 for medium quality"
    assert '18' in content, "Script should include CRF 18 for high quality"
    assert '15' in content, "Script should include CRF 15 for ultra quality"
    
    print("✓ Quality presets tests passed")

def test_ffmpeg_command_structure():
    """Test that ffmpeg commands are properly structured"""
    print("Testing ffmpeg command structure...")
    
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    
    with open(transcode_script, "r") as f:
        content = f.read()
    
    # Check for ffmpeg components
    assert "ffmpeg -i" in content, "Script should use ffmpeg with input file"
    assert "-c:v libx264" in content, "Script should use H.264 encoding"
    assert "-preset" in content, "Script should allow preset configuration"
    assert "-crf" in content, "Script should use CRF for quality control"
    assert "-c:a copy" in content, "Script should copy audio stream without re-encoding"
    
    # Check for parallel processing
    assert "parallel -j" in content, "Script should use parallel for batch processing"
    
    print("✓ FFmpeg command structure tests passed")

def test_copy_detection_logic():
    """Test that copy-encoded video detection logic exists"""
    print("Testing copy-encoded video detection logic...")
    
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    
    with open(transcode_script, "r") as f:
        content = f.read()
    
    # Check for detection function
    assert "is_copy_encoded()" in content, "Script should have copy detection function"
    assert "ffprobe" in content, "Script should use ffprobe for codec detection"
    assert "codec_name" in content, "Script should check codec name"
    assert "rawvideo" in content, "Script should detect raw video codec"
    assert "copy" in content, "Script should detect copy mode"
    
    # Check for file size analysis
    assert "file_size" in content, "Script should analyze file sizes"
    assert "duration" in content, "Script should check video duration"
    
    print("✓ Copy detection logic tests passed")

def test_gui_integration():
    """Test that GUI integration is properly implemented"""
    print("Testing GUI integration...")
    
    # Test main script GUI mode
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    with open(transcode_script, "r") as f:
        content = f.read()
    
    assert "--gui" in content, "Main script should support --gui flag"
    assert "launch_gui()" in content, "Main script should have GUI launch function"
    assert "zenity" in content, "Main script should use zenity for GUI"
    
    # Test GUI wrapper script
    gui_script = script_dir / "postprocessing" / "transcode_copy_videos_gui.sh"
    with open(gui_script, "r") as f:
        gui_content = f.read()
    
    assert "zenity" in gui_content, "GUI script should check for zenity"
    assert "transcode_copy_videos.sh" in gui_content, "GUI script should call main script"
    assert "--gui" in gui_content, "GUI script should pass --gui flag"
    
    print("✓ GUI integration tests passed")

def test_error_handling():
    """Test that error handling is properly implemented"""
    print("Testing error handling...")
    
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    
    with open(transcode_script, "r") as f:
        content = f.read()
    
    # Check for dependency checks
    assert "command -v ffmpeg" in content, "Script should check for ffmpeg"
    assert "command -v ffprobe" in content, "Script should check for ffprobe"
    assert "command -v parallel" in content, "Script should check for parallel"
    
    # Check for file existence checks
    assert "File not found" in content, "Script should check for file existence"
    assert "No input files specified" in content, "Script should validate input files"
    
    # Check for invalid option handling
    assert "Unknown option" in content, "Script should handle unknown options"
    assert "Invalid quality preset" in content, "Script should validate quality presets"
    
    print("✓ Error handling tests passed")

def test_output_naming():
    """Test that output file naming is properly handled"""
    print("Testing output file naming...")
    
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    
    with open(transcode_script, "r") as f:
        content = f.read()
    
    # Check for output suffix handling
    assert "OUTPUT_SUFFIX" in content, "Script should define output suffix"
    assert "_transcoded" in content, "Script should have default transcoded suffix"
    assert "--output-suffix" in content, "Script should allow custom output suffix"
    
    # Check for file extension handling
    assert "{/.}" in content, "Script should handle filename without extension"
    assert ".mp4" in content, "Script should output MP4 files"
    
    print("✓ Output naming tests passed")

def test_dry_run_functionality():
    """Test that dry-run functionality is implemented"""
    print("Testing dry-run functionality...")
    
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    
    with open(transcode_script, "r") as f:
        content = f.read()
    
    # Check for dry-run flag
    assert "--dry-run" in content, "Script should support dry-run flag"
    assert "DRY RUN" in content, "Script should indicate dry-run mode"
    assert "Would execute:" in content, "Script should show what would be executed"
    
    print("✓ Dry-run functionality tests passed")

def test_video_info_functionality():
    """Test that video information display is implemented"""
    print("Testing video information functionality...")
    
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    
    with open(transcode_script, "r") as f:
        content = f.read()
    
    # Check for video info function
    assert "get_video_info()" in content, "Script should have video info function"
    assert "Video Information for:" in content, "Script should display video info header"
    assert "Duration:" in content, "Script should show video duration"
    assert "Resolution:" in content, "Script should show video resolution"
    assert "Codec:" in content, "Script should show video codec"
    assert "File Size:" in content, "Script should show file size"
    assert "Status:" in content, "Script should show copy-encoded status"
    
    print("✓ Video information functionality tests passed")

def test_progress_reporting():
    """Test that progress reporting is implemented"""
    print("Testing progress reporting...")
    
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    
    with open(transcode_script, "r") as f:
        content = f.read()
    
    # Check for progress indicators
    assert "Processing:" in content, "Script should show processing status"
    assert "Settings:" in content, "Script should show encoding settings"
    assert "Transcoded successfully" in content, "Script should show success message"
    assert "Failed to transcode" in content, "Script should show failure message"
    assert "Size reduction:" in content, "Script should show size reduction"
    
    print("✓ Progress reporting tests passed")

def test_script_documentation():
    """Test that scripts have proper documentation"""
    print("Testing script documentation...")
    
    # Test main script documentation
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    with open(transcode_script, "r") as f:
        content = f.read()
    
    assert "Script to transcode and compress videos" in content, "Main script should have description"
    assert "recorded with -c:v copy flag" in content, "Main script should mention copy flag"
    assert "Features:" in content, "Main script should list features"
    assert "USAGE:" in content, "Main script should show usage examples"
    
    # Test GUI script documentation
    gui_script = script_dir / "postprocessing" / "transcode_copy_videos_gui.sh"
    with open(gui_script, "r") as f:
        gui_content = f.read()
    
    assert "GUI wrapper for transcode_copy_videos.sh" in gui_content, "GUI script should have description"
    assert "user-friendly interface" in gui_content, "GUI script should mention user-friendly interface"
    
    print("✓ Script documentation tests passed")

def test_no_files_error():
    """Test that script handles no files case correctly"""
    print("Testing no files error handling...")
    
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    
    # Test with no arguments
    result = subprocess.run([str(transcode_script)], capture_output=True, text=True)
    assert result.returncode != 0, "Script should return error when no files provided"
    assert "No input files specified" in (result.stderr + result.stdout), "Script should show appropriate error message"
    
    print("✓ No files error handling tests passed")

def test_invalid_quality_preset():
    """Test that script handles invalid quality preset correctly"""
    print("Testing invalid quality preset handling...")
    
    transcode_script = script_dir / "postprocessing" / "transcode_copy_videos.sh"
    
    # Create a dummy file for testing
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
        tmp_file.write(b"dummy content")
        tmp_file_path = tmp_file.name
    
    try:
        # Test with invalid quality preset
        result = subprocess.run([str(transcode_script), "--quality", "invalid", tmp_file_path], 
                              capture_output=True, text=True)
        assert result.returncode != 0, "Script should return error for invalid quality preset"
        assert "Invalid quality preset" in (result.stderr + result.stdout), "Script should show appropriate error message"
    finally:
        os.unlink(tmp_file_path)
    
    print("✓ Invalid quality preset handling tests passed")

def main():
    """Run all tests"""
    print("Running transcode_copy_videos.sh tests...\n")
    
    try:
        test_script_exists()
        test_script_syntax()
        test_help_functionality()
        test_quality_presets()
        test_ffmpeg_command_structure()
        test_copy_detection_logic()
        test_gui_integration()
        test_error_handling()
        test_output_naming()
        test_dry_run_functionality()
        test_video_info_functionality()
        test_progress_reporting()
        test_script_documentation()
        test_no_files_error()
        test_invalid_quality_preset()
        
        print("\n✓ All tests passed! The transcoding scripts are working correctly.")
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error during testing: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
