#!/bin/bash

: '
Script to simultaneously record from 2 cameras using ffmpeg
When run requests input for filename and time in minutes
Outputs:
-Video files (MP4 format with H.264 encoding)
-Marker text file (start and stop times for recording)

Options:
- Single channel recording: Uses extractplanes filter to record only Y (luminance) channel for better performance
- Normal recording: Records full color video
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

# Duration set to very large number, script is killed to stop recording
duration=180

# Setup recording directory
setup_recording_directory "$output_dir" "$fin_name"

# Build device list for parallel execution
build_device_list

# Ask for single channel recording option
echo -n "Record single channel (Y/luminance only) for better performance? (y/n): "
read single_channel

# Ask for copy mode option (no transcoding, faster but no scaling/luminance extraction)
echo -n "Use copy mode (-c:v copy) for faster recording? (y/n): "
read copy_mode

# Generate string to be evaluated using ffmpeg for video recording
# Uses -use_wallclock_as_timestamps 1 to save wall-clock timestamps in video files
if [[ "$single_channel" =~ ^[Yy]$ ]]; then
    echo "Recording single channel (Y/luminance only) for better performance..."
    exec_string="echo -e '$DEVICE_LIST' | parallel -j $NUM_CAMERAS --colsep ':' ffmpeg -use_wallclock_as_timestamps 1 -copyts -f v4l2 -i {2} -s 1280x720 -r 30 -vf \"extractplanes=y\" -c:v libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p name_cam{1}.mp4"
elif [[ "$copy_mode" =~ ^[Yy]$ ]]; then
    echo "Recording with copy mode (-c:v copy) - no transcoding, faster capture but no scaling or luminance extraction..."
    # Note: -c:v copy skips encoding, but we still need v4l2 for input and can't apply filters
    exec_string="echo -e '$DEVICE_LIST' | parallel -j $NUM_CAMERAS --colsep ':' ffmpeg -use_wallclock_as_timestamps 1 -copyts -f v4l2 -input_format mjpeg -i {2} -r 60 -c:v copy name_cam{1}.mp4"
else
    echo "Recording full color video..."
    exec_string="echo -e '$DEVICE_LIST' | parallel -j $NUM_CAMERAS --colsep ':' ffmpeg -use_wallclock_as_timestamps 1 -copyts -f v4l2 -i {2} -s 1280x720 -r 30 -c:v libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p name_cam{1}.mp4"
fi

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
