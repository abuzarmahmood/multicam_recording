import cv2
import numpy as np
from datetime import datetime
import time
 
# Create a VideoCapture object
cam0 = cv2.VideoCapture(0)
cam1 = cv2.VideoCapture(1)
cam2 = cv2.VideoCapture(2)
 
# Check if camera opened successfully
if (cam0.isOpened() == False): 
  print("Unable to read cam0 feed")
if (cam1.isOpened() == False): 
  print("Unable to read cam1 feed")
if (cam2.isOpened() == False): 
  print("Unable to read cam2 feed")
 
# Default resolutions of the frame are obtained.The default resolutions are system dependent.
# We convert the resolutions from float to integer.

cam0_w,cam0_h = int(cam0.get(3)),int(cam0.get(4))
cam1_w,cam1_h = int(cam1.get(3)),int(cam1.get(4))
cam2_w,cam2_h = int(cam2.get(3)),int(cam2.get(4))
 
# Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
out0 = cv2.VideoWriter('outpy0.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 30, (cam0_w,cam0_h))
out1 = cv2.VideoWriter('outpy1.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 30, (cam1_w,cam1_h))
out2 = cv2.VideoWriter('outpy2.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 30, (cam2_w,cam2_h))

print('Video now recording')

recording_time = 60 # in seconds
frame_rate = 1/30

start = time.time()
for i in range(int(recording_time/frame_rate)):
  ret0, frame0 = cam0.read()
  ret1, frame1 = cam1.read()
  ret2, frame2 = cam2.read()
 
  if ret0 and ret1 and ret2: 
     
    # Write the frame into the file 'output.avi'
    out0.write(frame0)
    out1.write(frame1)
    out2.write(frame2)
end = time.time()

print('Expected time = ' + str(recording_time) + ', Actual time = ' + str(end-start))

# When everything done, release the video capture and video write objects
cam0.release()
out0.release()

cam1.release()
out1.release()

cam2.release()
out2.release()
 
# Closes all the frames
cv2.destroyAllWindows()