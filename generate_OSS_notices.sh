#!/bin/bash

# Exit on error
set -e

pushd notices > /dev/null

source ./prepare_virtualenv.sh

./generate_notice.py

echo "Exit and delete virtual environment"
deactivate
rm -rf venv

popd > /dev/null
