#!/bin/bash
ffmpeg -f video4linux2 -input_format mjpeg -framerate 30 -video_size 1280x720 -i /dev/video0 -b:v 10000k out0.mpeg
