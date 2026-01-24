
Code to record from 2+ cameras simultaneously and split video into trials

## Dependencies

### System Dependencies

This project requires the following system packages to be installed:

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install ffmpeg streamer parallel zenity figlet
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
chmod +x parallel2video_ffmpeg.sh
chmod +x parallel2video_streamer.sh
chmod +x convert_files_gui.sh
chmod +x combine_utils/combine_videos_gui.sh
```

## Usage Pipeline

1) parallel2video_ffmpeg.sh (or parallel2video_streamer.sh for legacy systems)
|
V
2) convert_files_gui.sh
|
V
3) split_script.py

### Step 1: Record video using parallel2video_ffmpeg.sh (Recommended)
- Supply filename for session, time and date automatically appended to name
- Requires 2+ cameras connected to /dev/video<123>
- Press Ctrl+C to stop recording
- Outputs MP4 files with H.264 encoding for better compatibility and quality
- Uses ffmpeg for modern video processing

### Alternative: parallel2video_streamer.sh (Legacy)
- Uses the older streamer utility for backward compatibility
- Outputs AVI files that may require conversion (handled in Step 2)
- Use this if ffmpeg is not available or if you need to maintain compatibility with existing workflows

**Note:** Input device numbers are hardcoded and may not be correct, use `v4l2-ctl --list-devices` to adjust

### Step 2: Convert output video files using convert_files_gui.sh
- When using parallel2video_streamer.sh: This step uses ffmpeg to get rid of a bug which prevents counting the total number of frames in the original AVI files
- When using parallel2video_ffmpeg.sh: This step may be optional as the files are already in MP4 format, but can be used for further compression
- Compresses file to a smaller bitrate to save on space
- Provides a GUI interface to select files for conversion (requires zenity)

### Step 3: Split video using split_script.py
- Split video according to a file marking the start and end of the videos
- Another file marks the starting point of every trial
- Run with: `python split_script.py -h` for usage instructions

### Step 4: Combine videos using combine_utils/ (NEW)
- Combine multiple videos into a single frame showing all videos simultaneously
- Use `combine_utils/combine_videos_gui.sh` for GUI interface or `combine_utils/combine_videos.py` for command line
- Supports various grid layouts (auto, 2x1, 1x2, 2x2, 3x1, 1x3)
- Adjustable quality settings and video scaling
- Uses ffmpeg for efficient video processing

**Command Line Usage:**
```bash
python3 combine_utils/combine_videos.py video1.avi video2.avi -o combined.mp4 --grid 2x1 --quality high
```

**GUI Usage:**
```bash
./combine_utils/combine_videos_gui.sh
```

## Hardware Requirements

- 2 USB cameras (or other video devices)
- Sufficient disk space for video recordings
- Linux system recommended (some dependencies may not work on other OS)

## Notes

- The scripts are designed for Linux systems
- parallel2video_ffmpeg.sh uses ffmpeg for modern video processing (recommended)
- parallel2video_streamer.sh uses the legacy streamer utility for backward compatibility
- zenity provides the GUI for file selection in the conversion step
- ffmpeg is used extensively for video processing and conversion

## Resources

### Recording optimization

- [FFmpeg Multi-Camera DeepLabCut Optimization](docs/FFmpeg_Multi-Camera_DeepLabCut_Optimization.md) - Comprehensive guide for multi-camera recording optimization, including USB bandwidth management, encoding parameters, and streaming protocols
- https://breq.dev/2023/06/21/cameras - Original blog post with detailed technical information about camera streaming pipelines

### Other Resources

- https://tldp.org/HOWTO/Webcam-HOWTO/framegrabbers.html
- https://linux.die.net/man/1/streamer
