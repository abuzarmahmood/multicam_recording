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
import threading, queue
import os
import re
import glob
import multiprocessing as mp
import datetime
import tqdm


class webcam_recording:
    
    time_list = []
    moving_window = 100

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
        print('Recording for : {}'\
                .format(datetime.timedelta(seconds = self.duration)))        
        self.check_list = [self.testDevice(i) for i in self.device_ids[:self.cam_num]]
        if sum(self.check_list) == self.cam_num:
            self.all_cams = [VideoStream(src = i,
                                        resolution = self.resolution).start() \
                                                for i in self.device_ids[:self.cam_num]]
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
            for cam in range(self.cam_num):
                self.input_q[cam].put(self.all_cams[cam].read())
                self.in_count[cam] += 1
            self.time_list.append(time.time())
            self.text_q.put(self.time_list[-1])
        
        for thread in self.write_pool:
            thread.join()
        self.text_thread.join()

    def earray_generator(self,id):
        test_img = self.all_cams[0].read()
        hf5_path = self.file_name + "cam{}_frames.h5".format(id)
        hf5 = tables.open_file(hf5_path, mode = 'w')
        filters = tables.Filters(complevel=5, complib='blosc')
        data_storage = hf5.create_earray('/','data',
            tables.Atom.from_dtype(test_img.dtype),
            shape = (0, test_img.shape[0], test_img.shape[1], test_img.shape[2]),
            filters = filters,
            expectedrows = self.total_frames)
        return data_storage
    
    def write_setup(self):
        # Setup write worker threads
        self.input_q = [queue.Queue() for cam in range(self.cam_num)]
        self.write_pool = [write_thread(
                                self.input_q[cam], 
                                self.earray_generator(cam),
                                0.5/self.frame_rate) for cam in range(self.cam_num)]
        for thread in self.write_pool:
            thread.start()
        print('Writing queues initialized')

        self.text_q = queue.Queue()
        self.text_thread = text_thread(self.text_q, self.file_name + '.txt', 
                                        self.frame_rate, self.total_frames)
        self.text_thread.start()
        print('Text queue initialized')


    def print_stats(self):
        print(
                #'Frame lag = {0}, Avg FR = {1}, , Total time = {2}'.format(
                'Avg FR = {0}, , Total time = {1}'.format(
                  #str(np.asarray(self.in_count) - np.asarray(self.out_count)),
                  str(np.mean(np.diff(self.time_list))),
                  str(self.time_list[-1] - self.time_list[0])
                  ))
                     
    def start_read(self):
        t = threading.Thread(
                target = self.read_frames, 
                name='read_thread', 
                args=())
        #t.daemon = True
        t.start()
        print('Reading frames now')
        t.join()
        return self
    
    def start_recording(self):
        self.getDevices()
        self.initialize_cameras()
        self.write_setup()
        self.start_read()
        self.print_stats()

class text_thread(threading.Thread):

    def __init__(self, input_q, text_file_name , frame_rate, total_frames):
        super(text_thread, self).__init__()
        self.stoprequest = threading.Event()
        
        self.input_q = input_q
        self.text_file_name = text_file_name
        self.frame_rate = frame_rate
        self.pbar = tqdm.tqdm(total = total_frames)

    def run(self):
            while not self.stoprequest.isSet():
                try:
                    this_time = self.input_q.get(True, 1/self.frame_rate)
                    with open(self.text_file_name,'a') as f:
                        f.write(str(this_time) + '\n')
                    self.pbar.update(1)
                except:
                    continue

    def join(self, timeout = None):
        self.stoprequest.set()
        super(text_thread, self).join(timeout)

class write_thread(threading.Thread):

    def __init__(self, input_q, earray_handle, frame_rate):
        super(write_thread, self).__init__()
        self.stoprequest = threading.Event()
        
        self.input_q = input_q
        self.earray_handle = earray_handle
        self.frame_rate = frame_rate

    def run(self):
            while not self.stoprequest.isSet():
                try:
                    img = self.input_q.get(True, 1/self.frame_rate)
                    self.earray_handle.append(img[None])
                except:
                    continue

    def join(self, timeout = None):
        self.stoprequest.set()
        super(write_thread, self).join(timeout)

