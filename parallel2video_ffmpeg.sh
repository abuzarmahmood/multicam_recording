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
source "$SCRIPT_DIR/utils/recording_utils.sh"

# Function to transcode recorded videos
transcode_videos() {
    echo ""
    echo "Starting transcoding of recorded videos..."
    echo "This will compress the videos using H.264 with CRF 23 and scale to 960px width."
    echo ""
    
    # Allow a brief moment for user to read the message
    sleep 2
    
    # Check if transcode script exists
    local transcode_script="$SCRIPT_DIR/postprocessing/transcode/transcode_simple.sh"
    if [[ ! -f "$transcode_script" ]]; then
        echo "Warning: Transcode script not found at $transcode_script"
        echo "Skipping transcoding. You can manually transcode later."
        return 0
    fi
    
    # Find all .mp4 files that were just recorded (don't have "coded" in filename)
    local video_files=()
    while IFS= read -r -d '' file; do
        local basename_file=$(basename "$file")
        if [[ "$basename_file" != *"coded"* ]]; then
            video_files+=("$file")
        fi
    done < <(find . -maxdepth 1 -name "*.mp4" -type f -print0)
    
    if [[ ${#video_files[@]} -eq 0 ]]; then
        echo "No video files found to transcode"
        return 0
    fi
    
    echo "Found ${#video_files[@]} video file(s) to transcode"
    
    # Call the transcode script with current directory
    "$transcode_script" .
    
    echo ""
    echo "All done!"
}

# Function to handle Ctrl+C
cleanup_on_interrupt() {
    echo "" >&2
    echo "Ctrl+C detected. Stopping recording..." >&2
    
    # Stop recording with marker
    if [ -n "$time_file" ]; then
        stop_recording "$time_file"
    fi
    
    echo "Recording complete!" >&2
    
    # Continue to transcoding instead of exiting
    transcode_videos
    exit 0
}

# Trap SIGINT (Ctrl+C)
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
exec_string="echo -e '$DEVICE_LIST' | parallel -j $NUM_CAMERAS --colsep ':' ffmpeg -use_wallclock_as_timestamps 1 -copyts -f v4l2 -input_format mjpeg -framerate 60 -i {2} -c:v copy ${base_name}_cam{1}.mp4"

time_file="${fin_name}_markers.txt"

# Start recording with marker
start_recording "$time_file"

# Execute video recording
eval $exec_string

# Stop recording with marker
stop_recording "$time_file"

echo "Recording complete!"

# Transcode all recorded videos
transcode_videos
