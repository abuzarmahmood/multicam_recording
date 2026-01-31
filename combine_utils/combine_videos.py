#!/usr/bin/env python3
"""
Script to combine multiple videos into a single frame showing all videos simultaneously
For usage, type python combine_videos.py -h
"""

# ___       _ _   _       _ _         
#|_ _|_ __ (_) |_(_) __ _| (_)_______ 
# | || '_ \| | __| |/ _` | | |_  / _ \
# | || | | | | |_| | (_| | | |/ /  __/
#|___|_| |_|_|\__|_|\__,_|_|_/___\___|
#                                     

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Combine multiple videos into a single frame showing all videos simultaneously'
    )
    parser.add_argument(
        'input_videos', 
        nargs='+', 
        help='Input video files to combine'
    )
    parser.add_argument(
        '-o', '--output', 
        required=True,
        help='Output video file path'
    )
    parser.add_argument(
        '--grid', 
        choices=['2x1', '1x2', '2x2', '3x1', '1x3', 'auto'],
        default='auto',
        help='Grid layout for combining videos (default: auto)'
    )
    parser.add_argument(
        '--scale',
        type=int,
        default=640,
        help='Scale width for each video in the grid (default: 640)'
    )
    parser.add_argument(
        '--quality',
        default='high',
        choices=['low', 'medium', 'high'],
        help='Output video quality (default: high)'
    )
    parser.add_argument(
        '--timestamps',
        nargs='+',
        help='Timestamp files for each video (in same order as input videos). '
             'Used to align videos based on wall-clock timestamps.'
    )
    parser.add_argument(
        '--align',
        action='store_true',
        help='Auto-detect timestamp files based on video filenames (looks for cam*_timestamps.txt)'
    )
    return parser.parse_args()

def determine_grid_layout(num_videos, grid_option):
    """Determine the optimal grid layout based on number of videos"""
    if grid_option != 'auto':
        rows, cols = map(int, grid_option.split('x'))
        return rows, cols
    
    # Auto-determine best layout
    if num_videos == 1:
        return 1, 1
    elif num_videos == 2:
        return 1, 2  # Side by side
    elif num_videos == 3:
        return 1, 3  # Side by side
    elif num_videos == 4:
        return 2, 2  # 2x2 grid
    elif num_videos <= 6:
        return 2, 3  # 2 rows, 3 columns
    else:
        # For more videos, create a roughly square grid
        cols = int(num_videos ** 0.5) + 1
        rows = (num_videos + cols - 1) // cols
        return rows, cols

def get_quality_settings(quality):
    """Get ffmpeg quality settings based on quality level"""
    settings = {
        'low': {'crf': '28', 'preset': 'fast'},
        'medium': {'crf': '23', 'preset': 'medium'},
        'high': {'crf': '18', 'preset': 'slow'}
    }
    return settings.get(quality, settings['high'])

def build_ffmpeg_command(input_videos, output_file, rows, cols, scale_width, quality, offsets=None):
    """Build the ffmpeg command for combining videos"""
    quality_settings = get_quality_settings(quality)
    
    if offsets is None:
        offsets = [0.0] * len(input_videos)
    
    # Start building the command
    cmd = ['ffmpeg']
    
    # Add input files with timing offsets using itsoffset
    for i, video in enumerate(input_videos):
        if offsets[i] > 0:
            # Delay this video by the offset amount
            cmd.extend(['-itsoffset', str(offsets[i])])
        cmd.extend(['-i', video])
    
    # Build filter complex
    filter_parts = []
    
    # Scale all inputs to the same size
    for i, video in enumerate(input_videos):
        filter_parts.append(f'[{i}:v]scale={scale_width}:-1:flags=lanczos[v{i}]')
    
    # Create grid layout
    inputs = []
    for i in range(len(input_videos)):
        inputs.append(f'[v{i}]')
    
    inputs_str = ''.join(inputs)
    
    if rows == 1 and cols == 1:
        # Single video case
        filter_parts.append(f'{inputs_str}concat=n=1:v=1:a=0[outv]')
    elif rows == 1:
        # Horizontal layout
        filter_parts.append(f'{inputs_str}hstack=inputs={len(input_videos)}[outv]')
    elif cols == 1:
        # Vertical layout
        filter_parts.append(f'{inputs_str}vstack=inputs={len(input_videos)}[outv]')
    else:
        # Grid layout - need to handle this more carefully
        # For simplicity, we'll use xstack for grid layouts
        filter_parts.append(f'{inputs_str}xstack=inputs={len(input_videos)}:layout={generate_layout_string(len(input_videos), rows, cols, scale_width)}[outv]')
    
    filter_complex = ';'.join(filter_parts)
    
    # Add filter complex to command
    cmd.extend(['-filter_complex', filter_complex])
    
    # Map output
    cmd.extend(['-map', '[outv]'])
    
    # Add quality settings
    cmd.extend(['-c:v', 'libx264'])
    cmd.extend(['-crf', quality_settings['crf']])
    cmd.extend(['-preset', quality_settings['preset']])
    
    # Add output file
    cmd.extend(['-y', output_file])  # -y to overwrite output file
    
    return cmd

