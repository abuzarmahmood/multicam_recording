seq 0 1 | parallel -j 2 streamer -q -c /dev/video{} -s 1280x720 -f jpeg -t 600 -r 30 -j 75 -w 0 -o video{}.avi
