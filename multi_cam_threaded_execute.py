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

#this_recording = webcam_recording(10,30,2, resolution = (1280,720))
this_recording = webcam_recording(10,30,2)

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
