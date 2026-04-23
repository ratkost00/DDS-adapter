#!/bin/bash

###############################################################################
# Fast-DDS Complete Installation Script
# Based on: https://github.com/ratkost00/DDS-adapter
# 
# This script automates the installation of eprosima Fast DDS and all
# prerequisites including Python bindings and Fast DDS Gen tool.
###############################################################################

set -e  # Exit on any error

# Prevent interactive prompts during package installation
export DEBIAN_FRONTEND=noninteractive
export TZ=Europe/Belgrade

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
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

# Proxy configuration - only use proxy if already set in environment
PROXY_URL="${http_proxy:-${HTTP_PROXY:-}}"
if [ -n "$PROXY_URL" ]; then
    log_info "Using proxy from environment: $PROXY_URL"
else
    log_info "No proxy set - connecting directly"
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    log_error "Please do not run this script as root (use sudo when prompted)"
    exit 1
fi

# Working directory
WORK_DIR="$HOME/Fast-DDS-python"
FASTDDS_GEN_DIR="$HOME/Fast-DDS/src"

###############################################################################
# 1. PREREQUISITES - INSTALL REQUIRED TOOLS
###############################################################################
log_section "1. Installing Required Tools"

log_info "Updating package lists..."
sudo apt update

log_info "Installing required tools (cmake, g++, python3-pip, wget, git, swig)..."
sudo apt install -y cmake g++ python3-pip wget git swig

# Check Ubuntu version and install swig4.1 if needed
log_info "Checking Ubuntu version for SWIG compatibility..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [ "$ID" = "ubuntu" ] && [ "$VERSION_ID" = "24.04" ]; then
        log_info "Ubuntu 24.04 detected - installing swig4.1 for Fast-DDS Python compatibility..."
        sudo apt install -y swig4.1
        SWIG_EXECUTABLE="/usr/bin/swig4.1"
    else
        log_info "Ubuntu $VERSION_ID detected - using default SWIG"
        SWIG_EXECUTABLE=""
    fi
else
    log_warning "Cannot detect OS version - using default SWIG"
    SWIG_EXECUTABLE=""
fi

log_info "Checking CMake version..."
CMAKE_VERSION=$(cmake --version | head -n1 | cut -d' ' -f3)
log_info "CMake version: $CMAKE_VERSION"

git config --global http.postBuffer 524288000
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999

if [ -n "$PROXY_URL" ]; then
    log_info "Configuring Git to use proxy: $PROXY_URL"
    git config --global http.proxy "$PROXY_URL"
    git config --global https.proxy "$PROXY_URL"

    log_info "Testing proxy connectivity..."
    if ! curl -x "$PROXY_URL" --connect-timeout 10 -s https://github.com > /dev/null 2>&1; then
        log_warning "Proxy connectivity test failed. SSL verification will be disabled for git clones in this session only."
        log_warning "This does NOT modify your global git config."
        export GIT_SSL_NO_VERIFY=1
    fi
else
    log_info "Clearing any previously set git proxy settings..."
    git config --global --unset http.proxy  2>/dev/null || true
    git config --global --unset https.proxy 2>/dev/null || true
fi

###############################################################################
# 2. INSTALL REQUIRED PACKAGES
###############################################################################
log_section "2. Installing Required Packages"

PACKAGES=(
    "libasio-dev"
    "libtinyxml2-dev"
    "libssl-dev"
    "libp11-dev"
    "softhsm2"
    "libengine-pkcs11-openssl"
    "libpython3-dev"
)

for package in "${PACKAGES[@]}"; do
    log_info "Installing $package..."
    sudo apt install -y "$package"
done

###############################################################################
# 3. PREPARE WORKING DIRECTORY
###############################################################################
log_section "3. Preparing Working Directory"

log_info "Creating working directory: $WORK_DIR"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR" || { log_error "Failed to enter working directory: $WORK_DIR"; exit 1; }

###############################################################################
# 4. INSTALL FOONATHAN MEMORY
###############################################################################
log_section "4. Installing Foonathan Memory"

log_info "Cloning foonathan_memory_vendor repository..."
if [ -d "foonathan_memory_vendor" ]; then
    log_warning "foonathan_memory_vendor directory exists and will be removed: $WORK_DIR/foonathan_memory_vendor"
    sudo rm -rf foonathan_memory_vendor
fi
git clone https://github.com/eProsima/foonathan_memory_vendor.git

