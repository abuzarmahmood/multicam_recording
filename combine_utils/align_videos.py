#!/usr/bin/env python3
"""
Script to align multiple videos based on their timestamp files.
Outputs new video files with _aligned suffix, trimmed to start at the same wall-clock time.

For usage, type python align_videos.py -h
"""

import argparse
import os
import re
import subprocess
import sys
from typing import List, Optional, Tuple


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Align multiple videos based on timestamp files and output synchronized videos'
    )
    parser.add_argument(
        'input_videos',
        nargs='+',
        help='Input video files to align'
    )
    parser.add_argument(
        '-o', '--output-dir',
        help='Output directory for aligned videos (default: same as input)'
    )
    parser.add_argument(
        '--timestamps',
        nargs='+',
        help='Timestamp files for each video (in same order as input videos)'
    )
    parser.add_argument(
        '--suffix',
        default='_aligned',
        help='Suffix to add to output filenames (default: _aligned)'
    )
    parser.add_argument(
        '--quality',
        default='high',
        choices=['low', 'medium', 'high'],
        help='Output video quality (default: high)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print verbose output'
    )
    return parser.parse_args()


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
    match = re.search(r'cam(\d+)', video_name)
    if match:
        cam_num = match.group(1)
        timestamp_file = os.path.join(video_dir, f'cam{cam_num}_timestamps.txt')
        if os.path.exists(timestamp_file):
            return timestamp_file

    return None


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
            timestamp_files = list(args.timestamps)
            while len(timestamp_files) < len(input_videos):
                timestamp_files.append(None)
            return timestamp_files[:len(input_videos)]
        return args.timestamps

    # Auto-detect timestamp files
    timestamp_files = []
    for video in input_videos:
        ts_file = find_timestamp_file_for_video(video)
        timestamp_files.append(ts_file)
    return timestamp_files


def calculate_alignment_offsets(timestamp_files: List[Optional[str]], verbose: bool = False) -> Tuple[List[float], float]:
    """
    Calculate time offsets to align videos based on their first timestamps.
    
    Returns:
        - List of offsets in seconds (how much to trim from start of each video)
        - The latest start time (used to calculate common end time)
    """
    first_timestamps = []

    for ts_file in timestamp_files:
        if ts_file is None:
            first_timestamps.append(None)
            continue

        timestamps = read_timestamp_file(ts_file)
        if timestamps and len(timestamps) > 0:
            first_timestamps.append(timestamps[0])
            if verbose:
                print(f"  {ts_file}: first timestamp = {timestamps[0]:.3f}s")
        else:
            first_timestamps.append(None)

    # Find the maximum (latest) start timestamp - all videos need to be trimmed to this point
    valid_timestamps = [t for t in first_timestamps if t is not None]
    if not valid_timestamps:
        return [0.0] * len(timestamp_files), 0.0

    max_timestamp = max(valid_timestamps)

    # Calculate offsets - how much to trim from the start of each video
    offsets = []
    for ts in first_timestamps:
        if ts is not None:
            offsets.append(max_timestamp - ts)
        else:
            offsets.append(0.0)

    return offsets, max_timestamp


def get_quality_settings(quality: str) -> dict:
    """Get ffmpeg quality settings based on quality level"""
    settings = {
        'low': {'crf': '28', 'preset': 'fast'},
        'medium': {'crf': '23', 'preset': 'medium'},
        'high': {'crf': '18', 'preset': 'slow'}
    }
    return settings.get(quality, settings['high'])


def get_output_path(input_video: str, output_dir: Optional[str], suffix: str) -> str:
    """Generate output path for aligned video"""
    video_dir = os.path.dirname(input_video) or '.'
    video_name = os.path.basename(input_video)
    name, ext = os.path.splitext(video_name)

    out_dir = output_dir if output_dir else video_dir
    return os.path.join(out_dir, f"{name}{suffix}{ext}")


def align_video(input_video: str, output_video: str, offset: float, quality: str, verbose: bool = False) -> bool:
    """
    Create an aligned version of a video by trimming from the start.
    
    Args:
        input_video: Path to input video
        output_video: Path to output video
        offset: Seconds to trim from the start
        quality: Quality setting (low/medium/high)
        verbose: Print verbose output
    
    Returns:
        True if successful, False otherwise
    """
    quality_settings = get_quality_settings(quality)

    cmd = ['ffmpeg', '-y']

    # Use -ss before -i for fast seeking
    if offset > 0:
        cmd.extend(['-ss', str(offset)])

    cmd.extend(['-i', input_video])
    cmd.extend(['-c:v', 'libx264'])
    cmd.extend(['-crf', quality_settings['crf']])
    cmd.extend(['-preset', quality_settings['preset']])
    cmd.extend(['-c:a', 'copy'])  # Copy audio if present
    cmd.append(output_video)

    if verbose:
        print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing {input_video}: {e}")
        if verbose:
            print(f"FFmpeg stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please install ffmpeg.")
        return False


def validate_input_files(input_videos: List[str]) -> bool:
    """Validate that all input files exist and are readable"""
    for video in input_videos:
        if not os.path.exists(video):
            print(f"Error: Input file '{video}' does not exist")
            return False
        if not os.access(video, os.R_OK):
            print(f"Error: Cannot read input file '{video}'")
            return False
    return True


def main():
    """Main function to align videos"""
    args = parse_arguments()

    # Validate input files
    if not validate_input_files(args.input_videos):
        sys.exit(1)

    # Create output directory if specified and doesn't exist
    if args.output_dir and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # Get timestamp files
    timestamp_files = get_timestamp_files(args, args.input_videos)

    # Check if we have any timestamp files
    valid_ts_files = [f for f in timestamp_files if f is not None]
    if not valid_ts_files:
        print("Error: No timestamp files found. Provide --timestamps or ensure "
              "cam*_timestamps.txt files exist alongside videos.")
        sys.exit(1)

    print(f"Found {len(valid_ts_files)} timestamp files for {len(args.input_videos)} videos")

    # Calculate alignment offsets
    if args.verbose:
        print("\nReading timestamps:")
    offsets, latest_start = calculate_alignment_offsets(timestamp_files, args.verbose)

    print(f"\nAlignment offsets (seconds to trim from start):")
    for i, (video, offset) in enumerate(zip(args.input_videos, offsets)):
        print(f"  {os.path.basename(video)}: {offset:.3f}s")

    # Process each video
    print(f"\nAligning videos...")
    success_count = 0
    for i, (video, offset) in enumerate(zip(args.input_videos, offsets)):
        output_path = get_output_path(video, args.output_dir, args.suffix)
        print(f"  [{i+1}/{len(args.input_videos)}] {os.path.basename(video)} -> {os.path.basename(output_path)}")

        if align_video(video, output_path, offset, args.quality, args.verbose):
            success_count += 1
        else:
            print(f"    Failed to align {video}")

    print(f"\nCompleted: {success_count}/{len(args.input_videos)} videos aligned successfully")

    if success_count < len(args.input_videos):
        sys.exit(1)


if __name__ == '__main__':
    main()
