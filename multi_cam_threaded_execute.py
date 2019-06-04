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

this_recording = webcam_recording(60*10,30,3)

# =============================================================================
# this_recording.initialize_cameras()
# this_recording.initialize_writers()
# this_recording.initialize_stats()
# this_recording.start_read()
# this_recording.start_write()
# =============================================================================

print('Start time = ' + str(datetime.datetime.now()))
this_recording.start_recording()
print('End time = ' + str(datetime.datetime.now()))

this_recording.recording_stats()
plt.plot(np.diff(this_recording.time_list))
