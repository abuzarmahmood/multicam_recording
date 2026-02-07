#!/bin/bash

: '
Simple script to transcode MP4 files in a directory
Finds all .mp4 files without "coded" in filename and compresses them
Uses: ffmpeg -i name_cam0.mp4 -c:v libx264 -crf 23 -vf scale=960:-1 name_cam0_coded.mp4
'

# Function to show help
show_help() {
    cat << EOF
Usage: $0 [DIRECTORY]

Simple video transcoding script that:
- Finds all .mp4 files in the specified directory (or current directory)
- Skips files that already have "coded" in their filename
- Compresses them using H.264 with CRF 23 and scales to 960px width
- Adds "_coded" suffix to output filename

EXAMPLES:
    $0                    # Process current directory
    $0 /path/to/videos    # Process specific directory

EOF
}

# Function to transcode a single video
transcode_video() {
    local input_file="$1"
    local dir=$(dirname "$input_file")
    local basename=$(basename "$input_file" .mp4)
    local output_file="$dir/${basename}_coded.mp4"
    
    # Skip if output file already exists
    if [[ -f "$output_file" ]]; then
        echo "Skipping $input_file - output file already exists"
        return 0
    fi
    
    echo "Processing: $input_file -> $output_file"
    
    # Execute FFmpeg command
    if ffmpeg -i "$input_file" -c:v libx264 -crf 23 -vf scale=960:-1 "$output_file"; then
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
    
    echo "Looking for MP4 files in: $target_dir"
    echo ""
    
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
    
    echo "Found ${#video_files[@]} video file(s) to process:"
    for file in "${video_files[@]}"; do
        echo "  - $(basename "$file")"
    done
    echo ""
    
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
