from imutils.video import VideoStream
import numpy as np
import datetime
import imutils
import time
import cv2
import pylab as plt

resolution = (640,480)
webcam0 = VideoStream(src=0,resolution=resolution).start()
webcam1 = VideoStream(src=1,resolution=resolution).start()
webcam2 = VideoStream(src=2,resolution=resolution).start()

# =============================================================================
# webcam0 = VideoStream(src=0).start()
# webcam1 = VideoStream(src=1).start()
# webcam2 = VideoStream(src=2).start()
# =============================================================================

# Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
out0 = cv2.VideoWriter('outpy0.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 30, resolution)
out1 = cv2.VideoWriter('outpy1.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 30, resolution)
out2 = cv2.VideoWriter('outpy2.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 30, resolution)


print('Video now recording')

recording_time = 60 # in seconds
frame_rate = 1/30


time_list = []
start = time.time()
for i in range(int(recording_time/frame_rate)):
    time.sleep(frame_rate)
    # Write the frame into the file 'output.avi'
    out0.write(webcam0.read())
    out1.write(webcam1.read())
    out2.write(webcam2.read())
    time_list.append(time.time())
end = time.time()

print('Expected time = ' + str(recording_time) + ', Actual time = ' + str(end-start))
 
# When everything done, release the video capture and video write objects
out0.release()
out1.release()
out2.release()
 
# Closes all the frames
cv2.destroyAllWindows()