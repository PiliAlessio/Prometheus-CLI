#!/bin/bash
#
# One-command Prometheus CLI installation script for Linux/macOS
#
# Automatically handles:
# - Python environment setup (checks/creates venv)
# - Dependency installation
# - Prometheus CLI setup in editable mode
# - Verification that everything works
#
# Usage:
#   ./install.sh                    # Install with default .venv
#   ./install.sh --venv my-env      # Install with custom venv
#   ./install.sh --python python3.10 # Install with specific Python version
#

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Defaults
VENV_PATH=".venv"
PYTHON="python"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --venv)
            VENV_PATH="$2"
            shift 2
            ;;
        --python)
            PYTHON="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# Functions
write_success() {
    echo -e "${GREEN}✓${NC} $*"
}

write_error() {
    echo -e "${RED}✗${NC} $*" >&2
    exit 1
}

write_info() {
    echo -e "${YELLOW}→${NC} $*"
}

# 1. Check repository structure
write_info "Verifying Prometheus-CLI repository structure..."
for path in "tools/cli" ".git"; do
    if [ ! -d "$path" ]; then
        write_error "Missing $path - run this script from Prometheus-CLI root directory"
    fi
done
write_success "Repository structure verified"

# 2. Check Python installation
write_info "Checking Python installation..."
if ! $PYTHON --version > /dev/null 2>&1; then
    write_error "Python not found. Install Python 3.9+ or specify with --python parameter"
fi
PYTHON_VERSION=$($PYTHON --version 2>&1)
write_success "Found $PYTHON_VERSION"

# 3. Create virtual environment if needed
if [ ! -d "$VENV_PATH" ]; then
    write_info "Creating virtual environment at $VENV_PATH..."
    $PYTHON -m venv "$VENV_PATH"
    write_success "Virtual environment created"
else
    write_success "Virtual environment already exists at $VENV_PATH"
fi

# 4. Activate virtual environment
write_info "Activating virtual environment..."
source "$VENV_PATH/bin/activate"
write_success "Virtual environment activated"

# 5. Upgrade pip
write_info "Upgrading pip..."
python -m pip install --upgrade pip --quiet
write_success "pip upgraded"

# 6. Install development dependencies
write_info "Installing Prometheus CLI..."
cd tools/cli
pip install -e ".[dev]" --quiet
cd ../..
write_success "Prometheus CLI installed with dev dependencies"

# 7. Verify installation
write_info "Verifying installation..."
if ! prometheus version > /dev/null 2>&1; then
    write_error "Prometheus CLI verification failed"
fi
write_success "Installation verified"

echo ""
write_success "Prometheus CLI installation complete!"
echo ""
echo "Next steps:"
echo "  1. ${YELLOW}Activate the environment:${NC} source $VENV_PATH/bin/activate"
echo "  2. ${YELLOW}Verify commands:${NC} prometheus help"
echo "  3. ${YELLOW}Start using:${NC} prometheus init"
echo ""
echo "To update in the future, just run: ${GREEN}./install.sh${NC}"
