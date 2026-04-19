#!/usr/bin/env python3
"""
Test script for per-camera crop functionality
Verifies that the crop configuration works correctly
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Get the parent directory path
script_dir = Path(__file__).parent.parent


def test_config_has_crop_field():
    """Test that config.json has the crop field"""
    print("Testing config.json crop field...")
    
    config_file = script_dir / "config.json"
    assert config_file.exists(), "config.json should exist"
    
    with open(config_file, "r") as f:
        config = json.load(f)
    
    assert "crop" in config, "config.json should have crop field"
    print("✓ config.json has crop field")


def test_crop_has_enabled_flag():
    """Test that crop has enabled flag"""
    print("Testing crop enabled flag...")
    
    config_file = script_dir / "config.json"
    with open(config_file, "r") as f:
        config = json.load(f)
    
    crop = config.get("crop", {})
    assert "enabled" in crop, "crop should have enabled flag"
    assert isinstance(crop["enabled"], bool), "enabled should be a boolean"
    
    print("✓ Crop has enabled flag")


def test_crop_structure():
    """Test that crop field has correct structure"""
    print("Testing crop structure...")
    
    config_file = script_dir / "config.json"
    with open(config_file, "r") as f:
        config = json.load(f)
    
    crop = config.get("crop", {})
    
    # Check that crop values are arrays with 4 elements each (skip 'enabled' key)
    for cam_key, crop_values in crop.items():
        if cam_key == "enabled":
            continue
        assert isinstance(crop_values, list), f"crop['{cam_key}'] should be a list"
        assert len(crop_values) == 4, f"crop['{cam_key}'] should have 4 elements [x1, x2, y1, y2]"
        
        # Check that all values are integers
        for val in crop_values:
            assert isinstance(val, int), f"crop['{cam_key}'] values should be integers"
    
    print("✓ Crop structure is correct")


def test_transcode_script_has_crop_functions():
    """Test that transcode_simple.sh has crop-related functions"""
    print("Testing transcode_simple.sh crop functions...")
    
    transcode_script = script_dir / "postprocessing" / "transcode" / "transcode_simple.sh"
    assert transcode_script.exists(), "transcode_simple.sh should exist"
    
    with open(transcode_script, "r") as f:
        content = f.read()
    
    # Check for crop-related functions
    assert "load_crop_settings()" in content, "Script should have load_crop_settings function"
    assert "get_crop_filter()" in content, "Script should have get_crop_filter function"
    assert "CROP_SETTINGS" in content, "Script should have CROP_SETTINGS associative array"
    assert "_settings" in content.lower(), "Script should reference crop settings"
    
    print("✓ transcode_simple.sh has crop functions")


def test_crop_config_parsing():
    """Test that crop configuration can be parsed correctly"""
    print("Testing crop configuration parsing...")
    
    config_file = script_dir / "config.json"
    
    # Test jq parsing of crop settings
    result = subprocess.run(
        ["jq", "-r", ".crop.cam0[]", str(config_file)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, "jq should parse crop.cam0"
    assert "0" in result.stdout, "cam0 should have x1 value"
    assert "640" in result.stdout, "cam0 should have x2 value"
    
    print("✓ Crop configuration can be parsed correctly")


def test_crop_filter_in_script():
    """Test that crop filter code is present in script"""
    print("Testing crop filter code in script...")
    
    transcode_script = script_dir / "postprocessing" / "transcode" / "transcode_simple.sh"
    
    with open(transcode_script, "r") as f:
        content = f.read()
    
    # Check for crop filter generation logic
    assert "crop_w=$((x2" in content, "Script should calculate crop width"
    assert "crop_h=$((y2" in content, "Script should calculate crop height"
    assert "crop=${crop_w}:${crop_h}" in content, "Script should build crop filter string"
    assert "-vf $crop_filter" in content, "Script should use crop filter in ffmpeg"
    
    print("✓ Crop filter code is present in script")


def test_script_syntax():
    """Test that the script has valid bash syntax"""
    print("Testing script syntax...")
    
    transcode_script = script_dir / "postprocessing" / "transcode" / "transcode_simple.sh"
    result = subprocess.run(["bash", "-n", str(transcode_script)], capture_output=True, text=True)
    
    assert result.returncode == 0, f"Script should have valid bash syntax. Error: {result.stderr}"
    
    print("✓ Script syntax is valid")


def test_crop_filter_in_help():
    """Test that crop functionality is documented in script"""
    print("Testing crop documentation...")
    
    transcode_script = script_dir / "postprocessing" / "transcode" / "transcode_simple.sh"
    
    with open(transcode_script, "r") as f:
        content = f.read()
    
    # Check for crop documentation
    assert "crop" in content.lower(), "Script should mention crop"
    assert "config.json" in content, "Script should reference config.json for crop settings"
    
    print("✓ Crop functionality is documented")


def test_camera_index_extraction():
    """Test that camera index is extracted from filename"""
    print("Testing camera index extraction...")
    
    transcode_script = script_dir / "postprocessing" / "transcode" / "transcode_simple.sh"
    
    with open(transcode_script, "r") as f:
        content = f.read()
    
    # Check for camera index extraction
    assert "_cam([0-9]+)" in content, "Script should extract camera index from filename"
    assert "cam${BASH_REMATCH" in content, "Script should use captured camera index"
    
    print("✓ Camera index extraction works")


def main():
    """Run all tests"""
    print("Running crop functionality tests...\n")
    
    try:
        test_config_has_crop_field()
        test_crop_has_enabled_flag()
        test_crop_structure()
        test_transcode_script_has_crop_functions()
        test_crop_config_parsing()
        test_crop_filter_in_script()
        test_script_syntax()
        test_crop_filter_in_help()
        test_camera_index_extraction()
        
        print("\n✓ All crop tests passed!")
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"\n✗ File not found: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error during testing: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())