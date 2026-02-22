#!/bin/bash

: '
Script to simultaneously record from 2 cameras using ffmpeg
When run requests input for filename and time in minutes
Outputs:
-Video files (MP4 format with copy mode - no transcoding)
-Marker text file (start and stop times for recording)

Uses copy mode (-c:v copy) for faster recording without transcoding
'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/recording_utils.sh"

# Function to handle Ctrl+C - ensures timestamps are extracted before exit
cleanup_on_interrupt() {
    echo "" >&2
    echo "Ctrl+C detected. Stopping recording and extracting timestamps..." >&2
    
    # Stop recording with marker
    if [ -n "$time_file" ]; then
        stop_recording "$time_file"
    fi
    
    # Extract timestamps from recorded video files
    echo "Extracting timestamps from video files..."
    for i in $(seq 0 $((NUM_CAMERAS - 1))); do
        # We are already in the recording directory
        video_file="name_cam${i}.mp4"
        timestamps_file="cam${i}_timestamps.txt"
        if [ -f $video_file ]; then
            echo "Extracting timestamps from ${video_file}..." 
            ffmpeg -i $video_file -f mkvtimestamp_v2 -copyts $timestamps_file 2>/dev/null
            echo "Timestamps saved to ${timestamps_file}" 
        fi
    done
    
    echo "Recording and timestamp extraction complete!" >&2
    exit 0
}

# Trap SIGINT (Ctrl+C) to ensure timestamps are written
trap cleanup_on_interrupt SIGINT

# Help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help "$0" "ffmpeg" "H.264" "mp4"
    exit 0
fi

# Load video devices from config
load_video_devices "$SCRIPT_DIR" || exit 1

# Setup output directory with disk space check
setup_output_directory "$SCRIPT_DIR" || exit 1

# Generate recording name
generate_recording_name

# Setup recording directory
setup_recording_directory "$output_dir" "$fin_name"

# Build device list for parallel execution
build_device_list

# Generate string to be evaluated using ffmpeg for video recording
# Uses -use_wallclock_as_timestamps 1 to save wall-clock timestamps in video files
# Uses copy mode (-c:v copy) for faster recording without transcoding
echo "Recording with copy mode (-c:v copy) - no transcoding, faster capture..."
exec_string="echo -e '$DEVICE_LIST' | parallel -j $NUM_CAMERAS --colsep ':' ffmpeg -use_wallclock_as_timestamps 1 -copyts -f v4l2 -input_format mjpeg -i {2} -r 60 -c:v copy name_cam{1}.mp4"

time_file="${fin_name}_markers.txt"

# Start recording with marker
start_recording "$time_file"

# Execute video recording
eval $exec_string

# Disable trap for normal exit to avoid duplicate cleanup
trap - SIGINT

# Stop recording with marker
stop_recording "$time_file"

# Extract timestamps from recorded video files
# If not interrupted, extract timestamps here
if [ $? -eq 0 ]; then
    cleanup_on_interrupt
fi

echo "Recording and timestamp extraction complete!"
