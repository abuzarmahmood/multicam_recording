#!/bin/bash

: '
Script to simulatenously record from 2 cameras
When run requests input for filename and time in minutes
Outputs:
-Video files
-Marker text file (start and stop times for recording)
'

# Help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo ""
    echo "Record video from 2 cameras simultaneously using streamer."
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
    echo "  <output_dir>/<name>_video_<timestamp>_cam0.avi   Video from camera 0 (JPEG, 1280x720, 30fps)"
    echo "  <output_dir>/<name>_video_<timestamp>_cam1.avi   Video from camera 1 (JPEG, 1280x720, 30fps)"
    echo "  <output_dir>/<name>_video_<timestamp>_markers.txt  Start/stop timestamps (Unix epoch)"
    echo ""
    echo "Requirements:"
    echo "  - streamer"
    echo "  - GNU parallel"
    echo "  - figlet"
    echo "  - jq"
    echo "  - Video devices configured in config.json"
    echo ""
    echo "Press Ctrl+C to stop recording."
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.json"

# Check video devices from config
echo "Checking video devices..."
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

# Read video devices from config
mapfile -t WANTED_DEVICES < <(jq -r '.video_devices[]' "$CONFIG_FILE" 2>/dev/null)
if [ ${#WANTED_DEVICES[@]} -eq 0 ]; then
    echo "❌ No video devices configured in config.json"
    exit 1
fi

# Check which devices exist
AVAILABLE_DEVICES=()
MISSING_DEVICES=()
for device in "${WANTED_DEVICES[@]}"; do
    if [ -e "$device" ]; then
        AVAILABLE_DEVICES+=("$device")
        echo "✅ Found: $device"
    else
        MISSING_DEVICES+=("$device")
        echo "❌ Missing: $device"
    fi
done

# Handle missing devices
if [ ${#MISSING_DEVICES[@]} -gt 0 ]; then
    if [ ${#AVAILABLE_DEVICES[@]} -eq 0 ]; then
        echo ""
        echo "❌ No video devices available. Cannot proceed."
        exit 1
    fi
    
    echo ""
    echo "⚠️  ${#MISSING_DEVICES[@]} device(s) not found."
    echo "Available devices: ${AVAILABLE_DEVICES[*]}"
    echo ""
    echo -n "Continue with ${#AVAILABLE_DEVICES[@]} available device(s)? [y/N]: "
    read continue_choice
    if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
        echo "Aborting."
        exit 1
    fi
fi

NUM_CAMERAS=${#AVAILABLE_DEVICES[@]}
echo ""
echo "Recording with $NUM_CAMERAS camera(s)"

# Request output directory with default
default_output_dir="./recorded_videos"
echo -n "Enter output directory [$default_output_dir]: "
read output_dir
output_dir=${output_dir:-$default_output_dir}

# Create output directory if it doesn't exist
mkdir -p "$output_dir"

# Check disk space before starting recording
echo "Checking disk space..."
python3 "$SCRIPT_DIR/disk_space_check.py" --path "$output_dir"
if [ $? -ne 0 ]; then
    echo "❌ Disk space check failed. Please free up disk space and try again."
    exit 1
fi

# Initialize name template
name_template=name_video_time
# Request name and collect time
echo -n "Enter name: "
read name
time=$(date +%g%m%d-%H%M%S)
# Generate final name using input name and time
fin_name=${name_template/name/$name}
fin_name=${fin_name/time/$time}
echo "File name : $fin_name"

# Duration set to very large number, script is killed to stop recording
duration=180
frames=$(expr 30 \* 60 \* $duration)

# Make directory to store everything using final name inside output directory
mkdir -p "$output_dir/$fin_name"
cd "$output_dir/$fin_name"

# Build device list for parallel execution
DEVICE_LIST=""
for i in "${!AVAILABLE_DEVICES[@]}"; do
    if [ -n "$DEVICE_LIST" ]; then
        DEVICE_LIST="$DEVICE_LIST\n$i:${AVAILABLE_DEVICES[$i]}"
    else
        DEVICE_LIST="$i:${AVAILABLE_DEVICES[$i]}"
    fi
done

# Generate string to be evaluated
exec_string="echo -e '$DEVICE_LIST' | parallel -j $NUM_CAMERAS --colsep ':' streamer -q -c {2} -s 1280x720 -f jpeg -t frames -r 30 -j 75 -w 0 -o name_cam{1}.avi"

time_file="name_markers.txt"
time_file=${time_file/name/$fin_name}
exec_string=${exec_string/name/$fin_name}
exec_string=${exec_string/frames/$frames}

figlet "ctrl+c to stop"

# Write start and stop time and execute video recording
echo "Start time : $(date)"
echo

date +%s.%N | cut -b-14 > $time_file
eval $exec_string
echo "Stop time : $(date)"
echo
date +%s.%N | cut -b-14 >> $time_file
