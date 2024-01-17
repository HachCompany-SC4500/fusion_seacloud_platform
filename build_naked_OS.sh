#!/bin/bash

if [ $# -ne 1 ]
then
	echo "Usage: $0 <image name>"
	exit 1
fi

# From .repo/manifests, go back to base folder fusion_seacloud_platform
pushd ../.. > /dev/null

# Export environment variables
source ./export

# Return parameter $1 as return code
function return_code {
	return $1;
}

# Execute command using time and return measurement into stdout
# Pass a command as parameter and add single quote if command contains special characters ; ...
function time_to_stdout {
	# execute command passed and keep it properly quoted with eval and printf
	# backup exit code
	# redirect stderr to stdout to move timing of time into stdout
	# return with backup exit code
        time ( eval "$(printf " %q" "$@")" ; success=$?; exec 2>&1; return_code $success )
}
# Launch bitbake to build OS image
time_to_stdout  bitbake $1 || exit 1

popd > /dev/null

./generate_OSS_notices.sh

GIT_REVISION_FILE=../../deploy/images/os_commit
echo "Save current git SHA1 and branch into ${GIT_REVISION_FILE}"
git rev-parse HEAD > ${GIT_REVISION_FILE}
git rev-parse --abbrev-ref HEAD >> ${GIT_REVISION_FILE}
