
Code to record from 2+ cameras simultaneously and split video into trials

## Quickstart

### Running Your First Recording

1. **Connect your cameras** - Plug in 2 or more USB cameras to your computer

2. **Check camera devices** - Find your camera device paths:
```bash
v4l2-ctl --list-devices
```
This will show output like:
```
USB Camera (usb-0000:00:14.0-1):
    /dev/video0
    /dev/video1

USB Camera (usb-0000:00:14.0-2):
    /dev/video2
    /dev/video3
```
Note the `/dev/videoX` paths for your cameras.

3. **Configure your cameras** - Edit `config.json` to set your camera device paths:
```json
{
  "video_devices": [
    "/dev/video0",
    "/dev/video2"
  ]
}
```

4. **Run the recording script**:
```bash
./parallel2video_ffmpeg.sh
```

5. **Provide inputs when prompted**:
   - **Filename**: Enter a descriptive name for your recording session (e.g., `mouse_trial_01`)
   - **Duration**: Enter recording time in minutes (e.g., `5` for 5 minutes)
   - The script will automatically append date and time to your filename

6. **Stop recording**:
   - Press `Ctrl+C` to stop recording early, or
   - Wait for the timer to complete

7. **Automatic transcoding**:
   - After recording stops, the script automatically transcodes videos
   - This compresses files using H.264 and scales to 960px width
   - You can press `Ctrl+C` during transcoding to skip it

### What You'll Get

After recording completes, you'll have these files in your output directory:

**Original recordings** (in main directory):
- `mouse_trial_01_2026-02-21_14-30-00_cam1.mp4` - Raw video from camera 1
- `mouse_trial_01_2026-02-21_14-30-00_cam2.mp4` - Raw video from camera 2
- `mouse_trial_01_2026-02-21_14-30-00_markers.txt` - Timestamp markers for start/stop times

**Transcoded videos** (in `coded/` subdirectory):
- `coded/mouse_trial_01_2026-02-21_14-30-00_cam1_coded.mp4` - Compressed video from camera 1
- `coded/mouse_trial_01_2026-02-21_14-30-00_cam2_coded.mp4` - Compressed video from camera 2

**File sizes** (approximate for 5 minutes at 720p60):
- Original files: ~2-3 GB each (MJPEG format)
- Transcoded files: ~200-400 MB each (H.264 compressed, 960px width)

### Example Session

```bash
$ ./parallel2video_ffmpeg.sh

Enter filename for recording: mouse_behavior_test
Enter recording duration in minutes: 3

Checking disk space...
✓ Sufficient disk space available (50.2 GB free)

Recording will be saved to: output/mouse_behavior_test_2026-02-21_14-30-00/

Recording with copy mode (-c:v copy) - no transcoding, faster capture...
Recording started at: 2026-02-21 14:30:00

[Press Ctrl+C to stop recording early]

Recording stopped at: 2026-02-21 14:33:00
Recording complete!

Starting transcoding of recorded videos...
This will compress the videos using H.264 with CRF 23 and scale to 960px width.

Found 2 video file(s) to transcode
Transcoding: mouse_behavior_test_2026-02-21_14-30-00_cam1.mp4
  Original size: 2.8 GB
  Transcoded size: 320 MB (88.6% reduction)
Transcoding: mouse_behavior_test_2026-02-21_14-30-00_cam2.mp4
  Original size: 2.9 GB
  Transcoded size: 335 MB (88.4% reduction)

All done!
```

### Troubleshooting

**"Insufficient disk space" error:**
- Free up disk space or adjust `min_free_space_gb` in `config.json`

**"Device or resource busy" error:**
- Another program is using the camera
- Close other applications (Zoom, Skype, Cheese, etc.)

**Dropped frames or "select timeout" errors:**
- USB bandwidth issue - try lowering frame rate in the script (change `-r 60` to `-r 30`)
- Or distribute cameras across different USB controllers

