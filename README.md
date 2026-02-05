
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
- **NEW**: Option to record single channel (Y/luminance only) for better performance using extractplanes filter

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

The main recording command uses:
```bash
ffmpeg -use_wallclock_as_timestamps 1 -copyts -f v4l2 -i /dev/video0 -s 1280x720 -r 30 -c:v libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p output.mp4
```

#### Camera/Hardware Flags (Affect USB Bandwidth)

These flags configure what the camera captures and sends over USB. They directly affect USB bandwidth consumption.

| Flag | Value | Description | USB Bandwidth Impact | Alternatives |
|------|-------|-------------|---------------------|--------------|
| `-f v4l2` | v4l2 | Video4Linux2 input format | None (just specifies driver) | `-f dshow` (Windows), `-f avfoundation` (macOS) |
| `-i` | /dev/videoX | Input device path | None | Use `v4l2-ctl --list-devices` to find devices |
| `-s` | 1280x720 | **Resolution requested from camera** | **HIGH** - 720p uses ~2.5x bandwidth of 480p | `640x480` (saves ~60% bandwidth), `1920x1080` (uses ~2.25x more) |
| `-r` | 30 | **Frame rate requested from camera** | **HIGH** - Directly proportional to bandwidth | `15` (halves bandwidth), `60` (doubles bandwidth) |

**USB Bandwidth Calculation:**
```
Bandwidth = Width × Height × Bytes_per_pixel × FPS
Example: 1280 × 720 × 2 (YUYV) × 30 = 55.3 MB/s per camera
```

USB 2.0 practical limit is ~53 MB/s total, so 720p30 in raw format can only support 1 camera per USB controller. Use MJPEG input mode (`-input_format mjpeg`) to reduce this significantly.

#### Software/CPU Flags (Affect CPU Load)

These flags control how ffmpeg processes and encodes the video on your CPU. They don't affect what the camera sends.

| Flag | Value | Description | CPU Impact | Alternatives |
|------|-------|-------------|------------|--------------|
| `-c:v libx264` | libx264 | **Software H.264 encoder** | **HIGH** - All encoding done on CPU | `h264_nvenc` (NVIDIA GPU, very low CPU), `h264_vaapi` (Intel GPU), `h264_qsv` (Intel QuickSync) |
| `-preset ultrafast` | ultrafast | **Encoding speed/quality tradeoff** | **Selected for LOW CPU** - Fastest encoding | `superfast` → `veryslow` (slower = more CPU, better compression) |
| `-vf extractplanes=y` | y | Extract luminance only | **REDUCES** - Less data to encode | Full color (more CPU), other planes |
| `-use_wallclock_as_timestamps 1` | 1 | Use system clock for timestamps | Minimal | Default timestamps |
| `-copyts` | - | Preserve timestamps | Minimal | - |

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

These flags control the output file characteristics. They don't affect USB bandwidth or significantly affect CPU (except indirectly through compression).

| Flag | Value | Description | File Size Impact | Alternatives |
|------|-------|-------------|------------------|--------------|
| `-crf` | 23 | **Constant Rate Factor (quality)** | **DIRECT** - Lower = larger, higher quality | `18` (visually lossless, ~2x size), `28` (smaller, lower quality), `0` (lossless, huge) |
| `-pix_fmt yuv420p` | yuv420p | Pixel format in output | Minimal (standard) | `yuv444p` (better color, larger), `gray` (grayscale, smaller) |

**CRF Guidelines:**
| CRF | Quality | Typical Use Case | Relative Size |
|-----|---------|------------------|---------------|
| 0 | Lossless | Archival master | 10-50x |
| 18 | Visually lossless | High-quality archival | 2x |
| 23 | Good (default) | General recording | 1x |
| 28 | Acceptable | Storage-constrained | 0.5x |
| 35+ | Low | Previews only | 0.25x |

#### Single Channel Recording (extractplanes filter)

When single-channel mode is enabled:
```bash
ffmpeg ... -vf "extractplanes=y" ...
```

| Flag | Value | Description | Category | Impact |
|------|-------|-------------|----------|--------|
| `-vf extractplanes=y` | y | Extract Y (luminance) plane only | Software | Reduces CPU load and file size by ~50% |

**Why use single channel?**
- Color information is often unnecessary for tracking/DeepLabCut applications
- Reduces encoding workload (CPU impact)
- Reduces file size by approximately 50%
- Does NOT reduce USB bandwidth (camera still sends full color)

**Alternative plane options:** `u`, `v` (chrominance), `r`, `g`, `b`, `a` (RGBA components)

#### Reducing USB Bandwidth (MJPEG Input Mode)

If you're hitting USB bandwidth limits with multiple cameras, you can request MJPEG format from the camera:

```bash
ffmpeg -f v4l2 -input_format mjpeg -i /dev/video0 ...
```

| Flag | Value | USB Bandwidth Impact |
|------|-------|---------------------|
| `-input_format mjpeg` | mjpeg | **Reduces by 5-10x** - Camera compresses before sending |
| (default) | yuyv422 | Full uncompressed - highest bandwidth |

**Trade-off:** MJPEG input adds a decode step (slight CPU increase) but dramatically reduces USB bandwidth, allowing more cameras per USB controller.

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
1. Use MJPEG input: `-input_format mjpeg` (reduces bandwidth 5-10x)
2. Lower resolution: `-s 640x480` instead of 720p
3. Lower frame rate: `-r 15` instead of 30
4. Add USB controllers (PCIe expansion cards)
5. Distribute cameras across different USB controllers

#### If CPU Limited (encoding can't keep up)

**Symptoms:** High CPU usage, encoding warnings, growing latency

**Solutions (in order of effectiveness):**
1. Use hardware encoding: `-c:v h264_nvenc` (NVIDIA) or `-c:v h264_vaapi` (Intel)
2. Use fastest preset: `-preset ultrafast` (already default)
3. Use single-channel mode: `-vf extractplanes=y`
4. Lower resolution (reduces pixels to encode)

#### If Storage Limited (running out of disk space)

**Symptoms:** Disk filling up quickly, need longer recordings

**Solutions (in order of effectiveness):**
1. Use single-channel mode: `-vf extractplanes=y` (~50% reduction)
2. Increase CRF: `-crf 28` instead of 23 (~50% reduction)
3. Use slower preset (if CPU allows): `-preset medium` (~40% reduction)
4. Lower resolution: `-s 640x480` (~75% reduction from 720p)
5. Lower frame rate: `-r 15` (~50% reduction)

#### Quick Reference: Flag Changes by Constraint

| Constraint | Flag to Change | From | To | Effect |
|------------|---------------|------|-----|--------|
| USB bandwidth | `-input_format` | (none) | `mjpeg` | -80% bandwidth |
| USB bandwidth | `-s` | `1280x720` | `640x480` | -60% bandwidth |
| USB bandwidth | `-r` | `30` | `15` | -50% bandwidth |
| CPU load | `-c:v` | `libx264` | `h264_nvenc` | -90% CPU |
| CPU load | `-vf` | (none) | `extractplanes=y` | -30% CPU |
| File size | `-crf` | `23` | `28` | -50% size |
| File size | `-vf` | (none) | `extractplanes=y` | -50% size |
| File size | `-preset` | `ultrafast` | `medium` | -40% size |

#### For DeepLabCut/Tracking Applications
- Single-channel (Y plane) recording reduces file size without losing tracking accuracy
- Lower resolutions (640x480) may be sufficient and reduce bandwidth
- Consistent frame rate is more important than high resolution
- MJPEG input mode is recommended for multi-camera setups

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
