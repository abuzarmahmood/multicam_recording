#!/bin/bash

#echo -n "Enter something : "
#read statement
#echo -n "Here is what you typed"
#echo $statement

name_template=name_time
echo -n "Enter name: "
read name
fin_name=${name_template/name/$name}
time=$(date +%g%m%d-%H%M%S)
fin_name=${fin_name/time/$time}
echo $fin_name

echo -n "Enter duration (in minutes) : "
read duration
frames=$(expr 30 \* 60 \* $duration)
echo $frames

#date +%s.%N | cut -b-14 > time_test.txt
#sleep 5
#date +%s.%N | cut -b-14 >> time_test.txt

file0="streamer -q -c /dev/video0 -s 1280x720 -f jpeg -t total_frames -r 30 -j 75 -w 0 -o name_cam0.avi"
file1="streamer -q -c /dev/video1 -s 1280x720 -f jpeg -t total_frames -r 30 -j 75 -w 0 -o name_cam1.avi"

time_file0="name_cam0_frames.txt"
time_file1="name_cam1_frames.txt"

file0=${file0/total_frames/$frames}
file1=${file1/total_frames/$frames}
file0=${file0/name/$fin_name}
file1=${file1/name/$fin_name}
time_file0=${time_file0/name/$fin_name}
time_file1=${time_file1/name/$fin_name}

echo "date +%s.%N | cut -b-14 > $time_file0" > cam0.sh
echo $file0 >> cam0.sh
echo "date +%s.%N | cut -b-14 > $time_file0" >> cam0.sh

echo "date +%s.%N | cut -b-14 > $time_file0" > cam1.sh
echo $file0 >> cam1.sh
echo "date +%s.%N | cut -b-14 > $time_file0" >> cam1.sh

find . -name '*.sh' | parallel

