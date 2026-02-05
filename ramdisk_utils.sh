#!/bin/bash

# Ramdisk utility functions for multicam recording
# Provides functions to use tmpfs/ramdisk for recording when disk I/O is limited

# Default ramdisk mount point
DEFAULT_RAMDISK_PATH="/tmp/multicam_ramdisk"

# Check if ramdisk is enabled in config
# Args: $1 = script_dir
# Returns: 0 if enabled, 1 if disabled
is_ramdisk_enabled() {
    local script_dir="$1"
    local config_file="$script_dir/config.json"
    
    if [ ! -f "$config_file" ]; then
        return 1
    fi
    
    local enabled
    enabled=$(jq -r '.ramdisk.enabled // false' "$config_file" 2>/dev/null)
    
    if [ "$enabled" = "true" ]; then
        return 0
    else
        return 1
    fi
}

# Get ramdisk configuration
# Args: $1 = script_dir
# Sets: RAMDISK_PATH, RAMDISK_SIZE_GB
get_ramdisk_config() {
    local script_dir="$1"
    local config_file="$script_dir/config.json"
    
    RAMDISK_PATH=$(jq -r '.ramdisk.path // "/tmp/multicam_ramdisk"' "$config_file" 2>/dev/null)
    RAMDISK_SIZE_GB=$(jq -r '.ramdisk.size_gb // 4' "$config_file" 2>/dev/null)
}

# Check available RAM for ramdisk
# Args: $1 = required_gb
# Returns: 0 if sufficient RAM, 1 otherwise
check_available_ram() {
    local required_gb="$1"
    
    # Get available memory in GB (MemAvailable from /proc/meminfo)
    local available_kb
    available_kb=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
    
    # Convert to GB using awk for floating point
    local available_gb
    available_gb=$(awk "BEGIN {printf \"%.2f\", $available_kb / 1024 / 1024}")
    
    echo "Available RAM: ${available_gb} GB"
    echo "Required for ramdisk: ${required_gb} GB"
    
    # Compare using awk for floating point
    if awk "BEGIN {exit !($available_gb >= $required_gb)}"; then
        return 0
    else
        return 1
    fi
}

# Setup ramdisk for recording
# Args: $1 = script_dir
# Sets: RAMDISK_ACTIVE (0 or 1), RAMDISK_RECORDING_PATH
# Returns: 0 on success, 1 on failure (falls back to disk)
setup_ramdisk() {
    local script_dir="$1"
    
    RAMDISK_ACTIVE=0
    RAMDISK_RECORDING_PATH=""
    
    if ! is_ramdisk_enabled "$script_dir"; then
        echo "Ramdisk: disabled in config"
        return 1
    fi
    
    get_ramdisk_config "$script_dir"
    
    echo "Ramdisk: checking availability..."
    
    # Check if we have enough RAM
    if ! check_available_ram "$RAMDISK_SIZE_GB"; then
        echo "⚠️  Ramdisk: insufficient RAM, falling back to disk"
        return 1
    fi
    
    # Create ramdisk directory
    mkdir -p "$RAMDISK_PATH"
    
    # Check if already mounted as tmpfs
    if mountpoint -q "$RAMDISK_PATH" 2>/dev/null; then
        echo "Ramdisk: already mounted at $RAMDISK_PATH"
    else
        # Try to mount tmpfs (may require sudo)
        local size_mb=$((RAMDISK_SIZE_GB * 1024))
        if sudo mount -t tmpfs -o size=${size_mb}M tmpfs "$RAMDISK_PATH" 2>/dev/null; then
            echo "✅ Ramdisk: mounted ${RAMDISK_SIZE_GB}GB tmpfs at $RAMDISK_PATH"
        else
            # Fallback: use /dev/shm which is typically already a tmpfs
            if [ -d "/dev/shm" ]; then
                RAMDISK_PATH="/dev/shm/multicam_ramdisk"
                mkdir -p "$RAMDISK_PATH"
                echo "✅ Ramdisk: using /dev/shm at $RAMDISK_PATH"
            else
                echo "⚠️  Ramdisk: mount failed, falling back to disk"
                return 1
            fi
        fi
    fi
    
    RAMDISK_ACTIVE=1
    RAMDISK_RECORDING_PATH="$RAMDISK_PATH"
    echo "Ramdisk: ready for recording"
    return 0
}

# Get the recording path (ramdisk or disk)
# Args: $1 = original_output_dir, $2 = fin_name
# Returns: path to use for recording
get_recording_path() {
    local original_output_dir="$1"
    local fin_name="$2"
    
    if [ "$RAMDISK_ACTIVE" -eq 1 ] && [ -n "$RAMDISK_RECORDING_PATH" ]; then
        echo "$RAMDISK_RECORDING_PATH/$fin_name"
    else
        echo "$original_output_dir/$fin_name"
    fi
}

# Move recordings from ramdisk to final destination
# Args: $1 = ramdisk_path, $2 = final_path
# Returns: 0 on success, 1 on failure
move_from_ramdisk() {
    local ramdisk_path="$1"
    local final_path="$2"
    
    if [ "$RAMDISK_ACTIVE" -ne 1 ]; then
        return 0  # Nothing to move
    fi
    
    if [ ! -d "$ramdisk_path" ]; then
        echo "⚠️  Ramdisk: source path does not exist: $ramdisk_path"
        return 1
    fi
    
    echo "Moving recordings from ramdisk to disk..."
    echo "  From: $ramdisk_path"
    echo "  To: $final_path"
    
    # Create final directory
    mkdir -p "$final_path"
    
    # Move all files
    local file_count=0
    local total_size=0
    
    for file in "$ramdisk_path"/*; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            local filesize=$(stat -c%s "$file" 2>/dev/null || echo 0)
            total_size=$((total_size + filesize))
            
            echo "  Moving: $filename ($(numfmt --to=iec $filesize 2>/dev/null || echo "${filesize}B"))"
            
            if mv "$file" "$final_path/"; then
                file_count=$((file_count + 1))
            else
                echo "❌ Failed to move: $filename"
                return 1
            fi
        fi
    done
    
    echo "✅ Moved $file_count files ($(numfmt --to=iec $total_size 2>/dev/null || echo "${total_size}B")) to disk"
    
    # Clean up ramdisk directory
    rmdir "$ramdisk_path" 2>/dev/null
    
    return 0
}

# Cleanup ramdisk (unmount if we mounted it)
# Args: $1 = script_dir
cleanup_ramdisk() {
    local script_dir="$1"
    
    if [ "$RAMDISK_ACTIVE" -ne 1 ]; then
        return 0
    fi
    
    get_ramdisk_config "$script_dir"
    
    # Only unmount if we mounted it (not /dev/shm)
    if [ "$RAMDISK_PATH" != "/dev/shm/multicam_ramdisk" ]; then
        if mountpoint -q "$RAMDISK_PATH" 2>/dev/null; then
            echo "Ramdisk: unmounting $RAMDISK_PATH"
            sudo umount "$RAMDISK_PATH" 2>/dev/null
        fi
    fi
    
    RAMDISK_ACTIVE=0
}

# Get ramdisk status for display
# Args: $1 = script_dir
get_ramdisk_status() {
    local script_dir="$1"
    
    if ! is_ramdisk_enabled "$script_dir"; then
        echo "disabled"
        return
    fi
    
    get_ramdisk_config "$script_dir"
    
    if [ "$RAMDISK_ACTIVE" -eq 1 ]; then
        echo "active (${RAMDISK_SIZE_GB}GB at $RAMDISK_PATH)"
    else
        echo "enabled but not active"
    fi
}
