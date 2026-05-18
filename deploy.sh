#!/bin/bash
# Deploy script for ai-brief-site
# Usage: bash deploy.sh
#
# This is a convenience wrapper around scripts/deploy.sh
# For full options, use: bash scripts/deploy.sh --help

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the main deploy script
exec bash "$SCRIPT_DIR/scripts/deploy.sh" "$@"