#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 11:47:53 2019

@author: abuzarmahmood
"""

from imutils.video import VideoStream
import numpy as np
import tables
import time
import cv2
import threading
import os
import re
import glob
import warnings
import multiprocessing as mp

class webcam_recording:
    
    time_list = []
    moving_window = 100
    read_bool = 1
    write_bool = 1    
    time_bool = 0
    buffer_bool = 0

    def __init__(self,
                duration,
                frame_rate, 
                cam_num, 
                file_name = 'outpy',
                resolution = (640,480)):

        self.duration = duration # in seconds
        self.frame_rate = frame_rate # in # per second
        self.total_frames = duration*frame_rate
        self.file_name = file_name
        self.cam_num = cam_num
        self.resolution = resolution
        self.in_count = [0 for i in range(self.cam_num)]
        self.out_count = [0 for i in range(self.cam_num)]

        warnings.filterwarnings('ignore', category=tables.NaturalNameWarning)

             
    @staticmethod
    def testDevice(source):
        cap = cv2.VideoCapture(source) 
        if cap is None or not cap.isOpened():
            return 0
        else:
            return 1
    
    def getDevices(self):
        dir_list = os.listdir('/dev/')
        device_list = [x for x in dir_list if re.match('video[0-9]',x)]
        temp_device_ids = [int(re.findall(r'\d+',x)[0]) for x in device_list]
        temp_device_ids.sort()
        self.device_ids = temp_device_ids

    def initialize_cameras(self):
        
        self.check_list = [self.testDevice(i) for i in self.device_ids[:self.cam_num]]
        if sum(self.check_list) == self.cam_num:
            self.all_cams = [VideoStream(src = i,
                                        resolution = self.resolution).start() \
                                                for i in self.device_ids[:self.cam_num]]
            self.all_buffers = [[] for i in range(self.cam_num)]
            print('Cameras initialized')

        else:
            print("Only available devices are:")
            print(list(zip(range(self.cam_num),self.check_list)))
            print('Change cam_num')
        

    def shut_down(self):
        for cam in self.all_cams:
            cam.stop()
        
    def read_frames(self):
        for count in range(self.total_frames):
            if min(self.in_count) > self.moving_window:
                next_rate = 1/((1/self.frame_rate)*self.moving_window -  \
                            np.sum(np.diff(self.time_list[-self.moving_window:])))
            else:
                next_rate = self.frame_rate
            time.sleep(1/next_rate)
            #time.sleep(np.max([0,1/next_rate]))
            self.buffer_bool = 0
            for cam in range(self.cam_num):
                self.all_buffers[cam].append(self.all_cams[cam].read())
                self.in_count[cam] += 1
            self.buffer_bool = 1
            self.time_list.append(time.time())
            self.time_bool = 1        
        self.read_bool = 0

    
    # Pre-define all names for files
    def generate_name_list(self):
        self.name_list = [[os.path.dirname(self.file_name) + "/temp/{0}_cam{2}_{1:06d}".\
                format(os.path.basename(self.file_name),frame,cam) \
                for frame in range(self.total_frames)] for cam in range(self.cam_num)] 

    # To write out to binary files
    def write_binary(self):
        self.generate_name_list()
        os.mkdir(os.path.dirname(self.file_name) + '/temp')
        while self.write_bool > 0 or self.read_bool > 0:
            time.sleep(0.5/self.frame_rate)
            for cam in range(self.cam_num):
                if len(self.all_buffers[cam]) > 0 :#and self.buffer_bool == 1:
                    np.save(self.name_list[cam][self.out_count[cam]],
                            self.all_buffers[cam][0])
                    self.all_buffers[cam].pop(0)
                    self.out_count[cam] += 1
             
            self.write_bool = \
                sum([out_count < in_count for (out_count, in_count) in \
                     zip(self.out_count, self.in_count)])
            
            if self.time_bool == 1:
                with open("{0}_time_list.txt".format(self.file_name),"a") \
                        as out_file:
                    out_file.write(str(self.time_list[-1]) + '\n')        
                self.time_bool = 0


    def print_stats(self):
        print(
                'Frame lag = {0}, Avg FR = {1}, , Total time = {2}'.format(
                  str(np.asarray(self.in_count) - np.asarray(self.out_count)),
                  str(np.mean(np.diff(self.time_list[-self.moving_window:]))),
                  str(self.time_list[-1] - self.time_list[0])
                  ))
                     
    def start_read(self):
        t = threading.Thread(
                target = self.read_frames, 
                name='read_thread', 
                args=())
        t.daemon = True
        t.start()
        print('Reading frames now')
        return self
    
    def start_write(self):
        t = threading.Thread(
                target = self.write_binary, 
                name='print_thread', 
                args=())
        t.start()
        print('Writing frames now')
        t.join()
        return self
    
    def start_recording(self):
        self.getDevices()
        self.initialize_cameras()
        self.start_read()

        start_write_bool = 0
        while not start_write_bool: 
            if sum(self.in_count) > 0:
                self.start_write()
                start_write_bool = 1
        
        self.print_stats()
