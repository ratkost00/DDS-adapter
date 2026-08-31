#!/bin/bash

###############################################################################
# Fast-DDS Topic Data Type Generation Script
#
# Generates and builds the Python bindings for the Adapter topic data type
# from src/library/Adapter.idl, per the Fast DDS Python getting-started guide:
# https://fast-dds.docs.eprosima.com/en/latest/fastdds/getting_started/simple_python_app/simple_python_app.html#build-the-topic-data-type
###############################################################################

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

FASTDDS_GEN_DIR="$HOME/Fast-DDS/src"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIBRARY_DIR="$SCRIPT_DIR/src/library"

log_section "Generating Adapter Library"

cd "$LIBRARY_DIR"

log_info "Running fastddsgen -python on Adapter.idl..."
"$FASTDDS_GEN_DIR/fastddsgen/scripts/fastddsgen" -python Adapter.idl

log_info "Configuring with CMake..."
cmake .

log_info "Building with make..."
make

log_section "Library Generation Complete!"