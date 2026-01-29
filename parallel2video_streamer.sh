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

# Setup recording directory
setup_recording_directory "$output_dir" "$fin_name"

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
