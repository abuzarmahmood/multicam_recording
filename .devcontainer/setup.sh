#!/bin/bash

# .devcontainer/setup.sh - Setup script for multi-camera recording devcontainer

# Authenticate with GitHub CLI using token (if available)
if [ -n "$GITHUB_TOKEN" ]; then
    echo "$GITHUB_TOKEN" | gh auth login --with-token
    # Verify authentication
    gh auth status
fi