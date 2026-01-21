#!/bin/bash

: '
Script to simulatenously record from 2 cameras
When run requests input for filename and time in minutes
Outputs:
-Video files
-Marker text file (start and stop times for recording)
FIXED: Cameras now start recording at exactly the same time to fix sync issues
'
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

# Calculate future start time (3 seconds from now to ensure all processes are ready)
start_time=$(($(date +%s) + 3))
echo "All cameras will start recording at: $(date -d @$start_time)"

# Create a function that waits until the specified time before starting streamer
start_streamer_at_time() {
    local camera_id=$1
    local output_file=$2
    local frame_count=$3
    local target_time=$4
    
    # Wait until the target time
    current_time=$(date +%s)
    if [ $current_time -lt $target_time ]; then
        sleep $((target_time - current_time))
    fi
    
    # Start recording at exactly the target time
    streamer -q -c /dev/video$camera_id -s 1280x720 -f jpeg -t $frame_count -r 30 -j 75 -w 0 -o $output_file
}

# Export the function so parallel can use it
export -f start_streamer_at_time

# Generate string to be evaluated with synchronized start time
exec_string="seq 0 1 | parallel -j 2 start_streamer_at_time {} name_cam{}.avi $frames $start_time"

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