**Camera not found:**
- Run `v4l2-ctl --list-devices` to verify device paths
- Update `config.json` with correct paths

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
chmod +x postprocessing/transcode_copy_videos.sh
chmod +x postprocessing/transcode_copy_videos_gui.sh
chmod +x postprocessing/transcode_simple.sh
chmod +x postprocessing/combine_utils/combine_videos_gui.sh
```

## Usage Pipeline

1) parallel2video_ffmpeg.sh (or parallel2video_streamer.sh for legacy systems)
|
V
2) convert_files_gui.sh (or postprocessing/transcode_copy_videos_gui.sh for -c:v copy videos)
|
V
3) split_script.py

### Step 1: Record video using parallel2video_ffmpeg.sh (Recommended)
- Automatically checks disk space before starting recording
- Supply filename for session, time and date automatically appended to name
- Requires 2+ cameras connected to /dev/video<123>
- Press Ctrl+C to stop recording
- Uses `-c:v copy` mode for faster recording (no transcoding during capture)
- Automatically transcodes recorded videos after recording completes
- Transcoding compresses videos using H.264 with CRF 23 and scales to 960px width
- Outputs MP4 files with MJPEG input format for reduced USB bandwidth
- Uses ffmpeg for modern video processing

### Alternative: parallel2video_streamer.sh (Legacy)
- Automatically checks disk space before starting recording
- Uses the older streamer utility for backward compatibility
- Outputs AVI files that may require conversion (handled in Step 2)
- Use this if ffmpeg is not available or if you need to maintain compatibility with existing workflows

**Note:** Input device numbers are hardcoded and may not be correct, use `v4l2-ctl --list-devices` to adjust

### Step 2: Convert output video files using convert_files_gui.sh (Optional)
- When using parallel2video_streamer.sh: This step uses ffmpeg to get rid of a bug which prevents counting the total number of frames in the original AVI files
- When using parallel2video_ffmpeg.sh: This step is now **optional** as automatic transcoding happens after recording
- The automatic transcoding after recording compresses files using H.264 CRF 23 and scales to 960px width
- If you skipped automatic transcoding (Ctrl+C during transcoding), you can use this GUI tool or the transcode scripts below
- Provides a GUI interface to select files for conversion (requires zenity)

### Alternative Step 2: Transcode videos using postprocessing/transcode_copy_videos_gui.sh
- Specifically designed to handle videos recorded with `-c:v copy` flag
- **Note**: parallel2video_ffmpeg.sh now automatically transcodes after recording, so this is only needed if you skipped that step
- Automatically detects videos that were recorded without compression
- Provides multiple quality presets (low, medium, high, ultra) for compression
- Shows before/after file size comparison and compression ratio
- Supports batch processing with parallel execution for faster processing
- Preserves original timestamps and metadata
- Provides both GUI and command-line interfaces
- Uses efficient H.264 encoding to significantly reduce file size while maintaining quality

**Command Line Usage:**
```bash
# Basic usage
./postprocessing/transcode_copy_videos.sh video1.mp4 video2.mp4

# With quality preset
./postprocessing/transcode_copy_videos.sh --quality high *.mp4

# Custom settings
./postprocessing/transcode_copy_videos.sh --crf 20 --preset slow video.mp4

# GUI mode
./postprocessing/transcode_copy_videos_gui.sh
```

**Quality Presets:**
- `low` - CRF 28, fast preset (smaller files, faster processing)
- `medium` - CRF 23, medium preset (balanced quality/size)
- `high` - CRF 18, slow preset (better quality, smaller files)
- `ultra` - CRF 15, veryslow preset (best quality, smallest files)

### Simple Transcoding: postprocessing/transcode_simple.sh
- Simple script for basic video compression and scaling
- **Note**: parallel2video_ffmpeg.sh now uses similar automatic transcoding after recording
- Finds all MP4 files in a directory (excluding files already containing "coded" in filename)
- Compresses videos using H.264 with CRF 23 and scales to 960px width
- Saves transcoded files to a "coded" subdirectory with "_coded" suffix
- Shows file size comparison before and after compression
- Ideal for quick batch processing of recorded videos or re-transcoding with different settings

**Usage:**
```bash
# Process current directory
./postprocessing/transcode_simple.sh

# Process specific directory
./postprocessing/transcode_simple.sh /path/to/videos

# Show help
./postprocessing/transcode_simple.sh --help
```

### Step 3: Split video using split_script.py
- Split video according to a file marking the start and end of the videos
- Another file marks the starting point of every trial
- Run with: `python split_script.py -h` for usage instructions

### Step 4: Combine videos using postprocessing/combine_utils/ (NEW)
- Combine multiple videos into a single frame showing all videos simultaneously
- Use `postprocessing/combine_utils/combine_videos_gui.sh` for GUI interface or `postprocessing/combine_utils/combine_videos.py` for command line
- Supports various grid layouts (auto, 2x1, 1x2, 2x2, 3x1, 1x3)
- Adjustable quality settings and video scaling
- Uses ffmpeg for efficient video processing

**Command Line Usage:**
```bash
python3 postprocessing/combine_utils/combine_videos.py video1.avi video2.avi -o combined.mp4 --grid 2x1 --quality high
```

**GUI Usage:**
```bash
./postprocessing/combine_utils/combine_videos_gui.sh
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

