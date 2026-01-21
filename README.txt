 ____  _____    _    ____  __  __ _____ 
|  _ \| ____|  / \  |  _ \|  \/  | ____|
| |_) |  _|   / _ \ | | | | |\/| |  _|  
|  _ <| |___ / ___ \| |_| | |  | | |___ 
|_| \_\_____/_/   \_\____/|_|  |_|_____|
                                        

Code to record from 2 cameras simultaneously and split video into trials

## Dependencies

### System Dependencies

This project requires the following system packages to be installed:

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install ffmpeg streamer parallel zenity figlet
```

#### CentOS/RHEL/Fedora:
```bash
sudo yum install ffmpeg streamer parallel zenity figlet
# or for newer systems with dnf:
sudo dnf install ffmpeg streamer parallel zenity figlet
```

#### macOS (using Homebrew):
```bash
brew install ffmpeg parallel
# Note: streamer and zenity may not be available on macOS
# Alternative solutions may be needed for camera recording and GUI
```

### Python Dependencies

Install the required Python packages using pip:

```bash
pip install opencv-python numpy matplotlib tqdm moviepy
```

Or create a requirements.txt file with the following content:
```
opencv-python
numpy
matplotlib
tqdm
moviepy
```

Then install with:
```bash
pip install -r requirements.txt
```

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd multicam_recording
```

2. Install system dependencies (see above)

3. Install Python dependencies:
```bash
pip install opencv-python numpy matplotlib tqdm moviepy
```

4. Make the shell scripts executable:
```bash
chmod +x parallel_2_video.sh
chmod +x convert_files_gui.sh
```

## Usage Pipeline

1) parallel_2_video.sh
|
V
2) convert_files_gui.sh
|
V
3) split_script.py

### Step 1: Record video using parallel_2_video.sh
- Supply filename for session, time and date automatically appended to name
- Requires 2 cameras connected to /dev/video0 and /dev/video1
- Press Ctrl+C to stop recording

**Note:** Input device numbers are hardcoded and may not be correct, use `v4l2-ctl --list-devices` to adjust

### Step 2: Convert output video files using convert_files_gui.sh
- This step uses ffmpeg to get rid of a bug which prevents counting the total number of frames in the original video
- Compresses file to a smaller bitrate to save on space
- Provides a GUI interface to select files for conversion (requires zenity)

### Step 3: Split video using split_script.py
- Split video according to a file marking the start and end of the videos
- Another file marks the starting point of every trial
- Run with: `python split_script.py -h` for usage instructions

## Hardware Requirements

- 2 USB cameras (or other video devices)
- Sufficient disk space for video recordings
- Linux system recommended (some dependencies may not work on other OS)

## Notes

- The scripts are designed for Linux systems
- streamer is used for camera recording and may not be available on all systems
- zenity provides the GUI for file selection in the conversion step
- ffmpeg is used extensively for video processing and conversion

## Resources

- https://tldp.org/HOWTO/Webcam-HOWTO/framegrabbers.html
- https://linux.die.net/man/1/streamer
