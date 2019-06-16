#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 12:49:03 2019

@author: abuzarmahmood
"""
from multi_cam_threaded import webcam_recording
import pylab as plt
import numpy as np
import datetime
import sys
import os

folder_name = os.getcwd()
file_name = sys.argv[1]+ '_' + \
            datetime.datetime.today().\
            strftime('%y%m%d-%H%M%S')

fin_direc = (folder_name + '/' + file_name)
if not os.path.exists(fin_direc):
    os.mkdir(fin_direc)
#this_recording = webcam_recording(10,30,2, resolution = (1280,720))
this_recording = webcam_recording(
                                duration = 2,
                                frame_rate = 30,
                                cam_num = 3,
                                file_name = fin_direc + '/' + file_name) 
# =============================================================================
#this_recording.getDevices()
#this_recording.initialize_cameras()
#this_recording.initialize_writers()
#this_recording.start_read()
#this_recording.start_write()
# =============================================================================

print('Start time = ' + str(datetime.datetime.now()))
this_recording.start_recording()
print('End time = ' + str(datetime.datetime.now()))