## FFmpeg Flags Reference

This section documents all ffmpeg flags used in the project, explains why current settings were selected, and describes alternative options.

### Understanding Flag Categories

FFmpeg flags fall into three categories based on where they have their primary effect:

| Category | Where Applied | What It Affects |
|----------|---------------|-----------------|
| **Camera/Hardware** | On the camera itself | USB bandwidth, camera sensor settings |
| **Software/CPU** | During encoding on your computer | CPU load, encoding speed |
| **Output/File** | In the output file | File size, playback compatibility |

Understanding these categories helps you optimize for your specific constraints (USB bandwidth limited? CPU limited? Storage limited?).

### Flag Impact Summary

The following table shows all flags used in the recording script and their primary impact:

| Flag | Category | USB Bandwidth | CPU Load | File Size |
|------|----------|---------------|----------|-----------|
| `-f v4l2` | Camera | - | - | - |
| `-i /dev/videoX` | Camera | - | - | - |
| `-s 1280x720` | Camera | ⬆️ Higher = more | - | ⬆️ Higher = larger |
| `-r 30` | Camera | ⬆️ Higher = more | - | ⬆️ Higher = larger |
| `-c:v libx264` | Software | - | ⬆️ Software encoding | ⬇️ Good compression |
| `-preset ultrafast` | Software | - | ⬇️ Lower CPU | ⬆️ Larger files |
| `-crf 23` | Output | - | - | ⬆️ Lower = larger |
| `-pix_fmt yuv420p` | Output | - | - | - (compatibility) |
| `-vf extractplanes=y` | Software | - | ⬇️ Less data to encode | ⬇️ ~50% smaller |

**Legend:** ⬆️ = increases, ⬇️ = decreases, - = no significant effect

### Recording Script (parallel2video_ffmpeg.sh)

The main recording command uses copy mode for fast capture, then transcodes after recording:

**During Recording (copy mode - no transcoding):**
```bash
ffmpeg -use_wallclock_as_timestamps 1 -copyts -f v4l2 -input_format mjpeg -i /dev/video0 -r 60 -c:v copy output.mp4
```

**After Recording (automatic transcoding):**
```bash
ffmpeg -i output.mp4 -c:v libx264 -crf 23 -vf scale=960:-1 output_coded.mp4
```

#### Camera/Hardware Flags (Affect USB Bandwidth)

These flags configure what the camera captures and sends over USB. They directly affect USB bandwidth consumption.

| Flag | Value | Description | USB Bandwidth Impact | Alternatives |
|------|-------|-------------|---------------------|--------------|
| `-f v4l2` | v4l2 | Video4Linux2 input format | None (just specifies driver) | `-f dshow` (Windows), `-f avfoundation` (macOS) |
| `-input_format mjpeg` | mjpeg | **Request MJPEG from camera** | **LOW** - Camera compresses before sending (5-10x reduction) | `yuyv422` (default, uncompressed, high bandwidth) |
| `-i` | /dev/videoX | Input device path | None | Use `v4l2-ctl --list-devices` to find devices |
| `-r` | 60 | **Frame rate requested from camera** | **MEDIUM** - With MJPEG compression | `30` (halves bandwidth), `15` (quarters bandwidth) |

**USB Bandwidth Calculation:**
```
Bandwidth = Width × Height × Bytes_per_pixel × FPS
Example: 1280 × 720 × 2 (YUYV) × 30 = 55.3 MB/s per camera
```

USB 2.0 practical limit is ~53 MB/s total, so 720p30 in raw format can only support 1 camera per USB controller. Use MJPEG input mode (`-input_format mjpeg`) to reduce this significantly.

#### Software/CPU Flags (Affect CPU Load)

These flags control how ffmpeg processes and encodes the video on your CPU. They don't affect what the camera sends.

**During Recording (copy mode):**
| Flag | Value | Description | CPU Impact | Alternatives |
|------|-------|-------------|------------|--------------|
| `-c:v copy` | copy | **Copy video stream without re-encoding** | **MINIMAL** - No encoding during capture | `libx264` (encode during capture, higher CPU) |
| `-use_wallclock_as_timestamps 1` | 1 | Use system clock for timestamps | Minimal | Default timestamps |
| `-copyts` | - | Preserve timestamps | Minimal | - |

