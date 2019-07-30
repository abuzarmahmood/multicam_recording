pattern_str="*pattern*"
echo "Converting files :"
find -name "${pattern_str/pattern/$1}" | cat
echo
find -name "${pattern_str/pattern/$1}" | parallel ffmpeg -i {} -b:v 100000k {}_converted.avi
