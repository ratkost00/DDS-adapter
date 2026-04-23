#!/bin/bash

###############################################################################
# Fast-DDS Library Generation Script
# Finds all .idl files in src/library/, generates C++ and Python bindings
# for each using Fast-DDS Gen, then builds with CMake.
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/src/library"
FASTDDSGEN="$HOME/Fast-DDS/src/fastddsgen/scripts/fastddsgen"

if [ ! -f "$FASTDDSGEN" ]; then
    log_error "fastddsgen not found at: $FASTDDSGEN"
    exit 1
fi

if [ ! -d "$LIB_DIR" ]; then
    log_error "Library source directory not found: $LIB_DIR"
    exit 1
fi

cd "$LIB_DIR" || { log_error "Failed to enter: $LIB_DIR"; exit 1; }

mapfile -t IDL_FILES < <(find . -maxdepth 1 -name "*.idl" -type f | sort)

if [ ${#IDL_FILES[@]} -eq 0 ]; then
    log_error "No .idl files found in: $LIB_DIR"
    exit 1
fi

log_info "Found ${#IDL_FILES[@]} .idl file(s): ${IDL_FILES[*]}"

for idl in "${IDL_FILES[@]}"; do
    log_info "Running fastddsgen on $idl..."
    "$FASTDDSGEN" -python "$idl"
done

log_info "Running cmake..."
cmake .

log_info "Building library..."
make -j$(nproc)

log_info "Library generated successfully in: $LIB_DIR"
