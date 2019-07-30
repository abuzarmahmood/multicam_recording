#!/bin/bash

: '
Script to simulatenously record from 2 cameras
When run requests input for filename and time in minutes
Outputs:
-Video files
-Marker text file (start and stop times for recording)
'
# Initialize name template
name_template=name_time
# Request name and collect time
echo -n "Enter name: "
read name
time=$(date +%g%m%d-%H%M%S)
# Generate final name using input name and time
fin_name=${name_template/name/$name}
fin_name=${fin_name/time/$time}
echo $fin_name

# Request duration of video recording and calculate total frames
echo -n "Enter duration (in minutes) : "
read duration
frames=$(expr 30 \* 60 \* $duration)
echo $frames

# Make directory to store everything using final name
mkdir $fin_name
cd $fin_name

# Generate string to be evaluated
exec_string="seq 0 1 | parallel -j 2 streamer -q -c /dev/video{} -s 1280x720 -f jpeg -t frames -r 30 -j 75 -w 0 -o name_cam{}.avi"

time_file="name_markers.txt"
time_file=${time_file/name/$fin_name}
exec_string=${exec_string/name/$fin_name}
exec_string=${exec_string/frames/$frames}

# Write start and stop time and execute video recording
echo "Start time : $(date)"
date +%s.%N | cut -b-14 > $time_file
eval $exec_string
date +%s.%N | cut -b-14 >> $time_file
