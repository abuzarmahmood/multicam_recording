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

# Function to transcode recorded videos
transcode_videos() {
    echo ""
    echo "Starting transcoding of recorded videos..."
    echo "This will compress the videos using H.264 with CRF 23 and scale to 960px width."
    echo "Press Ctrl+C to skip transcoding if you want to do it later."
    echo ""
    
    # Allow a brief moment for user to read the message
    sleep 2
    
    # Find all .mp4 files that don't have "coded" in their filename
    video_files=()
    while IFS= read -r -d '' file; do
        basename_file=$(basename "$file")
        if [[ "$basename_file" != *"coded"* ]]; then
            video_files+=("$file")
        fi
    done < <(find . -maxdepth 1 -name "*.mp4" -type f -print0)
    
    if [[ ${#video_files[@]} -gt 0 ]]; then
        echo "Found ${#video_files[@]} video file(s) to transcode"
        
        # Create coded subdirectory
        mkdir -p coded
        
        # Process each video file
        success_count=0
        for file in "${video_files[@]}"; do
            basename_file=$(basename "$file" .mp4)
            output_file="coded/${basename_file}_coded.mp4"
            
            echo "Transcoding: $file -> $output_file"
            
            if ffmpeg -i "$file" -c:v libx264 -crf 23 -vf scale=960:-1 "$output_file" 2>&1 | grep -E "time=|error"; then
                echo "✓ Successfully transcoded: $basename_file"
                ((success_count++))
            else
                echo "✗ Failed to transcode: $file"
            fi
            echo ""
        done
        
        echo "Transcoding completed: $success_count/${#video_files[@]} files processed successfully"
    else
        echo "No video files found to transcode"
    fi
    
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
exec_string="echo -e '$DEVICE_LIST' | parallel -j $NUM_CAMERAS --colsep ':' ffmpeg -use_wallclock_as_timestamps 1 -copyts -f v4l2 -input_format mjpeg -i {2} -r 60 -c:v copy name_cam{1}.mp4"

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
