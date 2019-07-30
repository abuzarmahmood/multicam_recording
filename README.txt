 ____  _____    _    ____  __  __ _____ 
|  _ \| ____|  / \  |  _ \|  \/  | ____|
| |_) |  _|   / _ \ | | | | |\/| |  _|  
|  _ <| |___ / ___ \| |_| | |  | | |___ 
|_| \_\_____/_/   \_\____/|_|  |_|_____|
                                        

Code to record from 2 cameras simultaneously and split video into trials

Pipeline:

1) parallel_2_video.sh
|
V
2) ffmpeg_convert.sh
|
V
3) split_script.py

1) Record video using parallel_2_video.sh
	- Supply filename for session, time and date automatically appended to name
2) Convert output video files using ffmpeg
	-This is to get rid of a bug which prevents counting the total number
		of frames in the original video
3) Split video according to a file marking the start and end of the videos
	and another file marking the starting point of every trial
