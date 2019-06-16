import cv2
import matplotlib.pyplot as plt

def grab_frame(cap):
    ret,frame = cap.read()
    return cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

# Set framerate
framerate = 30

#Initiate the two cameras
cap1 = cv2.VideoCapture(0)
cap1.set(3,1280)
cap1.set(4,720)
cap2 = cv2.VideoCapture(1)
cap2.set(3,1280)
cap2.set(4,720)

#create two subplots
ax1 = plt.subplot(1,2,1)
ax2 = plt.subplot(1,2,2)

#create two image plots
im1 = ax1.imshow(grab_frame(cap1), origin='lower')
im2 = ax2.imshow(grab_frame(cap2), origin='lower')

plt.ion()

while True:
    im1.set_data(grab_frame(cap1))
    im2.set_data(grab_frame(cap2))
    plt.pause(0.1/framerate)

plt.ioff() # due to infinite loop, this gets never called.
plt.show()
