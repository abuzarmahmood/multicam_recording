#!/bin/bash

: '
GUI wrapper for transcode_copy_videos.sh
Provides a user-friendly interface for transcoding videos recorded with -c:v copy flag
'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if zenity is available
if ! command -v zenity &> /dev/null; then
    echo "Error: zenity is not installed. Please install it with:"
    echo "sudo apt-get install zenity"
    exit 1
fi

# Check if the main transcoding script exists
if [[ ! -f "$SCRIPT_DIR/transcode_copy_videos.sh" ]]; then
    zenity --error --text="transcode_copy_videos.sh not found in the postprocessing directory"
    exit 1
fi

# Launch the GUI mode of the main script
exec "$SCRIPT_DIR/transcode_copy_videos.sh" --gui
