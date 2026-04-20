#!/bin/bash

folder=$(zenity --file-selection --directory \
    --title="Find folder to search for files in")

testlist=$(echo "" $(find "$folder" -name "*.avi*" | sort) | sed 's/ /\nFALSE\n/g')

files=$(zenity --list --checklist --title="Check files to convert" \
    --column="Check" --column="Files names" $testlist --width=600 --height=400)

# If no files selected terminate rest of script
#if [ wc files ] then
#    echo "No file selected"
#    exit 0
#fi

files=$(echo $files | tr "|" "\n")
echo "Converting files:"
echo "$files"
echo

echo "$files" | parallel ffmpeg -i {} -b:v 2500k {}_converted.avi
