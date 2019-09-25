"""
Script to split video files according to trial times
For usage, type python split_script.py -h
"""

# ___       _ _   _       _ _         
#|_ _|_ __ (_) |_(_) __ _| (_)_______ 
# | || '_ \| | __| |/ _` | | |_  / _ \
# | || | | | | |_| | (_| | | |/ /  __/
#|___|_| |_|_|\__|_|\__,_|_|_/___\___|
#                                     

# Collect filenames to be used for processing

import argparse

parser = argparse.ArgumentParser(description = 'Collects names of files to process')
parser.add_argument('marker_file', help = 'File containing start and end times of file')
parser.add_argument('triallist_file', help = 'File containing timestamp of each trial')
parser.add_argument('video_file', help = 'All video files to process', nargs = '+')
args = parser.parse_args()


# Print what files are being used
print('\n')
print('Marker file : {}'.format(args.marker_file))
print('Trial list file: {}'.format(args.triallist_file))
print('Video files : {}'.format(args.video_file))

# Check how the file needs to be cut
while True:
    trial_bool = (input(\
            "Enter 1 if taste trials, 0 if affective, and >=2 to exit: \n"))
    try:
        trial_bool = int(trial_bool)
        if trial_bool >=2:
            print('Exiting')
            exit() 
        elif trial_bool not in [1,0]:
            print('Please enter 0,1 or >=2')
        else:
            break
    except:
        print('Please enter 0,1 or >=2')
# ___                            _    
#|_ _|_ __ ___  _ __   ___  _ __| |_  
# | || '_ ` _ \| '_ \ / _ \| '__| __| 
# | || | | | | | |_) | (_) | |  | |_  
#|___|_| |_| |_| .__/ \___/|_|   \__| 
#              |_|                    

import cv2
import glob
import re
import numpy as np
import pylab as plt
from tqdm import tqdm
import os
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

# ____       _               
#/ ___|  ___| |_ _   _ _ __  
#\___ \ / _ \ __| | | | '_ \ 
# ___) |  __/ |_| |_| | |_) |
#|____/ \___|\__|\__,_| .__/ 
#                     |_|    

def read_timelist(filename):
    """
    Define list reader
    """
    with open(filename,'r') as file:
        timelist = [float(line) for line in file]
    return timelist

# Initialize filenames

video_files = args.video_file
marker_file = args.marker_file 
triallist_file = args.triallist_file
directory = os.path.dirname(os.path.abspath(marker_file))

# Load list files
marker_vec = np.asarray(read_timelist(marker_file))
trial_vec = np.asarray(read_timelist(triallist_file))

# Initialize Paramteres
frame_rate = 30.0
# Define how much before and after the trial we want
t_prior = 5
t_post = 5

# Convert trial markers to time from start of video
trial_times = trial_vec - marker_vec[0]

# If tastes, return array with times before and after trial
# If affective, simply return start and end times as denoted by marker file
if trial_bool:
    split_times = np.asarray([trial_times-t_prior,trial_times+t_post])
else:
    split_times = trial_times[:,np.newaxis]

#  ____ _   _  ___  ____     ____ _   _  ___  ____  
# / ___| | | |/ _ \|  _ \   / ___| | | |/ _ \|  _ \ 
#| |   | |_| | | | | |_) | | |   | |_| | | | | |_) |
#| |___|  _  | |_| |  __/  | |___|  _  | |_| |  __/ 
# \____|_| |_|\___/|_|      \____|_| |_|\___/|_|    
#                                                   

# Open video file, extract frames bookending a delivery and write to new video
for video_num in range(len(video_files)):
    for trial_num in tqdm(range(split_times.shape[1])):

        # Open file to be split
        trial = split_times[:,trial_num]
        video_name = video_files[video_num]

        # Write out the list of frames at the appropriate framerate
        output_name = directory + '/' + 'trial{}_cam{}.avi'.format(trial_num,video_num)

        # Feed parameters to ffmpeg_extract_subclip
        ffmpeg_extract_subclip(video_name, trial[0], trial[1], targetname=output_name)
