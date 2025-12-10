#!/bin/bash

# setup_local_env.sh - Local Python environment setup script
# Purpose: Set up a local Python environment for service and utility tasks

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.12"
VENV_DIR=".venv"
UV_MIN_VERSION="0.1.0"

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
    print_success "Running in correct directory"
}

# Check if uv is installed
check_uv_installed() {
    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version | awk '{print $2}')
        print_success "uv is already installed (version: $UV_VERSION)"
        return 0
    else
        return 1
    fi
}

# Install uv
install_uv() {
    print_info "uv not found. Installing uv..."

    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_info "Detected Linux. Installing uv via curl..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_info "Detected macOS. Installing uv via curl..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    else
        print_error "Unsupported operating system: $OSTYPE"
        print_info "Please install uv manually from: https://github.com/astral-sh/uv"
        exit 1
    fi

    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"

    # Verify installation
    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version | awk '{print $2}')
        print_success "uv installed successfully (version: $UV_VERSION)"
    else
        print_error "uv installation failed. Please install manually."
        exit 1
    fi
}

# Check Python version
check_python_version() {
    print_info "Checking Python version..."

    if command -v python3 &> /dev/null; then
        PYTHON_CURRENT=$(python3 --version | awk '{print $2}')
        print_info "Found Python $PYTHON_CURRENT"

        # Check if Python 3.12+ is available
        if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null; then
            print_success "Python version meets requirements (>= 3.12)"
        else
            print_warning "Python 3.12+ is recommended but not found."
            print_info "Continuing with Python $PYTHON_CURRENT..."
        fi
    else
        print_error "Python 3 not found. Please install Python 3.12+."
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_info "Creating virtual environment in $VENV_DIR..."

    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment already exists at $VENV_DIR"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Removing existing virtual environment..."
            rm -rf "$VENV_DIR"
        else
            print_info "Using existing virtual environment"
            return 0
        fi
    fi

    uv venv "$VENV_DIR"
    print_success "Virtual environment created at $VENV_DIR"
}

# Install dependencies
install_dependencies() {
    print_info "Installing dependencies..."

    # Install all dependencies including dev extras
    uv sync --all-extras

    print_success "Dependencies installed successfully"
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."

    # Activate venv and check invoke
    source "$VENV_DIR/bin/activate"

    if command -v invoke &> /dev/null; then
        INVOKE_VERSION=$(invoke --version)
        print_success "invoke is available: $INVOKE_VERSION"
    else
        print_warning "invoke not found in PATH"
    fi

    # Check other key tools
    if command -v pytest &> /dev/null; then
        print_success "pytest is available"
    fi

    if command -v black &> /dev/null; then
        print_success "black is available"
    fi

    if command -v ruff &> /dev/null; then
        print_success "ruff is available"
    fi

    deactivate
}

# Main setup process
main() {
    echo ""
    print_info "=== Local Python Environment Setup ==="
    echo ""

    # Step 1: Check directory
    check_directory

    # Step 2: Check/install uv
    if ! check_uv_installed; then
        install_uv
    fi

    # Step 3: Check Python version
    check_python_version

    # Step 4: Create virtual environment
    create_venv

    # Step 5: Install dependencies
    install_dependencies

    # Step 6: Verify installation
    verify_installation

    # Success message
    echo ""
    print_success "=== Setup Complete ==="
    echo ""
    print_info "To activate the environment, run:"
    echo -e "  ${GREEN}source $VENV_DIR/bin/activate${NC}"
    echo ""
    print_info "Or use the helper script:"
    echo -e "  ${GREEN}source ./activate_env.sh${NC}"
    echo ""
    print_info "Available tasks (run 'invoke --list' after activation):"
    echo "  - invoke test      : Run tests"
    echo "  - invoke lint      : Run linting checks"
    echo "  - invoke format    : Format code"
    echo "  - invoke clean     : Clean cache files"
    echo ""
}

# Run main function
main