**After Recording (automatic transcoding):**
| Flag | Value | Description | CPU Impact | Alternatives |
|------|-------|-------------|------------|--------------|
| `-c:v libx264` | libx264 | **Software H.264 encoder** | **MEDIUM** - Encoding after recording | `h264_nvenc` (NVIDIA GPU, very low CPU), `h264_vaapi` (Intel GPU) |
| `-crf 23` | 23 | Constant Rate Factor (quality) | Standard | `18` (higher quality, more CPU), `28` (lower quality, less CPU) |
| `-vf scale=960:-1` | 960:-1 | Scale to 960px width, maintain aspect ratio | Low | `scale=1280:-1` (larger), `scale=640:-1` (smaller) |

**CPU Load by Preset (approximate for 720p30):**
| Preset | CPU Usage | File Size |
|--------|-----------|-----------|
| ultrafast | ~15% | 1.0x (baseline) |
| superfast | ~20% | 0.9x |
| veryfast | ~30% | 0.8x |
| faster | ~40% | 0.7x |
| medium | ~60% | 0.6x |
| slow | ~80% | 0.55x |
| veryslow | ~100% | 0.5x |

#### Output/File Flags (Affect File Size and Compatibility)

**During Recording (copy mode):**
- Output format is determined by camera's MJPEG stream
- File size is larger (uncompressed or lightly compressed)
- No quality loss during capture

**After Recording (automatic transcoding):**
| Flag | Value | Description | File Size Impact | Alternatives |
|------|-------|-------------|------------------|--------------|
| `-crf` | 23 | **Constant Rate Factor (quality)** | **DIRECT** - Lower = larger, higher quality | `18` (visually lossless, ~2x size), `28` (smaller, lower quality) |
| `-vf scale=960:-1` | 960:-1 | Scale to 960px width | **SIGNIFICANT** - Reduces resolution and file size | `scale=1280:-1` (larger), `scale=640:-1` (smaller) |

**CRF Guidelines:**
| CRF | Quality | Typical Use Case | Relative Size |
|-----|---------|------------------|---------------|
| 0 | Lossless | Archival master | 10-50x |
| 18 | Visually lossless | High-quality archival | 2x |
| 23 | Good (default) | General recording | 1x |
| 28 | Acceptable | Storage-constrained | 0.5x |
| 35+ | Low | Previews only | 0.25x |

#### Two-Stage Recording Process

The current script uses a two-stage approach:

1. **Fast Capture Stage** (`-c:v copy`):
   - Records video without transcoding for minimal CPU load during capture
   - Uses MJPEG input format to reduce USB bandwidth
   - Ensures no dropped frames during recording
   - Results in larger temporary files

2. **Post-Recording Transcoding Stage**:
   - Automatically runs after recording completes (or when Ctrl+C is pressed)
   - Compresses videos using H.264 with CRF 23
   - Scales videos to 960px width to reduce file size
   - Saves transcoded files to `coded/` subdirectory with `_coded` suffix
   - Can be skipped with Ctrl+C if you want to transcode later with different settings

**Benefits of this approach:**
- Minimizes risk of dropped frames during recording (copy mode is very fast)
- Reduces USB bandwidth with MJPEG input format
- Still achieves good compression through post-recording transcoding
- Allows flexibility to skip or customize transcoding later

#### USB Bandwidth Management (MJPEG Input Mode)

The recording script now uses MJPEG input format by default:

```bash
ffmpeg -f v4l2 -input_format mjpeg -i /dev/video0 -r 60 -c:v copy ...
```

| Flag | Value | USB Bandwidth Impact |
|------|-------|---------------------|
| `-input_format mjpeg` | mjpeg | **Reduces by 5-10x** - Camera compresses before sending (now default) |
| (alternative) | yuyv422 | Full uncompressed - highest bandwidth |

**Benefits:**
- Dramatically reduces USB bandwidth, allowing more cameras per USB controller
- Combined with `-c:v copy`, there's minimal CPU overhead during recording
- The MJPEG stream is copied directly to file without re-encoding
- Post-recording transcoding handles compression and scaling

### Conversion Script (convert_files_gui.sh)

```bash
ffmpeg -i input.avi -b:v 2500k output_converted.avi
```

| Flag | Value | Description | Why Selected | Alternatives |
|------|-------|-------------|--------------|--------------|
| `-i` | input.avi | Input file | - | - |
| `-b:v` | 2500k | Video bitrate (2.5 Mbps) | Reasonable compression for archival | `1000k` (smaller), `5000k` (higher quality), use `-crf` instead for quality-based encoding |

### Video Combining Script (combine_videos.py)

The script builds ffmpeg commands dynamically. Key flags used:

#### Scaling Filter
```bash
-filter_complex "[0:v]scale=640:-1:flags=lanczos[v0]"
```

