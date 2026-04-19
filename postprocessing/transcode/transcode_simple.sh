#!/bin/bash
# ffmpeg -i name_cam0.mp4 -c:v libx264 -crf 23 -vf scale=960:-1 name_cam0_coded.mp4

: '
Simple script to transcode MP4 files in a directory
Finds all .mp4 files without "coded" in filename and compresses them
Uses: ffmpeg -i name_cam0.mp4 -c:v libx264 -crf 23 -vf scale=960:-1 name_cam0_coded.mp4

Supports per-camera cropping from config.json:
  "crop": {
    "cam0": [x1, x2, y1, y2],
    "cam1": [x1, x2, y1, y2]
  }
Where [x1, x2, y1, y2] are left, right, top, bottom edges
ffmpeg crop filter: crop=w:h:x:y where w=x2-x1, h=y2-y1, x=x1, y=y1
'

# Function to load crop settings from config
# Sets: CROP_SETTINGS associative array
declare -A CROP_SETTINGS

load_crop_settings() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local config_file="$script_dir/../config.json"
    
    # Check if config file exists
    if [[ ! -f "$config_file" ]]; then
        return 0
    fi
    
    # Check if crop section exists in config
    local crop_exists
    crop_exists=$(jq -r '.crop // empty' "$config_file" 2>/dev/null)
    if [[ -z "$crop_exists" || "$crop_exists" == "null" || "$crop_exists" == "{}" ]]; then
        return 0
    fi
    
    # Check if crop is enabled
    local crop_enabled
    crop_enabled=$(jq -r '.crop.enabled // false' "$config_file" 2>/dev/null)
    if [[ "$crop_enabled" != "true" ]]; then
        return 0
    fi
    
    # Read crop settings for each camera (skip 'enabled' key)
    local cam_keys
    mapfile -t cam_keys < <(jq -r '.crop | keys[]' "$config_file" 2>/dev/null)
    
    for cam_key in "${cam_keys[@]}"; do
        # Skip the enabled flag key
        if [[ "$cam_key" == "enabled" ]]; then
            continue
        fi
        local crop_values
        # Get the array as a space-separated string
        crop_values=$(jq -r ".crop[\"$cam_key\"] | .[] | tostring" "$config_file" 2>/dev/null)
        if [[ -n "$crop_values" ]]; then
            CROP_SETTINGS[$cam_key]="$crop_values"
        fi
    done
    
    if [[ ${#CROP_SETTINGS[@]} -gt 0 ]]; then
        echo "Loaded crop settings for ${#CROP_SETTINGS[@]} camera(s)"
    fi
}

# Function to get crop filter for a camera
# Args: $1 = cam_key (e.g., cam0, cam1)
# Returns: crop filter string or empty
get_crop_filter() {
    local cam_key="$1"
    local crop_values="${CROP_SETTINGS[$cam_key]}"
    
    if [[ -z "$crop_values" ]]; then
        return 0
    fi
    
    # Parse crop values: x1 x2 y1 y2
    local x1 x2 y1 y2
    read -r x1 x2 y1 y2 <<< "$crop_values"
    
    # Calculate crop parameters for ffmpeg
    # crop=w:h:x:y where w=width, h=height, x=x_offset, y=y_offset
    local crop_w=$((x2 - x1))
    local crop_h=$((y2 - y1))
    
    if [[ $crop_w -le 0 || $crop_h -le 0 ]]; then
        echo ""
        return 0
    fi
    
    echo "crop=${crop_w}:${crop_h}:${x1}:${y1}"
}

# Function to transcode a single video
transcode_video() {
    local input_file="$1"
    local dir=$(dirname "$input_file")
    local basename=$(basename "$input_file" .mp4)
    local coded_dir="$dir/coded"
    local output_file="$coded_dir/${basename}_coded.mp4"
    
    # Create coded subdirectory if it doesn't exist
    if [[ ! -d "$coded_dir" ]]; then
        mkdir -p "$coded_dir"
    fi
    
    # Skip if output file already exists
    if [[ -f "$output_file" ]]; then
        echo "Skipping $input_file - output file already exists"
        return 0
    fi
    
    # Extract camera index from filename (e.g., "name_cam0.mp4" -> "cam0")
    local cam_key=""
    if [[ "$basename" =~ _cam([0-9]+)$ ]]; then
        cam_key="cam${BASH_REMATCH[1]}"
    fi
    
    # Get crop filter for this camera (if configured)
    local crop_filter=""
    if [[ -n "$cam_key" ]]; then
        crop_filter=$(get_crop_filter "$cam_key")
    fi
    
    echo "Processing: $input_file -> $output_file"
    if [[ -n "$crop_filter" ]]; then
        echo "  Applying crop: $crop_filter"
    fi
    
    # Build ffmpeg filter string
    local vf_filter=""
    if [[ -n "$crop_filter" ]]; then
        vf_filter="-vf $crop_filter"
    fi
    
    # Execute FFmpeg command with suppressed output
    if ffmpeg -loglevel error -i "$input_file" -c:v libx264 -crf 23 $vf_filter "$output_file"; then
        echo "✓ Successfully transcoded: $basename"
        
        # Show file size comparison
        local original_size=$(stat -f%z "$input_file" 2>/dev/null || stat -c%s "$input_file" 2>/dev/null)
        local new_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
        
        if [[ -n "$original_size" && -n "$new_size" ]]; then
            printf "Original: %.2f MB -> New: %.2f MB\n" \
                "$(echo "$original_size / 1048576" | bc -l)" \
                "$(echo "$new_size / 1048576" | bc -l)"
        fi
        echo ""
    else
        echo "✗ Failed to transcode: $input_file"
        return 1
    fi
}

# Main function
main() {
    local target_dir="."
    
    # Parse arguments
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        "")
            target_dir="."
            ;;
        *)
            target_dir="$1"
            ;;
    esac
    
    # Check if directory exists
    if [[ ! -d "$target_dir" ]]; then
        echo "Error: Directory '$target_dir' does not exist"
        exit 1
    fi
    
    # Check if ffmpeg is available
    if ! command -v ffmpeg &> /dev/null; then
        echo "Error: ffmpeg is not installed"
        exit 1
    fi
    
    # Load crop settings from config
    load_crop_settings
    
    echo "Looking for MP4 files in: $target_dir"
    
    # Find all .mp4 files that don't have "coded" in their filename
    local video_files=()
    while IFS= read -r -d '' file; do
        local basename=$(basename "$file")
        if [[ "$basename" != *"coded"* ]]; then
            video_files+=("$file")
        fi
    done < <(find "$target_dir" -maxdepth 1 -name "*.mp4" -type f -print0)
    
    # Check if any files were found
    if [[ ${#video_files[@]} -eq 0 ]]; then
        echo "No MP4 files found (or all files already have 'coded' in filename)"
        exit 0
    fi
    
    echo "Found ${#video_files[@]} video file(s) to process"
    
    # Process each video file
    local success_count=0
    local total_count=${#video_files[@]}
    
    for file in "${video_files[@]}"; do
        if transcode_video "$file"; then
            ((success_count++))
        fi
    done
    
    echo "Transcoding completed: $success_count/$total_count files processed successfully"
}

# Run main function with all arguments
main "$@"
