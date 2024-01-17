#!/usr/bin/env bash

# Exit on error
set -e

VIRTUALENV_FOLDER="venv"

# Exit if environment is already present
[ -x "${VIRTUALENV_FOLDER}" ] && ( echo "Virtual environment folder already exists. Remove it if you know what your are doing and try again" ; exit 1 )

echo "Create Python3 virtual environment"
python3 -m venv "${VIRTUALENV_FOLDER}"

source "${VIRTUALENV_FOLDER}/bin/activate"

echo "Force update to setuptools 50.3.2 (lastest version supporting Python 3.5.2 used on Ubuntu 16) otherwise python-docx install fails"
pip3 install setuptools==50.3.2
pip3 install wheel

echo "Install required modules"
# pip3 install -r requirements.txt can strangly fails due to PATH length limit of #! in shell script
# Use the proposed workaround to call pip through python interpreter (https://github.com/pypa/virtualenv/issues/596#issuecomment-411485104)
pip3 install -r requirements.txt
