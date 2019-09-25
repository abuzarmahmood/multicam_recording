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
from split_funcs import *
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

# ____        __ _              _____                     
#|  _ \  ___ / _(_)_ __   ___  |  ___|   _ _ __   ___ ___ 
#| | | |/ _ \ |_| | '_ \ / _ \ | |_ | | | | '_ \ / __/ __|
#| |_| |  __/  _| | | | |  __/ |  _|| |_| | | | | (__\__ \
#|____/ \___|_| |_|_| |_|\___| |_|   \__,_|_| |_|\___|___/
                                                         

def get_total_frames(filename):
    """
    Uses CV2 VideoCapture modules to extract frame count from video file
    """
    return cv2.VideoCapture(filename).get(7)

def read_timelist(filename):
    """
    Define list reader
    """
    with open(filename,'r') as file:
        timelist = [float(line) for line in file]
    return timelist

def calculate_frame_inds(marker_list, frame_count_list, trial_list):
    """
    Finds index of frames closest to trial markers
    """
    # Assuming every frame is evenly spaced, infer time for every frame
    frame_times_list = [np.linspace(marker_list[0],marker_list[1],frame_count)\
            for frame_count in frame_count_list]

    # Find closest frame to marker for every trial
    frame_inds_list = [[np.argmin(np.abs(trial - frame_times)) for trial in trial_list]\
                    for frame_times in frame_times_list]

    return frame_inds_list

def calculate_split_markers(frame_inds_list, prior_post_tuple, trial_bool):
    """
    function to calculation split markers to chop file by
    For trials, gives index of frames before and after start of trial
    For affective, simply returns index of start and end
    """
    # From frames closest to trial start time, find frames bounding
    # a pre-defined period before and after
    if trial_bool:
        t_prior_frames = prior_post_tuple[0]
        t_post_frames = prior_post_tuple[1]
        # Make a list of tuples to describe start and stop points for every video
        split_markers_list = [[(trial-t_prior_frames,trial+t_post_frames) \
                for trial in frame_inds] \
                for frame_inds in frame_inds_list]

    # If not trials, just big chunk of video, return as is
    # This is to keep execution flow the same for all video
    else:
        split_markers_list = [frame_inds_list]

    return split_markers_list
# ____       _               
#/ ___|  ___| |_ _   _ _ __  
#\___ \ / _ \ __| | | | '_ \ 
# ___) |  __/ |_| |_| | |_) |
#|____/ \___|\__|\__,_| .__/ 
#                     |_|    

# Initialize filenames

video_files = args.video_file
marker_file = args.marker_file 
triallist_file = args.triallist_file
directory = os.path.dirname(os.path.abspath(marker_file))

# Load list files
marker_list = read_timelist(marker_file)
trial_list = read_timelist(triallist_file)

# Initialize Paramteres
frame_rate = 30.0
# Define how much before and after the trial we want
t_prior = 5
t_post = 5

# Assuming uniform frame rate, how many frames would this be
t_prior_frames = np.ceil(t_prior * frame_rate).astype('int')
t_post_frames = np.ceil(t_post * frame_rate).astype('int')

# Get total number of frames from file
frame_count_list = [get_total_frames(file) for file in video_files]

# Find frames closest to markers
frame_inds_list = calculate_frame_inds(marker_list, frame_count_list, trial_list)
split_markers_list= calculate_split_markers(frame_inds_list,
        (t_prior_frames,t_post_frames), trial_bool)

# Convert inds to times 
split_times_list = [ [(trials[0]/frame_rate,trials[1]/frame_rate) \
        for trials in video ]\
        for video in split_markers_list]

#  ____ _   _  ___  ____     ____ _   _  ___  ____  
# / ___| | | |/ _ \|  _ \   / ___| | | |/ _ \|  _ \ 
#| |   | |_| | | | | |_) | | |   | |_| | | | | |_) |
#| |___|  _  | |_| |  __/  | |___|  _  | |_| |  __/ 
# \____|_| |_|\___/|_|      \____|_| |_|\___/|_|    
#                                                   

# Open video file, extract frames bookending a delivery and write to new video
for video_num in range(len(video_files)):
    for trial_num in tqdm(range(len(split_markers_list[video_num]))):

        # Open file to be split
        trial = split_times_list[video_num][trial_num]
        video_name = video_files[video_num]

        # Write out the list of frames at the appropriate framerate
        output_name = directory + '/' + 'trial{}_cam{}.avi'.format(trial_num,video_num)

        # Feed parameters to ffmpeg_extract_subclip
        ffmpeg_extract_subclip(video_name, trial[0], trial[1], targetname=output_name)
