#!/bin/sh
#Script to build buildroot configuration
#Author: Siddhant Jajoo

#Author: Harinarayanan Gajapathy <haga9942@colorado.edu>
#Modified: Apr 16, 2023
#Comment: Base script https://github.com/cu-ecen-aeld/buildroot-assignments-base/blob/master/build.sh
#         modified for project need.

set -e
cd `dirname $0`

git submodule init
git submodule sync
git submodule update

if [ $# -ne 3 ]
then
    echo "Usage: ./build.sh [device] [ssid] [password]"
    echo "device: rpi3b or rpi4b"
    exit 1
fi

build_type=$1

# Create wpa_supplicant.conf
ssid=$2
psk=$3

psk_enc=$(wpa_passphrase $ssid $psk)

cat <<EOF > base_external/rootfs_overlay/etc/wpa_supplicant.conf
ctrl_interface=/var/run/wpa_supplicant
ap_scan=1

$psk_enc
EOF

if [ $build_type = "rpi3b" ]
then
    echo "Build Type: Raspberry Pi 3B+"
    #TODO: @Ritika will add the buildroot configuration file for RPi 3B+
    # buildroot_config=base_external/configs/raspberrypi3b/buildroot.config
elif [ $build_type = "rpi4b" ]
then
    echo "Build Type: Raspberry Pi 4B"
    buildroot_config=base_external/configs/raspberrypi4/buildroot.config
else
    echo "Invalid build type!"
    echo "Use either rpi3b or rpi4b as arguments."
    exit 1
fi

echo "Buildroot config: $buildroot_config"

if [ ! -e buildroot/.config ]
then
    echo "MISSING BUILDROOT CONFIGURATION FILE"
    cp $buildroot_config buildroot/.config
else
    echo "USING EXISTING BUILDROOT CONFIG"
fi

make -C buildroot