log_info "Building foonathan_memory_vendor..."
mkdir -p foonathan_memory_vendor/build
cd foonathan_memory_vendor/build || { log_error "Failed to enter foonathan_memory_vendor/build"; exit 1; }
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local/ -DBUILD_SHARED_LIBS=ON
# Use sudo -E to preserve proxy environment variables
sudo -E cmake --build . --target install -- -j$(nproc)
log_info "Foonathan Memory installed successfully"

###############################################################################
# 5. INSTALL FAST-CDR
###############################################################################
log_section "5. Installing Fast-CDR"

cd "$WORK_DIR" || { log_error "Failed to enter working directory: $WORK_DIR"; exit 1; }
log_info "Cloning Fast-CDR repository..."
if [ -d "Fast-CDR" ]; then
    log_warning "Fast-CDR directory exists and will be removed: $WORK_DIR/Fast-CDR"
    sudo rm -rf Fast-CDR
fi
git clone https://github.com/eProsima/Fast-CDR.git

log_info "Building Fast-CDR..."
mkdir -p Fast-CDR/build
cd Fast-CDR/build || { log_error "Failed to enter Fast-CDR/build"; exit 1; }
cmake ..
sudo -E cmake --build . --target install -- -j$(nproc)
log_info "Fast-CDR installed successfully"

###############################################################################
# 6. INSTALL FAST-DDS
###############################################################################
log_section "6. Installing Fast-DDS"

cd "$WORK_DIR" || { log_error "Failed to enter working directory: $WORK_DIR"; exit 1; }
log_info "Cloning Fast-DDS repository..."
if [ -d "Fast-DDS" ]; then
    log_warning "Fast-DDS directory exists and will be removed: $WORK_DIR/Fast-DDS"
    sudo rm -rf Fast-DDS
fi
git clone https://github.com/eProsima/Fast-DDS.git

log_info "Building Fast-DDS..."
mkdir -p Fast-DDS/build
cd Fast-DDS/build || { log_error "Failed to enter Fast-DDS/build"; exit 1; }
cmake ..
sudo -E cmake --build . --target install -- -j$(nproc)
log_info "Fast-DDS installed successfully"

###############################################################################
# 7. INSTALL FAST-DDS PYTHON BINDINGS
###############################################################################
log_section "7. Installing Fast-DDS Python Bindings"

cd "$WORK_DIR" || { log_error "Failed to enter working directory: $WORK_DIR"; exit 1; }
log_info "Cloning Fast-DDS-python repository..."
if [ -d "Fast-DDS-python" ]; then
    log_warning "Fast-DDS-python directory exists and will be removed: $WORK_DIR/Fast-DDS-python"
    sudo rm -rf Fast-DDS-python
fi
git clone https://github.com/eProsima/Fast-DDS-python.git

log_info "Building Fast-DDS Python bindings..."
mkdir -p Fast-DDS-python/fastdds_python/build
cd Fast-DDS-python/fastdds_python/build || { log_error "Failed to enter Fast-DDS-python/fastdds_python/build"; exit 1; }
if [ -n "$SWIG_EXECUTABLE" ]; then
    log_info "Using SWIG 4.1 for Python bindings..."
    cmake .. -DSWIG_EXECUTABLE="$SWIG_EXECUTABLE"
else
    cmake ..
fi
sudo -E cmake --build . --target install -- -j$(nproc)
log_info "Fast-DDS Python bindings installed successfully"

###############################################################################
# 8. INSTALL FAST-DDS GEN
###############################################################################
log_section "8. Installing Fast-DDS Gen"

log_info "Checking for Java (required for Gradle)..."
if ! command -v java &> /dev/null; then
    log_warning "Java not found. Installing default-jdk..."
    sudo apt install -y default-jdk
else
    JAVA_VERSION=$(java -version 2>&1 | head -n1)
    log_info "Java found: $JAVA_VERSION"
fi

log_info "Creating Fast-DDS Gen directory: $FASTDDS_GEN_DIR"
mkdir -p "$FASTDDS_GEN_DIR"
cd "$FASTDDS_GEN_DIR" || { log_error "Failed to enter Fast-DDS Gen directory: $FASTDDS_GEN_DIR"; exit 1; }

log_info "Cloning Fast-DDS-Gen repository..."
if [ -d "fastddsgen" ]; then
    log_warning "fastddsgen directory exists and will be removed: $FASTDDS_GEN_DIR/fastddsgen"
    sudo rm -rf fastddsgen
