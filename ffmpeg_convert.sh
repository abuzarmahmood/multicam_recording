#!/bin/bash

: '
Input a pattern to pull out files for conversion.
INPUT and OUTPUT files are almost the same in terms of video.
This conversion corrects *some bug* (not identified yet) because \
	of which CV2 does not recognize the right number of frames

Usage : ffmpeg_convert.sh <pattern_string>
'

pattern_str="*pattern*"
echo "Converting files :"
find -name "${pattern_str/pattern/$1}" | cat
echo
find -name "${pattern_str/pattern/$1}" | parallel ffmpeg -i {} -b:v 100000k {}_converted.avi
