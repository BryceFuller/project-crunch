#!/usr/bin/env bash
#
# Written by John Sigmon and Bryce Fuller
# 
# This script does some of the heavy lifting for the install process,
# including installing the necessary system-wide dependencies and
# installing ROS if not installed. All of the necessary catkin work-
# space source code is installed here, although not all of the configuring
# is done inside this script

#####################################################################
# Parse args
#####################################################################

MYFILENAME="install.sh"
 
if [ $# -lt 4 ];
then
    echo "[ERROR: $MYFILENAME $LINENO] Incorrect number of arguments passed in."
    exit 1
fi

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -c|--catkin)
    CATKIN=$2
    shift
    shift
    ;;
    -p|--password)
    PASSWORD=$2
    shift
    shift
    ;;
    --is_base)
    IS_BASE=$2
    shift
    shift
    ;;
    --openhmdrules)
    OPENHMDRULES=$2
    shift
    shift
    ;;
    --viveconf)
    VIVECONF=$2
    shift
    shift
    ;;
esac
done

OPENCV_DEST="video_stream_opencv"
TXTSPHERE_DEST="rviz_textured_sphere"
OPENHMD_PLUGIN_DEST="rviz_openhmd"
OPENHMDRULES_DEST="/etc/udev/rules.d/"
VIVECONF_DEST="/usr/share/X11/xorg.conf.d/"
BUILD="build"
SRC="src"
OPENHMD_INSTALL_DEST="/usr/local/include/OpenHMD"

mkdir -p "$CATKIN"/"$BUILD"
mkdir -p "$CATKIN"/"$SRC"

#####################################################################
# Install dependencies
#####################################################################
echo "$PASSWORD" | sudo -S apt-get update && sudo apt-get -y install\
                        build-essential=12.1ubuntu2\
                        cmake=3.5.1-1ubuntu3\
                        git\
                        libgtest-dev=1.7.0-4ubuntu1\
                        openssh-server\
            			sshpass\
                        v4l-utils=1.10.0-1 2>&1

#####################################################################
# Install ros-kinetic
#####################################################################
sudo apt-get update

if ! dpkg -s ros-kinetic-desktop-full > /dev/null
then
    # Replaced $(lsb_release -sc) with xenial 
    # shellcheck disable=SC2016
    sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu xenial main" > /etc/apt/sources.list.d/ros-latest.list'
    sudo apt-key adv \
        --keyserver hkp://ha.pool.sks-keyservers.net:80 \
        --recv-key 421C365BD9FF1F717815A3895523BAEEB01FA116
    sudo apt-get update && sudo apt-get -y install ros-kinetic-desktop-full
    sudo rosdep init
    rosdep update
    echo "source /opt/ros/kinetic/setup.bash" >> ~/.bashrc
    # shellcheck disable=SC1090
    source ~/.bashrc
    echo "[INFO: $MYFILENAME $LINENO] Installed ros-kinetic-desktop-full."
fi
    echo "[INFO: $MYFILENAME $LINENO] ros-kinetic-desktop-full already installed."

#####################################################################
# Install OpenCV Video streaming package
#####################################################################
#TODO possibly checkout specific version of repo
if [ ! -d "$CATKIN"/"$SRC"/"$OPENCV_DEST" ];
then
    echo "[INFO: $MYFILENAME $LINENO] Installing video_stream_opencv into $CATKIN/$SRC/$OPENCV_DEST"
    git clone https://github.com/ros-drivers/video_stream_opencv.git "$CATKIN"/"$SRC"/"$OPENCV_DEST"/ &&
    echo "[INFO: $MYFILENAME $LINENO] Installed video_stream_opencv into $CATKIN/$SRC/$OPENCV_DEST"
fi

#####################################################################
# Install rviz textured sphere
#####################################################################
if [ ! -d "$CATKIN"/"$SRC"/"$TXTSPHERE_DEST" ];
then
	echo "[INFO: $MYFILENAME $LINENO] Cloning $TXTSPHERE_DEST into $CATKIN/$SRC."
    git clone https://github.com/UTNuclearRoboticsPublic/rviz_textured_sphere.git "$CATKIN"/"$SRC"/"$TXTSPHERE_DEST" &&
	echo "[INFO: $MYFILENAME $LINENO] $TXTSPHERE_DEST cloned to $CATKIN/$SRC/$TXTSPHERE_DEST"
else
    echo "[INFO: $MYFILENAME $LINENO] $TXTSPHERE_DEST is already cloned, skipping installation."
fi

#####################################################################
# Install OpenHMD plugin
#####################################################################
echo "$PASSWORD" | sudo -S apt-get update && sudo apt-get -y install\
                        libglu1-mesa-dev \
                        mesa-common-dev \
                        libogre-1.9-dev \
                        libudev-dev \
                        libusb-1.0-0-dev \
                        libfox-1.6-dev \
                        autotools-dev \
                        autoconf \
                        automake \
                        libtool \
                        libsdl2-dev \
                        libxmu-dev \
                        libxi-dev \
                        libgl-dev \
                        libglew1.5-dev \
                        libglew-dev \
                        libglewmx1.5-dev \
                        libglewmx-dev \
                        libhidapi-dev \
                        freeglut3-dev

