#!/bin/bash

: '
Script to simulatenously record from 2 cameras
When run requests input for filename and time in minutes
Outputs:
-Video files
-Marker text file (start and stop times for recording)
'

# Help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo ""
    echo "Record video from 2 cameras simultaneously using streamer."
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message and exit"
    echo ""
    echo "Inputs (prompted interactively):"
    echo "  name          Base name for output files"
    echo ""
    echo "Outputs:"
    echo "  <name>_video_<timestamp>/           Directory containing all outputs"
    echo "  <name>_video_<timestamp>_cam0.avi   Video from camera 0 (JPEG, 1280x720, 30fps)"
    echo "  <name>_video_<timestamp>_cam1.avi   Video from camera 1 (JPEG, 1280x720, 30fps)"
    echo "  <name>_video_<timestamp>_markers.txt  Start/stop timestamps (Unix epoch)"
    echo ""
    echo "Requirements:"
    echo "  - streamer"
    echo "  - GNU parallel"
    echo "  - figlet"
    echo "  - Two video devices at /dev/video0 and /dev/video1"
    echo ""
    echo "Press Ctrl+C to stop recording."
    exit 0
fi

# Initialize name template
name_template=name_video_time
# Request name and collect time
echo -n "Enter name: "
read name
time=$(date +%g%m%d-%H%M%S)
# Generate final name using input name and time
fin_name=${name_template/name/$name}
fin_name=${fin_name/time/$time}
echo "File name : $fin_name"

# Duration set to very large number, script is killed to stop recording
duration=180
frames=$(expr 30 \* 60 \* $duration)

# Make directory to store everything using final name
mkdir $fin_name
cd $fin_name

# Generate string to be evaluated
exec_string="seq 0 1 | parallel -j 2 streamer -q -c /dev/video{} -s 1280x720 -f jpeg -t frames -r 30 -j 75 -w 0 -o name_cam{}.avi"

time_file="name_markers.txt"
time_file=${time_file/name/$fin_name}
exec_string=${exec_string/name/$fin_name}
exec_string=${exec_string/frames/$frames}

figlet "ctrl+c to stop"

# Write start and stop time and execute video recording
echo "Start time : $(date)"
echo

date +%s.%N | cut -b-14 > $time_file
eval $exec_string
echo "Stop time : $(date)"
echo
date +%s.%N | cut -b-14 >> $time_file
