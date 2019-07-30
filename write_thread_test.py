import threading, queue
import os
import time
import numpy as np

class write_thread(threading.Thread):

    def __init__(self, input_q, directory, file_name, frame_rate):
        super(write_thread, self).__init__()
        self.stoprequest = threading.Event()
        
        self.input_q = input_q
        self.file_name = file_name
        self.directory = directory
        self.frame_rate = frame_rate

    def run(self):
        self.out_count = 0  
        with open(self.directory + '/' + self.file_name + '_{}'.format(self.out_count),'ba')\
                as f:
            while not self.stoprequest.isSet():
                try:
                    img = self.input_q.get(True, 1/self.frame_rate)
                    np.save(f,
                            img
                            )
                    self.out_count += 1
                except:
                    continue

    #def _write_image(self,img):

    def join(self, timeout = None):
        self.stoprequest.set()
        super(write_thread, self).join(timeout)

class write_thread(threading.Thread):

    def __init__(self, input_q, earray_handle, frame_rate):
        super(write_thread, self).__init__()
        self.stoprequest = threading.Event()
        
        self.input_q = input_q
        self.earray = earray_handle
        self.frame_rate = frame_rate

    def run(self):
        self.out_count = 0  
        with open(self.directory + '/' + self.file_name + '_{}'.format(self.out_count),'ba')\
                as f:
            while not self.stoprequest.isSet():
                try:
                    img = self.input_q.get(True, 1/self.frame_rate)
                    np.save(f,
                            img
                            )
                    self.out_count += 1
                except:
                    continue

    def join(self, timeout = None):
        self.stoprequest.set()
        super(write_thread, self).join(timeout)

directory = os.path.abspath('write_test')
if not os.path.exists(directory):
    os.makedirs(directory)

#array_size = (1000,1000,1000)
array_size = (100,100,1000)
array = np.random.random(array_size)
print('Done creating array')

# Individual files
start_t1 = time.time()
for img in range(array_size[2]):
    np.save(directory + '/file{}'.format(img), array[:,:,img])
stop_t1 = time.time()
print('Individual file save : {}'.format(stop_t1 - start_t1))

# Single file threaded
input_q = queue.Queue()
thread = write_thread(input_q, directory, 'test', 30)
thread.start()
for img in range(array_size[2]):
    input_q.put(array[:,:,img])

print('Single file save : {}'.format(stop_t2 - start_t2))
thread.join()

print('Ratio : {}'.format( (stop_t1 - start_t1)/(stop_t2-start_t2) ))
