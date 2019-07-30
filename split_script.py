# ___       _ _   _       _ _         
#|_ _|_ __ (_) |_(_) __ _| (_)_______ 
# | || '_ \| | __| |/ _` | | |_  / _ \
# | || | | | | |_| | (_| | | |/ /  __/
#|___|_| |_|_|\__|_|\__,_|_|_/___\___|
#                                     

import argparse

parser = argparse.ArgumentParser(description = 'Collects names of files to process')
parser.add_argument('marker_file', help = 'File containing start and end times of file')
parser.add_argument('triallist_file', help = 'File containing timestamp of each trial')
parser.add_argument('video_file', help = 'All video files to process', nargs = '+')
args = parser.parse_args()

print('\n')
print('Marker file : {}'.format(args.marker_file))
print('Trial list file: {}'.format(args.triallist_file))
print('Video files : {}'.format(args.video_file))

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

# ____       _               
#/ ___|  ___| |_ _   _ _ __  
#\___ \ / _ \ __| | | | '_ \ 
# ___) |  __/ |_| |_| | |_) |
#|____/ \___|\__|\__,_| .__/ 
#                     |_|    

# Define functions to be used

def get_total_frames(filename):
    return cv2.VideoCapture(filename).get(7)

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

# Initialize Paramteres
frame_rate = 30.0
# Define how much before and after the trial we want
t_prior = 5
t_post = 5

# Assuming uniform frame rate, how many frames would this be
t_prior_frames = np.ceil(t_prior * frame_rate).astype('int')
t_post_frames = np.ceil(t_post * frame_rate).astype('int')

# Load list files
#frame_list = read_timelist(framelist_file)
marker_list = read_timelist(marker_file)
trial_list = read_timelist(triallist_file)

# Get total number of frames from file
frame_count_list = [get_total_frames(file) for file in video_files]
frame_times_list = [np.linspace(marker_list[0],marker_list[1],frame_count)\
        for frame_count in frame_count_list]
frame_inds_list = [[np.argmin(np.abs(trial - frame_times)) for trial in trial_list]\
                for frame_times in frame_times_list]

# Make a list of tuples to describe start and stop points for every video
split_markers_list = [[(trial-t_prior_frames,trial+t_post_frames) \
        for trial in frame_inds] \
        for frame_inds in frame_inds_list]

#  ____ _   _  ___  ____     ____ _   _  ___  ____  
# / ___| | | |/ _ \|  _ \   / ___| | | |/ _ \|  _ \ 
#| |   | |_| | | | | |_) | | |   | |_| | | | | |_) |
#| |___|  _  | |_| |  __/  | |___|  _  | |_| |  __/ 
# \____|_| |_|\___/|_|      \____|_| |_|\___/|_|    
#                                                   

for video_num in range(len(video_files)):
    for trial_num in tqdm(range(len(split_markers_list[video_num]))):
        trial = split_markers_list[video_num][trial_num]
        video_name = video_files[video_num]
        cap = cv2.VideoCapture(video_name)
        cap.set(1,trial[0])
        frame_count = trial[0]
        saved_frame_count = 0
        success = 1
        frame_list = []
        while success and saved_frame_count <= (trial[1]-trial[0]):
            if frame_count <= trial[1] and frame_count >= trial[0]:
                success, frame = cap.read()
                frame_list.append(frame)
                frame_count += 1 
                saved_frame_count += 1
            else:
                success, frame = cap.read()
                frame_count += 1 
        cap.release()
        
        # Write out the list of frames at the appropriate framerate
        resolution = (frame_list[0].shape[1],frame_list[0].shape[0])
        output_name = directory + '/' + 'trial{}_cam{}.avi'.format(trial_num,video_num)
        writer = cv2.VideoWriter(output_name,
                               cv2.VideoWriter_fourcc(*'XVID'), 
                               frame_rate, 
                               resolution) 
        
        for frame in frame_list:
            writer.write(frame)
        writer.release()



# Half-baked functions to clean-up script above (in the future)

def write_module(list_of_frames, output_name, frame_rate):
    """
    list_of_frames :: all frames to be output in a single file
    output_name :: name of file to be output
    """
    resolution = list_of_frames[0].shape 
    
    writer = cv2.VideoWriter(output_name,
                           cv2.VideoWriter_fourcc('M','J','P','G'), 
                           frame_rate, 
                           resolution) 
   
    for frame in list_of_frames:
        writer.write(frame)
    writer.release()

def split_module(video_capture, split_markers):
    """
    Parses single video file according to markers
    all_markers :: list of tuples of (start,end) splits
    """

    video_name = video_files[0]
    cap = cv2.VideoCapture(video_name)
    for trial in split_markers[0]:
        cap.set(2,trial[0])
        frame_count = 0
        success = 1
        frame_list = []
        while success and frame_count <= (trial[0]-trial[1]):
            success, frame = cap.read()
            frame_list.append(frame)
            frame_count += 1 

    cap.release() 
