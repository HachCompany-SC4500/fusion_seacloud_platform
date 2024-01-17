#!/bin/bash

if [ $# -ne 1 ]
then
	echo "Usage: $0 <download mirror location>"
	exit 1
fi

# From .repo/manifests, go back to base folder fusion_seacloud_platform
pushd ../.. > /dev/null

# Export environment variables
SOURCE_OUTPUT=${PWD}/source_output
source ./export &> ${SOURCE_OUTPUT} || cat ${SOURCE_OUTPUT}
rm ${SOURCE_OUTPUT}; unset SOURCE_OUTPUT

RELATIVE_MIRROR_PATH=$(grep '^SOURCE_MIRROR_URL' conf/local.conf | sed -n 's#SOURCE_MIRROR_URL.*${TOPDIR}/##p'| sed -n 's#"##p')
echo "Mirror download path: ${RELATIVE_MIRROR_PATH}"

# Move yocto package download folder
NEW_MIRROR_PATH=$1
echo "Create symbolic link to redirect download mirror to ${NEW_MIRROR_PATH}"
ln -sfn ${NEW_MIRROR_PATH} ${RELATIVE_MIRROR_PATH} 

popd > /dev/null
