
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
- Automatically checks disk space before starting recording
- Supply filename for session, time and date automatically appended to name
- Requires 2+ cameras connected to /dev/video<123>
- Press Ctrl+C to stop recording
- Outputs MP4 files with H.264 encoding for better compatibility and quality
- Uses ffmpeg for modern video processing

### Alternative: parallel2video_streamer.sh (Legacy)
- Automatically checks disk space before starting recording
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

## Configuration

The project uses a `config.json` file to configure various settings, including disk space requirements:

### Disk Space Configuration

The recording scripts automatically check for sufficient disk space before starting. The configuration includes:

```json
{
  "disk_space": {
    "min_free_space_gb": 10,
    "warning_threshold_gb": 5,
    "estimated_space_per_minute_gb": 0.5,
    "max_recording_minutes": 180
  }
}
```

- `min_free_space_gb`: Minimum free space required before recording (default: 10 GB)
- `warning_threshold_gb`: Show warning if remaining space after recording falls below this (default: 5 GB)
- `estimated_space_per_minute_gb`: Estimated disk space needed per minute of recording (default: 0.5 GB)
- `max_recording_minutes`: Maximum allowed recording duration in minutes (default: 180)

### Recording Configuration

```json
{
  "recording": {
    "default_duration_minutes": 180,
    "video_resolution": "1280x720",
    "frame_rate": 30,
    "num_cameras": 2
  }
}
```

### Manual Disk Space Check

You can manually check disk space using the provided utility:

```bash
python3 disk_space_check.py [--config config.json] [--path .] [--duration 60]
```

- `--config`: Path to configuration file (default: config.json)
- `--path`: Directory to check for disk space (default: current directory)
- `--duration`: Expected recording duration in minutes (optional)

## Notes

- The scripts are designed for Linux systems
- parallel2video_ffmpeg.sh uses ffmpeg for modern video processing (recommended)
- parallel2video_streamer.sh uses the legacy streamer utility for backward compatibility
- zenity provides the GUI for file selection in the conversion step
- ffmpeg is used extensively for video processing and conversion

## Resources

### Recording optimization

- [Multi camera optimization blog post summary](docs/FFmpeg_Multi-Camera_DeepLabCut_Optimization.md) - Comprehensive guide for multi-camera recording optimization, including USB bandwidth management, encoding parameters, and streaming protocols
- https://breq.dev/2023/06/21/cameras - Original blog post with detailed technical information about camera streaming pipelines

### Other Resources
- [FFmpeg Multi-Camera DeepLabCut Optimization](docs/FFmpeg_Multi-Camera_DeepLabCut_Optimization.rtf) - Comprehensive guide on optimizing multi-camera recordings for DeepLabCut, including USB bandwidth management, camera recommendations, and video encoding parameters

### General resources

- https://tldp.org/HOWTO/Webcam-HOWTO/framegrabbers.html
- https://linux.die.net/man/1/streamer
