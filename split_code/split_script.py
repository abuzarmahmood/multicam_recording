
## Import modules 

import cv2
import glob
import re
import numpy as np
import pylab as plt
from tqdm import tqdm

# Initialize filenames

directory = '/media/bigdata/blech_codes/vid_recordings/BS46_Extra_190618-110823'
video_files = glob.glob( directory + '/**/*.avi', recursive=True)
framelist_file = glob.glob( directory + '/**/*framelist*', recursive=True)[0]
trial_list_file = glob.glob( directory + '/**/*trial_timelist*', recursive=True)[0]

# Initialize Paramteres
frame_rate = 30.0
# Define how much before and after the trial we want
t_prior = 2
t_post = 5

# Assuming uniform frame rate, how many frames would this be
t_prior_frames = np.ceil(t_prior * frame_rate).astype('int')
t_post_frames = np.ceil(t_post * frame_rate).astype('int')


def read_timelist(filename):
    """
    Define list reader
    """
    with open(filename,'r') as file:
        timelist = [float(line) for line in file]
    return timelist

# Load list files
frame_list = read_timelist(framelist_file)
trial_list = read_timelist(trial_list_file)

# Find frames in frame_list to every trial
frame_inds = [np.argmin((np.asarray(frame_list) - trial_time)**2) for \
                trial_time in trial_list] 

# Make a list of tuples to describe start and stop points for every video
split_markers = [(trial-t_prior_frames,trial+t_post_frames) for trial in frame_inds] 

import dill
## Save dill session
dill_filename = '/media/bigdata/blech_codes/vid_recordings/BS46_Extra_190618-110823' + '/' + 'dill_session.pkl'
#dill.dump_session(dill_filename)

## Load dill session
dill.load_session(dill_filename)


# CHOP CHOP
cam = 0

for trial_num in tqdm(range(len(split_markers))):
    video_name = video_files[cam]
    cap = cv2.VideoCapture(video_name)
    trial = split_markers[trial_num]
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
    resolution = frame_list[0].shape[:2]
    output_name = directory + '/' + 'trial{}_cam{}.avi'.format(trial_num,cam)
    writer = cv2.VideoWriter(output_name,
                           cv2.VideoWriter_fourcc(*'XVID'), 
                           frame_rate, 
                           (640,480)) 
    
    for frame in frame_list:
        writer.write(frame)
    writer.release()



@staticmethod
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

@staticmethod
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
