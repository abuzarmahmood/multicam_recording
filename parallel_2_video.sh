#!/bin/bash

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

mkdir $fin_name
cd $fin_name

exec_string="seq 0 1 | parallel -j 2 streamer -q -c /dev/video{} -s 1280x720 -f jpeg -t frames -r 30 -j 75 -w 0 -o name_cam{}.avi"

time_file0="name_markers.txt"
time_file0=${time_file0/name/$fin_name}
exec_string=${exec_string/name/$fin_name}
exec_string=${exec_string/frames/$frames}

echo "Start time : $(date)"
date +%s.%N | cut -b-14 > $time_file0
#date > $time_file0
eval $exec_string
#date >> $time_file0
date +%s.%N | cut -b-14 >> $time_file0
