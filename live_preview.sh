#!/bin/bash

: '
Script to play live video from all configured cameras simultaneously.
Reads camera devices from config.json and displays them in a grid
using ffmpeg filter_complex piped to ffplay.

Uses the same device loading logic as the recording scripts via recording_utils.sh.
'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils/recording_utils.sh"

# Help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo ""
    echo "Play live video from all configured cameras in a grid layout."
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message and exit"
    echo "  --scale W     Scale width for each video (default: 640)"
    echo ""
    echo "Requirements:"
    echo "  - ffmpeg / ffplay"
    echo "  - jq"
    echo "  - Video devices configured in config.json"
    echo ""
    echo "Press 'q' or Ctrl+C to stop."
    exit 0
fi

# Parse optional --scale argument
SCALE_WIDTH=640
while [[ $# -gt 0 ]]; do
    case "$1" in
        --scale)
            SCALE_WIDTH="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Load video devices from config (sets AVAILABLE_DEVICES and NUM_CAMERAS)
load_video_devices "$SCRIPT_DIR" || exit 1

if [ "$NUM_CAMERAS" -eq 0 ]; then
    echo "❌ No cameras available for preview."
    exit 1
fi

# Determine grid layout based on number of cameras.
# Mirrors the auto-layout logic from combine_utils/combine_videos.py.
determine_grid() {
    local n=$1
    if [ "$n" -eq 1 ]; then
        GRID_ROWS=1; GRID_COLS=1
    elif [ "$n" -eq 2 ]; then
        GRID_ROWS=1; GRID_COLS=2
    elif [ "$n" -eq 3 ]; then
        GRID_ROWS=1; GRID_COLS=3
    elif [ "$n" -eq 4 ]; then
        GRID_ROWS=2; GRID_COLS=2
    elif [ "$n" -le 6 ]; then
        GRID_ROWS=2; GRID_COLS=3
    else
        GRID_COLS=$(echo "sqrt($n) + 1" | bc)
        GRID_ROWS=$(( (n + GRID_COLS - 1) / GRID_COLS ))
    fi
}

determine_grid "$NUM_CAMERAS"
echo "Grid layout: ${GRID_ROWS}x${GRID_COLS} for $NUM_CAMERAS camera(s)"

# Single camera: play directly with ffplay
if [ "$NUM_CAMERAS" -eq 1 ]; then
    echo "Playing live preview from ${AVAILABLE_DEVICES[0]}..."
    exec ffplay -f v4l2 -input_format mjpeg -video_size 1280x720 -framerate 30 \
        -i "${AVAILABLE_DEVICES[0]}" \
        -window_title "Live Preview - ${AVAILABLE_DEVICES[0]}"
fi

# Multiple cameras: use ffmpeg to combine into a grid, pipe to ffplay

# Build ffmpeg input arguments
INPUT_ARGS=()
for device in "${AVAILABLE_DEVICES[@]}"; do
    INPUT_ARGS+=(-f v4l2 -input_format mjpeg -video_size 1280x720 -framerate 30 -i "$device")
done

# Build filter_complex
FILTER=""

# Scale each input
for i in "${!AVAILABLE_DEVICES[@]}"; do
    FILTER+="[$i:v]scale=${SCALE_WIDTH}:-1[v$i];"
done

if [ "$GRID_ROWS" -eq 1 ]; then
    # Single row: hstack
    LABELS=""
    for i in "${!AVAILABLE_DEVICES[@]}"; do
        LABELS+="[v$i]"
    done
    FILTER+="${LABELS}hstack=inputs=${NUM_CAMERAS}[out]"

elif [ "$GRID_COLS" -eq 1 ]; then
    # Single column: vstack
    LABELS=""
    for i in "${!AVAILABLE_DEVICES[@]}"; do
        LABELS+="[v$i]"
    done
    FILTER+="${LABELS}vstack=inputs=${NUM_CAMERAS}[out]"

else
    # General grid: hstack each row, then vstack the rows.
    # Pad with black frames if cameras don't fill the grid.
    TOTAL_SLOTS=$(( GRID_ROWS * GRID_COLS ))
    PADDING_NEEDED=$(( TOTAL_SLOTS - NUM_CAMERAS ))
    SCALE_HEIGHT=$(( SCALE_WIDTH * 9 / 16 ))

    NULL_IDX=$NUM_CAMERAS
    for (( p=0; p<PADDING_NEEDED; p++ )); do
        INPUT_ARGS+=(-f lavfi -i "color=c=black:s=${SCALE_WIDTH}x${SCALE_HEIGHT}:r=30")
        FILTER+="[$NULL_IDX:v]scale=${SCALE_WIDTH}:-1[v$NULL_IDX];"
        NULL_IDX=$(( NULL_IDX + 1 ))
    done

    # Build each row
    for (( r=0; r<GRID_ROWS; r++ )); do
        ROW_LABELS=""
        for (( c=0; c<GRID_COLS; c++ )); do
            IDX=$(( r * GRID_COLS + c ))
            ROW_LABELS+="[v$IDX]"
        done
        FILTER+="${ROW_LABELS}hstack=inputs=${GRID_COLS}[row$r];"
    done

    # Stack rows vertically
    ROW_STREAM_LABELS=""
    for (( r=0; r<GRID_ROWS; r++ )); do
        ROW_STREAM_LABELS+="[row$r]"
    done
    FILTER+="${ROW_STREAM_LABELS}vstack=inputs=${GRID_ROWS}[out]"
fi

echo "Playing live preview from $NUM_CAMERAS cameras..."
echo "Press 'q' to quit."

# Pipe combined video through ffmpeg to ffplay.
# -probesize and -analyzeduration are low to minimize startup latency.
# -f nut is a low-overhead container suitable for piping.
ffmpeg \
    -probesize 32 -analyzeduration 0 \
    "${INPUT_ARGS[@]}" \
    -filter_complex "$FILTER" \
    -map "[out]" \
    -f nut -c:v rawvideo -pix_fmt yuv420p \
    -an - 2>/dev/null \
| ffplay \
    -autoexit \
    -window_title "Live Preview - All Cameras" \
    -
