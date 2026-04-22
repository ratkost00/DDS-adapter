#!/bin/bash

###############################################################################
# Fast-DDS Python Environment Setup Script
# Configures LD_LIBRARY_PATH and PYTHONPATH for Fast-DDS Python bindings.
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

log_info "Configuring environment for Fast-DDS Python..."

export LD_LIBRARY_PATH=/usr/local/lib/${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
log_info "LD_LIBRARY_PATH set to: $LD_LIBRARY_PATH"

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_SITE_PACKAGES="/usr/local/lib/python${PYTHON_VERSION}/site-packages"
export PYTHONPATH=$PYTHON_SITE_PACKAGES:$PYTHONPATH
log_info "PYTHONPATH set to: $PYTHONPATH"

if [ -f ~/.bashrc ]; then
    if ! grep -q "export LD_LIBRARY_PATH=/usr/local/lib/" ~/.bashrc; then
        log_info "Adding LD_LIBRARY_PATH to ~/.bashrc..."
        echo 'export LD_LIBRARY_PATH=/usr/local/lib/${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}' >> ~/.bashrc
    else
        log_info "LD_LIBRARY_PATH already in ~/.bashrc"
    fi

    if ! grep -q "export PYTHONPATH=" ~/.bashrc; then
        log_info "Adding PYTHONPATH to ~/.bashrc..."
        echo "export PYTHONPATH=$PYTHON_SITE_PACKAGES:\$PYTHONPATH" >> ~/.bashrc
    else
        log_info "PYTHONPATH already in ~/.bashrc"
    fi
else
    log_warning "~/.bashrc not found — skipping persistence"
fi

log_info "Done. Run 'source ~/.bashrc' or open a new terminal to apply changes."