# Install OpenHMD Lib in /usr/local/include if on robot, and put plugin 
# in catkin workspace.
if [ "$IS_BASE" == "y" ];
then
    if [ ! -d "$OPENHMD_INSTALL_DEST" ];
    then
        echo "[INFO: $MYFILENAME $LINENO] Cloning OpenHMD Lib into $OPENHMD_INSTALL."
        sudo git clone https://github.com/OpenHMD/OpenHMD.git "$OPENHMD_INSTALL_DEST" 
        cd "$OPENHMD_INSTALL_DEST" || exit 1
        sudo git checkout 4ca169b49ab4ea4bee2a8ea519d9ba8dcf662bd5
        sudo cmake .
        sudo make
        sudo ./autogen.sh
        sudo ./configure
        sudo make
        cd - || exit 1
    else
        echo "[INFO: $MYFILENAME $LINENO] OpenHMD Lib is already cloned, skipping installation."
    fi

    # Install the OpenHMD plugin
    if [ ! -d "$CATKIN"/"$SRC"/"$OPENHMD_PLUGIN_DEST" ];
    then
        echo "[INFO: $MYFILENAME $LINENO] Cloning $OPENHMD_PLUGIN_DEST into $CATKIN/$SRC."
        git clone https://github.com/UTNuclearRoboticsPublic/rviz_openhmd.git "$CATKIN"/"$SRC"/"$OPENHMD_PLUGIN_DEST" &&
        echo "[INFO: $MYFILENAME $LINENO] $OPENHMD_PLUGIN_DEST cloned to $CATKIN/$SRC/$OPENHMD_PLUGIN_DEST"
    else
        echo "[INFO: $MYFILENAME $LINENO] $OPENHMD_PLUGIN_DEST is already cloned, skipping installation."
    fi
fi
#####################################################################
# Vive and OpenHMD configuration
#####################################################################
# NVIDIA drivers
# Add apt-repo updates list of available drivers (which requires the user to hit enter)
# Checks for recommended drivers and installs them
echo | sudo add-apt-repository ppa:graphics-drivers/ppa
sudo apt update
DRIVER=$(sudo ubuntu-drivers devices | grep "recommended" | awk '{print $3}')
if dpkg -s "$DRIVER" &> /dev/null
then
    echo "[INFO: $MYFILENAME $LINENO] The recommended graphics drivers ($DRIVER) are already installed." 
else
    sudo apt-get -y install "$DRIVER" &&
    echo "[INFO: $MYFILENAME $LINENO] $DRIVER installed."
fi

# Copy over rules files for using a HMD in Linux.
# This is required for Linux to allow access to a HMD.
# For more info: https://github.com/OpenHMD/OpenHMD/wiki/Udev-rules-list
if ! sudo cp "$OPENHMDRULES" "$OPENHMDRULES_DEST"
then
echo "[ERROR: $MYFILENAME $LINENO] Copy $OPENHMDRULES to $OPENHMDRULES_DEST failed"
    exit 1
fi

# Updates rules in OS for USB port access by OpenHMD plugin that come from the
# modified openHMD rules file above.
sudo udevadm control --reload-rules

# This config file tells the GPU to allow a HMD to be treated like a regular monitor.
# Without this, your GPU may block access to the HMD and make it appear as though
# it does not work.
# For more info: http://doc-ok.org/?p=1763
if ! sudo cp "$VIVECONF" "$VIVECONF_DEST"
then
    echo "[ERROR: $MYFILENAME $LINENO] Copy $VIVECONF to $VIVECONF_DEST failed"
    exit 1
fi

# Point plugin source file to location of "resources" file.
# The plugin has a hard coded absolute path to point to the resources configuration file.
# Changing this is requried so the plugin will find the resources directory
LINETOEDIT=73
FILETOEDIT="$CATKIN"/"$SRC"/"$OPENHMD_PLUGIN_DEST"/"$SRC"/openhmd_display.cpp
LINEBEFORE=$(head -"$LINETOEDIT" "$FILETOEDIT" | tail -1)
sed -i "${LINETOEDIT}s|.*|    mResourcesCfg = \"${CATKIN}/src/rviz_openhmd/src/resources.cfg\";|" "$FILETOEDIT"
LINEAFTER=$(head -"$LINETOEDIT" "$FILETOEDIT" | tail -1)
echo "[INFO: $MYFILENAME $LINENO] $FILETOEDIT Line $LINETOEDIT changed from $LINEBEFORE to $LINEAFTER"

# Point resource file to openHMD resources directory.
# This config file points to the location of the compositor resources used in the plugin.
# It uses a hard coded absolute path to find the directory, so this needs to be set for each computer.
LINETOEDIT=3
FILETOEDIT="$CATKIN"/"$SRC"/"$OPENHMD_PLUGIN_DEST"/"$SRC"/resources.cfg
LINEBEFORE=$(head -"$LINETOEDIT" "$FILETOEDIT" | tail -1)
sed -i "${LINETOEDIT}s|.*|FileSystem=${CATKIN}/src/rviz_openhmd/src/resources/|" "$FILETOEDIT"
LINEAFTER=$(head -"$LINETOEDIT" "$FILETOEDIT" | tail -1)
echo "[INFO: $MYFILENAME $LINENO] $FILETOEDIT Line $LINETOEDIT changed from $LINEBEFORE to $LINEAFTER"

# Change permissions on USB ports to all users.
# There is a potential security vulnerability opened by changing these permissions.
# It is required that the plugin have raw access to the USB port as only the plugin using OpenHMD,
# and not the OS (who usually intercepts data), knows how to handle the incomming information.
sudo chmod a+rw /dev/hidraw*

# Export OpenHMD library and header location for CMakeLists in Catkin
echo "export OPENHMD_INSTALL_DEST=$OPENHMD_INSTALL_DEST" >> ~/.bashrc

# Update port rules to allow for ssh configuration
sudo ufw allow 22
