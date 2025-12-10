#!/bin/bash

# activate_env.sh - Environment activation helper script
# Purpose: Simplified activation of the local Python virtual environment

# This script should be sourced, not executed
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    echo "Error: This script should be sourced, not executed directly."
    echo "Usage: source ./activate_env.sh"
    exit 1
fi

# Configuration
VENV_DIR=".venv"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}[ERROR]${NC} Virtual environment not found at $VENV_DIR"
    echo -e "${YELLOW}[INFO]${NC} Run './setup_local_env.sh' first to create the environment"
    return 1
fi

# Check if activation script exists
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo -e "${RED}[ERROR]${NC} Activation script not found at $VENV_DIR/bin/activate"
    echo -e "${YELLOW}[INFO]${NC} The virtual environment may be corrupted. Try running './setup_local_env.sh' again"
    return 1
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Verify activation
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${GREEN}[SUCCESS]${NC} Virtual environment activated: $VIRTUAL_ENV"
    echo ""
    echo "Available invoke tasks:"
    echo "  invoke --list      : Show all available tasks"
    echo "  invoke test        : Run tests"
    echo "  invoke lint        : Run linting checks"
    echo "  invoke format      : Format code"
    echo "  invoke clean       : Clean cache files"
    echo ""
    echo "To deactivate, run: deactivate"
else
    echo -e "${RED}[ERROR]${NC} Failed to activate virtual environment"
    return 1
fi
