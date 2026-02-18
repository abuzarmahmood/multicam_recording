#!/bin/bash

# Wrapper script to run parallel2video_ffmpeg.sh with tee logging

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_SCRIPT="$SCRIPT_DIR/parallel2video_ffmpeg.sh"

if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "Error: parallel2video_ffmpeg.sh not found in $SCRIPT_DIR"
    exit 1
fi

if [ ! -x "$MAIN_SCRIPT" ]; then
    echo "Error: parallel2video_ffmpeg.sh is not executable"
    exit 1
fi

# Generate log filename with timestamp
TIMESTAMP=$(date +%g%m%d-%H%M%S)
LOG_FILE="${TIMESTAMP}_recording.log"

# Run the main script with tee
# This will show output on terminal AND save to log file
"$MAIN_SCRIPT" 2>&1 | tee "$LOG_FILE"