def generate_layout_string(num_videos, rows, cols, scale_width):
    """Generate layout string for xstack filter"""
    layout = []
    # Calculate aspect ratio (assuming 16:9)
    scale_height = int(scale_width * 9 / 16)
    
    for i in range(num_videos):
        row = i // cols
        col = i % cols
        x = col * scale_width
        y = row * scale_height
        layout.append(f'{i}_w/{cols}*{col}:{i}_h/{rows}*{row}')
    
    return '|'.join(layout)

def validate_input_files(input_videos):
    """Validate that all input files exist and are readable"""
    for video in input_videos:
        if not os.path.exists(video):
            print(f"Error: Input file '{video}' does not exist")
            return False
        if not os.access(video, os.R_OK):
            print(f"Error: Cannot read input file '{video}'")
            return False
    return True


def read_timestamp_file(timestamp_file: str) -> Optional[List[float]]:
    """
    Read timestamps from an mkvtimestamp_v2 format file.
    
    The format has a header line "# timestamp format v2" followed by
    timestamps in milliseconds, one per line.
    
    Returns list of timestamps in seconds, or None if file cannot be read.
    """
    if not os.path.exists(timestamp_file):
        return None
    
    timestamps = []
    try:
        with open(timestamp_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip header and empty lines
                if line.startswith('#') or not line:
                    continue
                try:
                    # Timestamps are in milliseconds, convert to seconds
                    timestamps.append(float(line) / 1000.0)
                except ValueError:
                    continue
    except IOError as e:
        print(f"Warning: Could not read timestamp file '{timestamp_file}': {e}")
        return None
    
    return timestamps if timestamps else None


def find_timestamp_file_for_video(video_path: str) -> Optional[str]:
    """
    Auto-detect timestamp file for a video based on naming convention.
    
    Looks for cam*_timestamps.txt in the same directory as the video.
    For a video named 'name_cam0.mp4', looks for 'cam0_timestamps.txt'.
    """
    video_dir = os.path.dirname(video_path) or '.'
    video_name = os.path.basename(video_path)
    
    # Extract camera number from video filename (e.g., name_cam0.mp4 -> 0)
    import re
    match = re.search(r'cam(\d+)', video_name)
    if match:
        cam_num = match.group(1)
        timestamp_file = os.path.join(video_dir, f'cam{cam_num}_timestamps.txt')
        if os.path.exists(timestamp_file):
            return timestamp_file
    
    return None


def calculate_alignment_offsets(timestamp_files: List[Optional[str]]) -> List[float]:
    """
    Calculate time offsets to align videos based on their first timestamps.
    
    Returns a list of offsets in seconds. Each video should be delayed by
    its offset to align with the video that started earliest.
    """
    first_timestamps = []
    
    for ts_file in timestamp_files:
        if ts_file is None:
            first_timestamps.append(None)
            continue
        
        timestamps = read_timestamp_file(ts_file)
        if timestamps and len(timestamps) > 0:
            first_timestamps.append(timestamps[0])
        else:
            first_timestamps.append(None)
    
    # Find the minimum (earliest) timestamp among all videos
    valid_timestamps = [t for t in first_timestamps if t is not None]
    if not valid_timestamps:
        # No valid timestamps, return zero offsets
        return [0.0] * len(timestamp_files)
    
    min_timestamp = min(valid_timestamps)
    
    # Calculate offsets relative to the earliest video
    offsets = []
    for ts in first_timestamps:
        if ts is not None:
            offsets.append(ts - min_timestamp)
        else:
            offsets.append(0.0)
    
    return offsets


def get_timestamp_files(args, input_videos: List[str]) -> List[Optional[str]]:
    """
    Get timestamp files based on command line arguments.
    
    Returns a list of timestamp file paths (or None for videos without timestamps).
    """
    if args.timestamps:
        # Explicit timestamp files provided
        if len(args.timestamps) != len(input_videos):
            print(f"Warning: Number of timestamp files ({len(args.timestamps)}) "
                  f"doesn't match number of videos ({len(input_videos)})")
            # Pad with None or truncate
            timestamp_files = list(args.timestamps)
            while len(timestamp_files) < len(input_videos):
                timestamp_files.append(None)
            return timestamp_files[:len(input_videos)]
        return args.timestamps
    
    elif args.align:
        # Auto-detect timestamp files
        timestamp_files = []
        for video in input_videos:
            ts_file = find_timestamp_file_for_video(video)
            timestamp_files.append(ts_file)
            if ts_file:
                print(f"Found timestamp file for {video}: {ts_file}")
            else:
                print(f"No timestamp file found for {video}")
        return timestamp_files
    
    return [None] * len(input_videos)

def main():
    """Main function to combine videos"""
    args = parse_arguments()
    
    # Validate input files
    if not validate_input_files(args.input_videos):
        sys.exit(1)
    
    # Determine grid layout
    rows, cols = determine_grid_layout(len(args.input_videos), args.grid)
    
    print(f"Combining {len(args.input_videos)} videos into {rows}x{cols} grid")
    print(f"Output file: {args.output}")
    print(f"Scale width: {args.scale}")
    print(f"Quality: {args.quality}")
    
    # Build ffmpeg command
    cmd = build_ffmpeg_command(
        args.input_videos, 
        args.output, 
        rows, 
        cols, 
        args.scale, 
        args.quality
    )
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run ffmpeg command
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Successfully combined videos into {args.output}")
    except subprocess.CalledProcessError as e:
        print(f"Error combining videos: {e}")
        print(f"FFmpeg stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please install ffmpeg.")
        sys.exit(1)

if __name__ == '__main__':
    main()
