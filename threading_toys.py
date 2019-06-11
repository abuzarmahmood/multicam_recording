#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 09:50:15 2019

@author: abuzarmahmood
"""

import threading
import time
import numpy as np

def print_stuff_100():
    for i in range(100):
        time.sleep(0.1)
        print(i)
        
def print_stuff_200():
    for i in range(100,200):
        time.sleep(0.1)
        print(i)
        
x = threading.Thread(target = print_stuff_100, name='print_thread',args=())
y = threading.Thread(target = print_stuff_200, name='print_thread',args=())
print("Before starting thread")
x.start()
y.start()
x.join()
y.join()
print('Thread started')

########################



class get_number():
    
    number = -1
    
    def __init__(self):
        self.x = (i for i in range(20))
        
    def read(self):
        self.number = next(self.x)
    
    def print_num(self):
        while True:
            if self.number is not -1:
                time.sleep(0.1)
                print(self.number)
                self.number = -1
            
    def start_print(self):
        t = threading.Thread(target = self.print_num, name='print_thread', args=())
        t.daemon = True
        t.start()
        return self


number_gen = get_number()
number_gen.start_print()

time_list = []

for i in range(10):
    number_gen.read()
    time_list.append(time.time())
    
# =============================================================================
# WORKING VERSION!
# =============================================================================
    

class get_number():
    
    in_list = [] 
    out_list = []
    
    fin_count = 0
    time_list = []
    
    def __init__(self):
        self.x = np.arange(1000)
        
    def read(self):
        for count in range(len(self.x)//10):
            time.sleep(0.1)
            self.in_list.append(self.x[count])
            print('In list = ' + str(self.in_list))
            self.fin_count += 1
            self.time_list.append(time.time())
    
    def print_num(self):
        while True:
            if len(self.in_list) > 0 and len(self.out_list) < self.fin_count:
                self.out_list.append(self.in_list[0])
                self.in_list.pop(0)
                print('Out list = ' + str(self.out_list))
                time.sleep(0.2)
    
    def start_read(self):
        t = threading.Thread(target = self.read, name='read_thread', args=())
        t.daemon = True
        t.start()
        return self
    
    def start_print(self):
        t = threading.Thread(target = self.print_num, name='print_thread', args=())
        t.start()
        t.join()
        return self


number_gen = get_number()
number_gen.start_read()
number_gen.start_print()
print('Done!')



