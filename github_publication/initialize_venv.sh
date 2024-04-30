#!/bin/bash

# check number of parameters
if [ $# -ne 1 ]
then
	echo "This script initialize the python virtualenv environment"
	echo
	echo "Syntax: $0 <virtual environment destination path>"
	echo "e.g.: $0 /tmp/venv"
	exit -1
fi

SCRIPT_DIRECTORY=$(dirname "$0")

ENV_LOCATION=$1

if [ ! -d "${ENV_LOCATION}" ]
then
	echo "Error: The virtual environment destination path doesn't exist."
	exit -1
fi

# Convert path to absolute path
pushd ${ENV_LOCATION} > /dev/null
ABSOLUTE_LOCATION=$(pwd)
popd > /dev/null

# Install required tools if needed
# Required for DBus python module compilation

sudo DEBIAN_FRONTEND=noninteractive apt-get --yes install virtualenv python-dev

echo "Create virtual environment"
virtualenv -p python3 ${ENV_LOCATION}

# Check the maximum path length of the #! in all scripts generated in the virtual environment to detect path longer than 128

# grep --no-filename --binary-files=without-match '^#!'	: Scripts that contains a shebang (#!) are located in bin folder
# wc -L													: Print the length in byte of the longest line
bytelen=$(grep --no-filename --binary-files=without-match '^#!' ${ENV_LOCATION}/bin/* | wc -L)
if [ "${bytelen}" -gt "128" ]
then
	echo "Error: The virtual environment destination path is longer than 128 bytes. It will cause string 'bad interpreter' errors due to bash path limitation at 128 bytes."
	rm -rf ${ENV_LOCATION}
	exit -1
fi

echo "Activate virtualenv"
source ${ENV_LOCATION}/bin/activate

echo "Install needed requirements in the virtualenv"
pip install -r ${SCRIPT_DIRECTORY}/requirements.txt

echo "Desactive the virtualenv"
deactivate

echo "Virtual environment created"

echo "To activate the virtual environment later type: source ${ENV_LOCATION}/bin/activate"
echo "To deactivate the virtual environment type: deactivate"
echo "To Remove the virtual environment type: rm -r ${ENV_LOCATION}"

