#!/bin/bash

: '
Script to combine multiple videos into a single frame showing all videos simultaneously
Uses zenity for GUI file selection
'

# Check if zenity is available
if ! command -v zenity &> /dev/null; then
    echo "Error: zenity is not installed. Please install zenity for GUI support."
    echo "On Ubuntu/Debian: sudo apt-get install zenity"
    echo "Or use the Python script directly: python3 combine_videos.py"
    exit 1
fi

# Check if ffmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed. Please install ffmpeg."
    echo "On Ubuntu/Debian: sudo apt-get install ffmpeg"
    exit 1
fi

# Select folder to search for videos
folder=$(zenity --file-selection --directory \
    --title="Find folder containing videos to combine")

if [ -z "$folder" ]; then
    echo "No folder selected. Exiting."
    exit 0
fi

# Find video files in the folder
testlist=$(echo "" $(find "$folder" -name "*.avi" -o -name "*.mp4" -o -name "*.mov" -o -name "*.mkv" | sort) | sed 's/ /\nFALSE\n/g')

if [ -z "$testlist" ]; then
    zenity --error --text="No video files found in the selected folder."
    exit 1
fi

# Select files to combine
files=$(zenity --list --checklist --title="Select videos to combine" \
    --column="Check" --column="Video files" $testlist --width=800 --height=600)

if [ -z "$files" ]; then
    echo "No files selected. Exiting."
    exit 0
fi

# Convert pipe-separated list to space-separated
files=$(echo $files | tr "|" " ")

# Select output file
output_file=$(zenity --file-selection --save \
    --title="Save combined video as..." \
    --file-filter="Video files | *.avi *.mp4 *.mkv" \
    --file-filter="All files | *")

if [ -z "$output_file" ]; then
    echo "No output file selected. Exiting."
    exit 0
fi

# Add extension if not present
if [[ ! "$output_file" =~ \.(avi|mp4|mkv|mov)$ ]]; then
    output_file="${output_file}.mp4"
fi

# Select grid layout
grid_layout=$(zenity --list --title="Select grid layout" \
    --column="Layout" --column="Description" \
    "auto" "Automatic layout based on number of videos" \
    "2x1" "2 videos, side by side" \
    "1x2" "2 videos, stacked vertically" \
    "2x2" "4 videos in 2x2 grid" \
    "3x1" "3 videos, side by side" \
    "1x3" "3 videos, stacked vertically" \
    --width=400 --height=300)

if [ -z "$grid_layout" ]; then
    grid_layout="auto"
fi

# Select quality
quality=$(zenity --list --title="Select output quality" \
    --column="Quality" --column="Description" \
    "high" "High quality (larger file)" \
    "medium" "Medium quality (balanced)" \
    "low" "Low quality (smaller file)" \
    --width=300 --height=200)

if [ -z "$quality" ]; then
    quality="high"
fi

# Select scale width
scale_width=$(zenity --entry --title="Video scale" \
    --text="Enter width for each video in pixels (default: 640):" \
    --entry-text="640")

if [ -z "$scale_width" ]; then
    scale_width="640"
fi

# Confirm operation
zenity --question --title="Confirm" --text="Combine $(echo $files | wc -w) videos into:\n$output_file\n\nLayout: $grid_layout\nQuality: $quality\nScale: ${scale_width}px\n\nProceed?"

if [ $? -ne 0 ]; then
    echo "Operation cancelled."
    exit 0
fi

echo "Combining videos:"
echo "$files"
echo "Output: $output_file"
echo "Layout: $grid_layout"
echo "Quality: $quality"
echo "Scale: $scale_width"
echo

# Run the Python script
python3 "$(dirname "$0")/combine_videos.py" $files \
    --output "$output_file" \
    --grid "$grid_layout" \
    --scale "$scale_width" \
    --quality "$quality"

# Check result
if [ $? -eq 0 ]; then
    zenity --info --title="Success" --text="Videos combined successfully!\n\nOutput saved to:\n$output_file"
else
    zenity --error --title="Error" --text="Failed to combine videos.\nPlease check the console output for details."
fi
