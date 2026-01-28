#!/bin/bash

: '
Script to simultaneously record from 2 cameras using ffmpeg
When run requests input for filename and time in minutes
Outputs:
-Video files (MP4 format with H.264 encoding)
-Marker text file (start and stop times for recording)
'
# Check disk space before starting recording
echo "Checking disk space..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/disk_space_check.py" --path .
if [ $? -ne 0 ]; then
    echo "❌ Disk space check failed. Please free up disk space and try again."
    exit 1
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

# Make directory to store everything using final name
mkdir $fin_name
cd $fin_name

# Generate string to be evaluated using ffmpeg for video recording
exec_string="seq 0 1 | parallel -j 2 ffmpeg -f v4l2 -i /dev/video{} -s 1280x720 -r 30 -c:v libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p name_cam{}.mp4"

time_file="name_markers.txt"
time_file=${time_file/name/$fin_name}
exec_string=${exec_string/name/$fin_name}

figlet "ctrl+c to stop"

# Write start and stop time and execute video recording
echo "Start time : $(date)"
echo

date +%s.%N | cut -b-14 > $time_file
eval $exec_string
echo "Stop time : $(date)"
echo
date +%s.%N | cut -b-14 >> $time_file
