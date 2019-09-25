import cv2
import numpy as np

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
