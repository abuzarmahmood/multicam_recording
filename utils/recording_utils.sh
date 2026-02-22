#!/bin/bash

# Shared utility functions for multicam recording scripts

# Get script directory (call from sourcing script)
get_script_dir() {
    cd "$(dirname "${BASH_SOURCE[1]}")" && pwd
}

# Show help message
# Args: $1 = script name, $2 = tool name, $3 = video format, $4 = video extension
show_help() {
    local script_name="$1"
    local tool_name="$2"
    local video_format="$3"
    local video_ext="$4"
    
    echo "Usage: $(basename "$script_name") [OPTIONS]"
    echo ""
    echo "Record video from 2 cameras simultaneously using $tool_name."
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message and exit"
    echo ""
    echo "Inputs (prompted interactively):"
    echo "  output_dir    Directory to save recordings (default: ./recorded_videos)"
    echo "  name          Base name for output files"
    echo ""
    echo "Outputs:"
    echo "  <output_dir>/<name>_video_<timestamp>/           Directory containing all outputs"
    echo "  <output_dir>/<name>_video_<timestamp>_cam0.$video_ext   Video from camera 0 ($video_format, 1280x720, 30fps)"
    echo "  <output_dir>/<name>_video_<timestamp>_cam1.$video_ext   Video from camera 1 ($video_format, 1280x720, 30fps)"
    echo "  <output_dir>/<name>_video_<timestamp>_markers.txt  Start/stop timestamps (Unix epoch)"
    echo ""
    echo "Requirements:"
    echo "  - $tool_name"
    echo "  - GNU parallel"
    echo "  - figlet"
    echo "  - jq"
    echo "  - Video devices configured in config.json"
    echo ""
    echo "Press Ctrl+C to stop recording."
}

# Load and validate video devices from config
# Sets: AVAILABLE_DEVICES array, NUM_CAMERAS
# Returns: 0 on success, 1 on failure
load_video_devices() {
    local script_dir="$1"
    local config_file="$script_dir/config.json"
    
    echo "Checking video devices..."
    if [ ! -f "$config_file" ]; then
        echo "❌ Config file not found: $config_file"
        return 1
    fi

    # Read video devices from config
    local wanted_devices
    mapfile -t wanted_devices < <(jq -r '.video_devices[]' "$config_file" 2>/dev/null)
    if [ ${#wanted_devices[@]} -eq 0 ]; then
        echo "❌ No video devices configured in config.json"
        return 1
    fi

    # Check which devices exist
    AVAILABLE_DEVICES=()
    local missing_devices=()
    for device in "${wanted_devices[@]}"; do
        if [ -e "$device" ]; then
            AVAILABLE_DEVICES+=("$device")
            echo "✅ Found: $device"
        else
            missing_devices+=("$device")
            echo "❌ Missing: $device"
        fi
    done

    # Handle missing devices
    if [ ${#missing_devices[@]} -gt 0 ]; then
        if [ ${#AVAILABLE_DEVICES[@]} -eq 0 ]; then
            echo ""
            echo "❌ No video devices available. Cannot proceed."
            return 1
        fi
        
        echo ""
        echo "⚠️  ${#missing_devices[@]} device(s) not found."
        echo "Available devices: ${AVAILABLE_DEVICES[*]}"
        echo ""
        echo -n "Continue with ${#AVAILABLE_DEVICES[@]} available device(s)? [y/N]: "
        read continue_choice
        if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
            echo "Aborting."
            return 1
        fi
    fi

    NUM_CAMERAS=${#AVAILABLE_DEVICES[@]}
    echo ""
    echo "Recording with $NUM_CAMERAS camera(s)"
    return 0
}

# Setup output directory with disk space check
# Args: $1 = script_dir
# Sets: output_dir
# Returns: 0 on success, 1 on failure
setup_output_directory() {
    local script_dir="$1"
    local default_output_dir="./recorded_videos"
    
    echo -n "Enter output directory [$default_output_dir]: "
    read output_dir
    output_dir=${output_dir:-$default_output_dir}

    # Create output directory if it doesn't exist
    mkdir -p "$output_dir"

    # Check disk space before starting recording
    echo "Checking disk space..."
    python3 "$script_dir/disk_space_check.py" --path "$output_dir"
    if [ $? -ne 0 ]; then
        echo "❌ Disk space check failed. Please free up disk space and try again."
        return 1
    fi
    return 0
}

# Generate recording name with timestamp
# Sets: fin_name
generate_recording_name() {
    local name_template="name_video_time"
    
    echo -n "Enter name: "
    read name
    local time=$(date +%g%m%d-%H%M%S)
    
    fin_name=${name_template/name/$name}
    fin_name=${fin_name/time/$time}
    echo "File name : $fin_name"
}

# Build device list string for parallel execution
# Uses: AVAILABLE_DEVICES array
# Sets: DEVICE_LIST
build_device_list() {
    DEVICE_LIST=""
    for i in "${!AVAILABLE_DEVICES[@]}"; do
        if [ -n "$DEVICE_LIST" ]; then
            DEVICE_LIST="$DEVICE_LIST\n$i:${AVAILABLE_DEVICES[$i]}"
        else
            DEVICE_LIST="$i:${AVAILABLE_DEVICES[$i]}"
        fi
    done
}

# Create recording directory and change to it
# Args: $1 = output_dir, $2 = fin_name
setup_recording_directory() {
    local output_dir="$1"
    local fin_name="$2"
    
    mkdir -p "$output_dir/$fin_name"
    cd "$output_dir/$fin_name"
}

# Write start marker and show recording message
# Args: $1 = time_file
start_recording() {
    local time_file="$1"
    
    figlet "ctrl+c to stop"
    echo "Start time : $(date)"
    echo
    date +%s.%N | cut -b-14 > "$time_file"
}

# Write stop marker
# Args: $1 = time_file
stop_recording() {
    local time_file="$1"
    
    echo "Stop time : $(date)"
    echo
    date +%s.%N | cut -b-14 >> "$time_file"
}
