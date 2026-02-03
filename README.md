# DDS-adapter
DDS adapter is wrapper for eprosima Fast DDS implementation, which is replacement for TCP/UDP communication API used in message passing API.

## 1. Prerequisites
For utilization of eprosima Fast DDS implementation, Fast DDS library must be installed. In order to use Python for application level development  Fast DDS Python bindings must be installed. For generation of API Fast DDS Gen tool is used.
Guide provides multiple ways to install all necessary libraries, for this solution installation from sources is chosen, which is provided on this [link](https://fast-dds.docs.eprosima.com/en/latest/installation/sources/sources_linux.html#).
Exact steps used to install all necessary libraries and prerequisites are executed as described bellow.

### 1.1 Required tools
Tools used for this installation:
- CMake (must be 3.28 or higher)
- g++ compiler (included as part of GNU toolchain packages)
- pip3
- wget
- git
- swig (swig4.1 in case Ubuntu 24.04 is used)
- openjdk-18-jdk

Following command may be used to install all missing tools:
~~~~bash
sudo apt install cmake g++ python3-pip wget git
sudo apt install swig
~~~~

### 1.2 Required packages
In order to start installation process following packages must be installed:
- libasio-dev
- libtinyxml2-dev
- libssl-dev
- libp11-dev
- softhsm2
- libengine-pkcs11-openssl
- libpython3-dev

Following command may be used to install missing packages:
~~~~bash
sudo apt install $package_name
~~~~

## 2. Installation
For this project CMake installation is used and all necessary libraries are installed system-wide (additional CMake flags will enable local installation).

Source code may be cloned inside temporary directory on file system.
~~~~bash
mkdir ~/Fast-DDS-python
cd Fast-DDS-python/
~~~~

### 2.1 Foonathan memory
Set of command for compilation and installation for memory allocator:
~~~~bash
cd ~/Fast-DDS-python/
git clone https://github.com/eProsima/foonathan_memory_vendor.git
mkdir foonathan_memory_vendor/build
cd foonathan_memory_vendor/build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local/ -DBUILD_SHARED_LIBS=ON
cmake --build . --target install
~~~~

### 2.2 Fast-CDR
Set of command for compilation and installation:
~~~~bash
cd ~/Fast-DDS-python/
git clone https://github.com/eProsima/Fast-CDR.git
mkdir Fast-CDR/build
cd Fast-CDR/build
cmake ..
cmake --build . --target install
~~~~

### 2.3 Fast-DDS
Set of command for compilation and installation:
~~~~bash
cd ~/Fast-DDS-python/
git clone https://github.com/eProsima/Fast-DDS.git
mkdir Fast-DDS/build
cd Fast-DDS/build
cmake ..
cmake --build . --target install
~~~~

### 2.3 Fast-DDS Python bindings
Set of command for compilation and installation:
~~~~bash
cd ~/Fast-DDS-python/
git clone https://github.com/eProsima/Fast-DDS-python.git
mkdir -p Fast-DDS-python/fastdds_python/build
cd Fast-DDS-python/fastdds_python/build
cmake ..
cmake --build . --target install
~~~~

### 2.4 Fast-DDS Gen installation
Fast DDS Gen is generation tool used to generate source code from data types defined in IDL file. For compilation of Fast DDS Gen build automation tool Gradle is used which requires java version above 11. Compilation can be executed by following steps bellow:
~~~~bash
mkdir -p ~/Fast-DDS/src
cd ~/Fast-DDS/src
git clone --recursive https://github.com/eProsima/Fast-DDS-Gen.git fastddsgen
cd fastddsgen
./gradlew assemble
~~~~