| Flag | Value | Description | Why Selected | Alternatives |
|------|-------|-------------|--------------|--------------|
| `scale=640:-1` | 640:-1 | Scale width to 640, auto-calculate height | Maintains aspect ratio | `scale=1280:-1` (larger), `scale=-1:480` (height-based) |
| `flags=lanczos` | lanczos | High-quality scaling algorithm | Best quality for downscaling | `bilinear` (faster), `bicubic` (balanced), `neighbor` (fastest, pixelated) |

#### Layout Filters
| Filter | Description | Use Case |
|--------|-------------|----------|
| `hstack` | Horizontal stack | Side-by-side videos |
| `vstack` | Vertical stack | Top-bottom videos |
| `xstack` | Grid layout | 2x2 or larger grids |

#### Quality Settings
| Quality Level | CRF | Preset | Use Case |
|---------------|-----|--------|----------|
| low | 28 | fast | Quick previews, small files |
| medium | 23 | medium | General use |
| high | 18 | slow | Archival, best quality |

### Legacy Streamer Script (parallel2video_streamer.sh)

```bash
streamer -q -c /dev/video0 -s 1280x720 -f jpeg -t 324000 -r 30 -j 75 -w 0 -o output.avi
```

| Flag | Value | Description |
|------|-------|-------------|
| `-q` | - | Quiet mode |
| `-c` | /dev/videoX | Capture device |
| `-s` | 1280x720 | Resolution |
| `-f` | jpeg | Output format (MJPEG) |
| `-t` | 324000 | Total frames (30fps × 60s × 180min) |
| `-r` | 30 | Frame rate |
| `-j` | 75 | JPEG quality (0-100) |
| `-w` | 0 | Wait time between frames |
| `-o` | output.avi | Output file |

### Choosing the Right Settings

Use this decision guide based on your primary constraint:

#### If USB Bandwidth Limited (multiple cameras, dropped frames)

**Symptoms:** Frames dropping, "select timeout" errors, cameras disconnecting

**Solutions (in order of effectiveness):**
1. ✓ **Already implemented**: Script uses MJPEG input format by default (reduces bandwidth 5-10x)
2. Lower frame rate: Change `-r 60` to `-r 30` or `-r 15` in the script
3. Add USB controllers (PCIe expansion cards)
4. Distribute cameras across different USB controllers

#### If CPU Limited (encoding can't keep up)

**Symptoms:** High CPU usage during recording, encoding warnings, growing latency

**Solutions (in order of effectiveness):**
1. ✓ **Already implemented**: Script uses `-c:v copy` mode during recording (minimal CPU)
2. For post-recording transcoding: Use hardware encoding in transcode scripts
3. Skip automatic transcoding (Ctrl+C) and transcode later when CPU is available
4. Reduce transcoding quality: Use lower CRF or faster preset in transcode scripts

#### If Storage Limited (running out of disk space)

**Symptoms:** Disk filling up quickly, need longer recordings

**Solutions (in order of effectiveness):**
1. ✓ **Already implemented**: Automatic transcoding after recording compresses files significantly
2. ✓ **Already implemented**: Transcoding scales to 960px width (reduces file size)
3. Adjust transcoding CRF: Modify script to use `-crf 28` instead of 23 (~50% additional reduction)
4. Lower recording frame rate: Change `-r 60` to `-r 30` or `-r 15` in recording script
5. Delete original uncompressed files after transcoding completes successfully

#### Quick Reference: Current Script Settings

| Feature | Current Setting | Effect | Alternative |
|---------|----------------|--------|-------------|
| USB bandwidth | `-input_format mjpeg` | -80% bandwidth | Remove flag for uncompressed |
| Recording CPU | `-c:v copy` | Minimal CPU during capture | `-c:v libx264` to encode during capture |
| Recording frame rate | `-r 60` | 60 fps capture | `-r 30` or `-r 15` for lower bandwidth |
| Transcoding quality | `-crf 23` | Balanced quality/size | `-crf 18` (larger) or `-crf 28` (smaller) |
| Transcoding resolution | `scale=960:-1` | 960px width | `scale=1280:-1` (larger) or `scale=640:-1` (smaller) |

#### For DeepLabCut/Tracking Applications
- ✓ **Already optimized**: Script uses MJPEG input for reduced USB bandwidth
- ✓ **Already optimized**: Copy mode during recording ensures no dropped frames
- ✓ **Already optimized**: Automatic transcoding compresses files after recording
- The 960px width scaling is suitable for most tracking applications
- Consistent frame rate (60 fps) is maintained throughout recording
- Consider lowering frame rate to 30 fps if 60 fps is not needed for your application

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
