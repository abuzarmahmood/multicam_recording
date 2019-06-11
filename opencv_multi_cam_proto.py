from imutils.video import VideoStream
import numpy as np
import datetime
import imutils
import time
import cv2
import pylab as plt

# =============================================================================
# webcam0 = VideoStream(src=0,resolution=(640,480)).start()
# webcam1 = VideoStream(src=1,resolution=(640,480)).start()
# webcam2 = VideoStream(src=2,resolution=(640,480)).start()
# =============================================================================

webcam0 = VideoStream(src=0).start()
webcam1 = VideoStream(src=1).start()
webcam2 = VideoStream(src=2).start()

frames = 30*60*10 # Total frames
frame_rate = 30 # per second

vid0 = []
vid1 = []
vid2 = []
time_list = []

start = time.time()
for i in range(frames):
    time.sleep(1/frame_rate)
    vid0.append(webcam0.read())
    vid1.append(webcam1.read())
    vid2.append(webcam2.read())
    time_list.append(time.time())
end = time.time()

run_time = end-start
print(run_time)

vid0 = np.asarray(vid0)
vid1 = np.asarray(vid1)
vid2 = np.asarray(vid2)

fin_vid = np.concatenate((vid0,vid1,vid2),axis=2)

video_name = 'video.avi'

height, width, layers = fin_vid.shape[1:]

video = cv2.VideoWriter(video_name, 0, 30.0, (width,height))

for image in range(fin_vid.shape[0]):
    video.write(fin_vid[image,:,:,:])

cv2.destroyAllWindows()
video.release()