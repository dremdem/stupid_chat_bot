#!/bin/bash

# cleanup_env.sh - Environment cleanup script
# Purpose: Clean up virtual environment and cache files

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR=".venv"

# Helper functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in backend directory
check_directory() {
    if [ ! -f "pyproject.toml" ]; then
        print_error "pyproject.toml not found. Please run this script from the backend directory."
        exit 1
    fi
}

# Remove virtual environment
remove_venv() {
    if [ -d "$VENV_DIR" ]; then
        print_info "Removing virtual environment at $VENV_DIR..."
        rm -rf "$VENV_DIR"
        print_success "Virtual environment removed"
    else
        print_warning "No virtual environment found at $VENV_DIR"
    fi
}

# Clean Python cache files
clean_python_cache() {
    print_info "Cleaning Python cache files..."

    # Remove __pycache__ directories
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

    # Remove .pyc files
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    # Remove .pyo files
    find . -type f -name "*.pyo" -delete 2>/dev/null || true

    # Remove .pytest_cache
    if [ -d ".pytest_cache" ]; then
        rm -rf ".pytest_cache"
    fi

    # Remove .ruff_cache
    if [ -d ".ruff_cache" ]; then
        rm -rf ".ruff_cache"
    fi

    # Remove .coverage files
    if [ -f ".coverage" ]; then
        rm -f ".coverage"
    fi

    if [ -d "htmlcov" ]; then
        rm -rf "htmlcov"
    fi

    print_success "Python cache files cleaned"
}

# Main cleanup process
main() {
    echo ""
    print_info "=== Environment Cleanup ==="
    echo ""

    # Step 1: Check directory
    check_directory

    # Step 2: Ask for confirmation
    print_warning "This will remove:"
    echo "  - Virtual environment ($VENV_DIR)"
    echo "  - Python cache files (__pycache__, .pyc, .pyo)"
    echo "  - Test cache (.pytest_cache)"
    echo "  - Linter cache (.ruff_cache)"
    echo "  - Coverage files (.coverage, htmlcov)"
    echo ""

    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleanup cancelled"
        exit 0
    fi

    # Step 3: Remove virtual environment
    remove_venv

    # Step 4: Clean Python cache
    clean_python_cache

    # Success message
    echo ""
    print_success "=== Cleanup Complete ==="
    echo ""
    print_info "To recreate the environment, run:"
    echo -e "  ${GREEN}./setup_local_env.sh${NC}"
    echo ""
}

# Run main function
main
