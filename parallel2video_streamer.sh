#!/bin/bash

: '
Script to simultaneously record from 2 cameras
When run requests input for filename and time in minutes
Outputs:
-Video files
-Marker text file (start and stop times for recording)
'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/recording_utils.sh"
source "$SCRIPT_DIR/ramdisk_utils.sh"

# Help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help "$0" "streamer" "JPEG" "avi"
    exit 0
fi

# Load video devices from config
load_video_devices "$SCRIPT_DIR" || exit 1

# Setup output directory with disk space check
setup_output_directory "$SCRIPT_DIR" || exit 1

# Generate recording name
generate_recording_name

# Duration set to very large number, script is killed to stop recording
duration=180
frames=$(expr 30 \* 60 \* $duration)

# Setup ramdisk if enabled
setup_ramdisk "$SCRIPT_DIR"
FINAL_OUTPUT_DIR="$output_dir/$fin_name"

# Get recording path (ramdisk or disk)
recording_path=$(get_recording_path "$output_dir" "$fin_name")

# Setup recording directory (use ramdisk path if available)
mkdir -p "$recording_path"
cd "$recording_path"

if [ "$RAMDISK_ACTIVE" -eq 1 ]; then
    echo "Recording to ramdisk: $recording_path"
    echo "Final destination: $FINAL_OUTPUT_DIR"
else
    echo "Recording to disk: $recording_path"
fi

# Build device list for parallel execution
build_device_list

# Generate string to be evaluated using streamer for video recording
exec_string="echo -e '$DEVICE_LIST' | parallel -j $NUM_CAMERAS --colsep ':' streamer -q -c {2} -s 1280x720 -f jpeg -t $frames -r 30 -j 75 -w 0 -o ${fin_name}_cam{1}.avi"

time_file="${fin_name}_markers.txt"

# Start recording with marker
start_recording "$time_file"

# Execute video recording
eval $exec_string

# Stop recording with marker
stop_recording "$time_file"

# Move files from ramdisk to final destination if ramdisk was used
if [ "$RAMDISK_ACTIVE" -eq 1 ] && [ -n "$FINAL_OUTPUT_DIR" ]; then
    move_from_ramdisk "$(pwd)" "$FINAL_OUTPUT_DIR"
    cd "$FINAL_OUTPUT_DIR"
fi

# Cleanup ramdisk
cleanup_ramdisk "$SCRIPT_DIR"

echo "Recording complete!"