fi
git clone --recursive https://github.com/eProsima/Fast-DDS-Gen.git fastddsgen

log_info "Building Fast-DDS Gen with Gradle..."
cd fastddsgen || { log_error "Failed to enter fastddsgen directory"; exit 1; }

mkdir -p ~/.gradle
if [ -n "$PROXY_URL" ]; then
    PROXY_HOST=$(echo "$PROXY_URL" | sed 's|https\?://||' | cut -d: -f1)
    PROXY_PORT=$(echo "$PROXY_URL" | sed 's|https\?://||' | cut -d: -f2)
    log_info "Configuring Gradle proxy settings ($PROXY_HOST:$PROXY_PORT)..."
    cat > ~/.gradle/gradle.properties << EOF
systemProp.http.proxyHost=$PROXY_HOST
systemProp.http.proxyPort=$PROXY_PORT
systemProp.https.proxyHost=$PROXY_HOST
systemProp.https.proxyPort=$PROXY_PORT
EOF
else
    log_info "No proxy set - clearing Gradle proxy settings..."
    sed -i '/systemProp\.\(http\|https\)\.proxy/d' ~/.gradle/gradle.properties 2>/dev/null || true
fi

./gradlew assemble
log_info "Fast-DDS Gen built successfully"

###############################################################################
# 9. UPDATE LIBRARY CACHE
###############################################################################
log_section "9. Updating Library Cache"

log_info "Running ldconfig to update shared library cache..."
sudo ldconfig

###############################################################################
# 10. CONFIGURE ENVIRONMENT FOR FAST-DDS PYTHON
###############################################################################
log_section "10. Configuring Environment for Fast-DDS Python"

log_info "Adding /usr/local/lib/ to LD_LIBRARY_PATH..."
export LD_LIBRARY_PATH=/usr/local/lib/${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}

# Detect Python version and add site-packages to PYTHONPATH
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_SITE_PACKAGES="/usr/local/lib/python${PYTHON_VERSION}/site-packages"

log_info "Adding $PYTHON_SITE_PACKAGES to PYTHONPATH..."
export PYTHONPATH=$PYTHON_SITE_PACKAGES:$PYTHONPATH

# Add to bashrc for persistence
if [ -f ~/.bashrc ]; then
    if ! grep -q "export LD_LIBRARY_PATH=/usr/local/lib/" ~/.bashrc; then
        log_info "Adding LD_LIBRARY_PATH to ~/.bashrc for future sessions..."
        echo 'export LD_LIBRARY_PATH=/usr/local/lib/${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}' >> ~/.bashrc
    else
        log_info "LD_LIBRARY_PATH already configured in ~/.bashrc"
    fi
    
    if ! grep -q "export PYTHONPATH=" ~/.bashrc; then
        log_info "Adding PYTHONPATH to ~/.bashrc for future sessions..."
        echo "export PYTHONPATH=$PYTHON_SITE_PACKAGES:\$PYTHONPATH" >> ~/.bashrc
    else
        log_info "PYTHONPATH already configured in ~/.bashrc"
    fi
fi

###############################################################################
# INSTALLATION COMPLETE
###############################################################################
log_section "Installation Complete!"

echo ""
log_info "Fast-DDS and all components have been successfully installed:"
echo "  ✓ Foonathan Memory"
echo "  ✓ Fast-CDR"
echo "  ✓ Fast-DDS"
echo "  ✓ Fast-DDS Python bindings"
echo "  ✓ Fast-DDS Gen"
echo "  ✓ LD_LIBRARY_PATH configured"
echo ""
log_info "Installation directories:"
echo "  - Fast-DDS libraries: $WORK_DIR"
echo "  - Fast-DDS Gen: $FASTDDS_GEN_DIR/fastddsgen"
echo ""
log_info "Environment configuration:"
echo "  - LD_LIBRARY_PATH has been set to /usr/local/lib/"
echo "  - PYTHONPATH has been set to include Python site-packages"
echo "  - Both have been added to ~/.bashrc for future sessions"
echo ""
log_info "To use Fast-DDS Gen, you may want to add it to your PATH:"
echo "  export PATH=\$PATH:$FASTDDS_GEN_DIR/fastddsgen/scripts"
echo ""
log_info "IMPORTANT: To apply environment changes in your current shell, run:"
echo "  source ~/.bashrc"
echo ""
log_info "Or simply start a new terminal session."