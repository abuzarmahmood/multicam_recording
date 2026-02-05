#!/bin/bash

# Test script for ramdisk_utils.sh functionality

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/ramdisk_utils.sh"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Test helper functions
pass() {
    echo "✅ PASS: $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
    echo "❌ FAIL: $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

# Create temporary test config
create_test_config() {
    local enabled="$1"
    local temp_dir="$2"
    
    cat > "$temp_dir/config.json" << EOF
{
  "disk_space": {
    "min_free_space_gb": 10
  },
  "ramdisk": {
    "enabled": $enabled,
    "path": "$temp_dir/test_ramdisk",
    "size_gb": 1
  }
}
EOF
}

# Test: is_ramdisk_enabled with enabled=true
test_is_ramdisk_enabled_true() {
    local temp_dir=$(mktemp -d)
    create_test_config "true" "$temp_dir"
    
    if is_ramdisk_enabled "$temp_dir"; then
        pass "is_ramdisk_enabled returns true when enabled"
    else
        fail "is_ramdisk_enabled should return true when enabled"
    fi
    
    rm -rf "$temp_dir"
}

# Test: is_ramdisk_enabled with enabled=false
test_is_ramdisk_enabled_false() {
    local temp_dir=$(mktemp -d)
    create_test_config "false" "$temp_dir"
    
    if ! is_ramdisk_enabled "$temp_dir"; then
        pass "is_ramdisk_enabled returns false when disabled"
    else
        fail "is_ramdisk_enabled should return false when disabled"
    fi
    
    rm -rf "$temp_dir"
}

# Test: is_ramdisk_enabled with missing config
test_is_ramdisk_enabled_no_config() {
    local temp_dir=$(mktemp -d)
    
    if ! is_ramdisk_enabled "$temp_dir"; then
        pass "is_ramdisk_enabled returns false when config missing"
    else
        fail "is_ramdisk_enabled should return false when config missing"
    fi
    
    rm -rf "$temp_dir"
}

# Test: get_ramdisk_config
test_get_ramdisk_config() {
    local temp_dir=$(mktemp -d)
    create_test_config "true" "$temp_dir"
    
    get_ramdisk_config "$temp_dir"
    
    if [ "$RAMDISK_PATH" = "$temp_dir/test_ramdisk" ]; then
        pass "get_ramdisk_config sets RAMDISK_PATH correctly"
    else
        fail "get_ramdisk_config RAMDISK_PATH incorrect: $RAMDISK_PATH"
    fi
    
    if [ "$RAMDISK_SIZE_GB" = "1" ]; then
        pass "get_ramdisk_config sets RAMDISK_SIZE_GB correctly"
    else
        fail "get_ramdisk_config RAMDISK_SIZE_GB incorrect: $RAMDISK_SIZE_GB"
    fi
    
    rm -rf "$temp_dir"
}

# Test: get_recording_path with ramdisk inactive
test_get_recording_path_disk() {
    RAMDISK_ACTIVE=0
    RAMDISK_RECORDING_PATH=""
    
    local result=$(get_recording_path "/output" "test_recording")
    
    if [ "$result" = "/output/test_recording" ]; then
        pass "get_recording_path returns disk path when ramdisk inactive"
    else
        fail "get_recording_path should return disk path: $result"
    fi
}

# Test: get_recording_path with ramdisk active
test_get_recording_path_ramdisk() {
    RAMDISK_ACTIVE=1
    RAMDISK_RECORDING_PATH="/tmp/ramdisk"
    
    local result=$(get_recording_path "/output" "test_recording")
    
    if [ "$result" = "/tmp/ramdisk/test_recording" ]; then
        pass "get_recording_path returns ramdisk path when active"
    else
        fail "get_recording_path should return ramdisk path: $result"
    fi
    
    # Reset
    RAMDISK_ACTIVE=0
    RAMDISK_RECORDING_PATH=""
}

# Test: move_from_ramdisk
test_move_from_ramdisk() {
    local temp_dir=$(mktemp -d)
    local ramdisk_path="$temp_dir/ramdisk"
    local final_path="$temp_dir/final"
    
    mkdir -p "$ramdisk_path"
    echo "test content" > "$ramdisk_path/test_file.txt"
    
    RAMDISK_ACTIVE=1
    
    if move_from_ramdisk "$ramdisk_path" "$final_path"; then
        if [ -f "$final_path/test_file.txt" ]; then
            pass "move_from_ramdisk moves files correctly"
        else
            fail "move_from_ramdisk file not found in destination"
        fi
        
        if [ ! -f "$ramdisk_path/test_file.txt" ]; then
            pass "move_from_ramdisk removes source files"
        else
            fail "move_from_ramdisk should remove source files"
        fi
    else
        fail "move_from_ramdisk returned error"
    fi
    
    RAMDISK_ACTIVE=0
    rm -rf "$temp_dir"
}

# Test: move_from_ramdisk when inactive
test_move_from_ramdisk_inactive() {
    RAMDISK_ACTIVE=0
    
    if move_from_ramdisk "/nonexistent" "/also_nonexistent"; then
        pass "move_from_ramdisk returns success when inactive"
    else
        fail "move_from_ramdisk should return success when inactive"
    fi
}

# Test: check_available_ram
test_check_available_ram() {
    # Test with very small requirement (should pass)
    if check_available_ram "0.001" > /dev/null 2>&1; then
        pass "check_available_ram passes with small requirement"
    else
        fail "check_available_ram should pass with small requirement"
    fi
    
    # Test with impossibly large requirement (should fail)
    if ! check_available_ram "999999" > /dev/null 2>&1; then
        pass "check_available_ram fails with large requirement"
    else
        fail "check_available_ram should fail with large requirement"
    fi
}

# Test: config.json has ramdisk section
test_config_has_ramdisk() {
    if [ -f "$SCRIPT_DIR/config.json" ]; then
        local has_ramdisk=$(jq 'has("ramdisk")' "$SCRIPT_DIR/config.json" 2>/dev/null)
        if [ "$has_ramdisk" = "true" ]; then
            pass "config.json has ramdisk section"
        else
            fail "config.json missing ramdisk section"
        fi
    else
        fail "config.json not found"
    fi
}

# Run all tests
echo "Running ramdisk_utils.sh tests..."
echo ""

test_is_ramdisk_enabled_true
test_is_ramdisk_enabled_false
test_is_ramdisk_enabled_no_config
test_get_ramdisk_config
test_get_recording_path_disk
test_get_recording_path_ramdisk
test_move_from_ramdisk
test_move_from_ramdisk_inactive
test_check_available_ram
test_config_has_ramdisk

echo ""
echo "================================"
echo "Tests passed: $TESTS_PASSED"
echo "Tests failed: $TESTS_FAILED"
echo "================================"

if [ $TESTS_FAILED -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed!"
    exit 1
fi
