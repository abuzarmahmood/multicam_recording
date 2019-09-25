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
split_markers_list = calculate_split_markers(frame_inds_list,
        (t_prior_frames,t_post_frames), trial_bool)

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
        trial = split_markers_list[video_num][trial_num]
        video_name = video_files[video_num]
        cap = cv2.VideoCapture(video_name)

        # Initialize progress bar
        pbar = tqdm(total = frame_count_list[video_num]) 

        # Resolution width-first
        #resolution = (frame_list[0].shape[1],frame_list[0].shape[0])
        resolution = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        # Write out the list of frames at the appropriate framerate
        output_name = directory + '/' + 'trial{}_cam{}.avi'.format(trial_num,video_num)
        writer = cv2.VideoWriter(output_name,
                               cv2.VideoWriter_fourcc(*'XVID'), 
                               frame_rate, 
                               resolution) 

        cap.set(1,trial[0])
        frame_count = trial[0]
        saved_frame_count = 0
        success = 1
        frame_list = []
        while success and saved_frame_count <= (trial[1]-trial[0]):
            if frame_count <= trial[1] and frame_count >= trial[0]:
                success, frame = cap.read()
                writer.write(frame)
                #frame_list.append(frame)
                frame_count += 1 
                saved_frame_count += 1

                # Update progress bar
                pbar.update(1)

            else:
                success, frame = cap.read()
                frame_count += 1 
                # Update progress bar
                pbar.update(1)

        pbar.close()
        cap.release()
        
