import numpy as np
import os
import time
directory = 'write_test'

if not os.path.exists(directory):
    os.makedirs(directory)

array_size = (100,100,3)
iterations = 1000

# Individual files - save

start_t = time.time()
for i in range(iterations):
    np.save(directory + '/file{}'.format(i),np.random.random(array_size))
stop_t = time.time()

print('Individual save : {}'.format(stop_t - start_t))

# Individual files -- tofile

start_t = time.time()
for i in range(iterations):
    np.random.random(array_size).tofile(directory + '/file{}'.format(i))
    #np.tofile(directory + '/file{}'.format(i),np.random.rand(100,100))
stop_t = time.time()

print('Individual tofile: {}'.format(stop_t - start_t))


# Single file

start_t = time.time()
with open(directory + '/asd.dat','ab') as file:
    for i in range(iterations):
        np.random.random(array_size).tofile(file)
        #np.save( file, np.random.rand(100,100))
stop_t = time.time()

print('Single: {}'.format(stop_t - start_t))
