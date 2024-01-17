#!/bin/bash

if [ $# -ne 1 ]
then
	echo "Usage: $0 <path where to install SDK>"
	echo "Waring! The path content will be deleted before installation"
	exit 1
fi

# Remove old SDK before installing it again
sudo rm -rf $1

SDKFilename=$(find ../../deploy/sdk/ -name "*toolchain*.sh")
echo $1 | ${SDKFilename}

