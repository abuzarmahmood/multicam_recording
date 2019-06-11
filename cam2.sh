#!/bin/bash
echo $(($(date +%s%N)/1000000))
streamer -q -c /dev/video2 -s 1280x720 -f jpeg -t 180 -r 30 -j 75 -w 0 -o video2.avi
