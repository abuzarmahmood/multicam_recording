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
source "$SCRIPT_DIR/ramdisk_utils.sh"

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
    
    # Move files from ramdisk to final destination if ramdisk was used
    if [ "$RAMDISK_ACTIVE" -eq 1 ] && [ -n "$FINAL_OUTPUT_DIR" ]; then
        move_from_ramdisk "$(pwd)" "$FINAL_OUTPUT_DIR"
        cd "$FINAL_OUTPUT_DIR"
    fi
    
    # Cleanup ramdisk
    cleanup_ramdisk "$SCRIPT_DIR"
    
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

# Ask for single channel recording option
echo -n "Record single channel (Y/luminance only) for better performance? (y/n): "
read single_channel

# Generate string to be evaluated using ffmpeg for video recording
# Uses -use_wallclock_as_timestamps 1 to save wall-clock timestamps in video files
if [[ "$single_channel" =~ ^[Yy]$ ]]; then
    echo "Recording single channel (Y/luminance only) for better performance..."
    exec_string="echo -e '$DEVICE_LIST' | parallel -j $NUM_CAMERAS --colsep ':' ffmpeg -use_wallclock_as_timestamps 1 -copyts -f v4l2 -i {2} -s 1280x720 -r 30 -vf \"extractplanes=y\" -c:v libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p name_cam{1}.mp4"
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
echo "Extracting timestamps from video files..."
for i in $(seq 0 $((NUM_CAMERAS - 1))); do
    video_file="name_cam${i}.mp4"
    timestamps_file="cam${i}_timestamps.txt"
    if [ -f $video_file ]; then
        echo "Extracting timestamps from ${video_file}..." 
        ffmpeg -i $video_file -f mkvtimestamp_v2 -copyts $timestamps_file 2>/dev/null
        echo "Timestamps saved to ${timestamps_file}" 
    fi
done

# Move files from ramdisk to final destination if ramdisk was used
if [ "$RAMDISK_ACTIVE" -eq 1 ] && [ -n "$FINAL_OUTPUT_DIR" ]; then
    move_from_ramdisk "$(pwd)" "$FINAL_OUTPUT_DIR"
    cd "$FINAL_OUTPUT_DIR"
fi

# Cleanup ramdisk
cleanup_ramdisk "$SCRIPT_DIR"

echo "Recording and timestamp extraction complete!"
