#!/bin/sh
#Script to build buildroot configuration
#Author: Siddhant Jajoo

#Author: Harinarayanan Gajapathy <haga9942@colorado.edu>
#Modified: Apr 16, 2023
#Comment: Base script https://github.com/cu-ecen-aeld/buildroot-assignments-base/blob/master/build.sh
#         modified for project need.

EXTERNAL_REL_BUILDROOT=base_external

if [ ! -e buildroot/.config ]
then
    echo "MISSING BUILDROOT CONFIGURATION FILE"
    cp ${EXTERNAL_REL_BUILDROOT}/configs/raspberrypi4/rpi-4b-custom.config buildroot/.config
    make -C buildroot BR2_EXTERNAL=../${EXTERNAL_REL_BUILDROOT}
else
    echo "USING EXISTING BUILDROOT CONFIG"
    make -C buildroot BR2_EXTERNAL=../${EXTERNAL_REL_BUILDROOT}
fi
