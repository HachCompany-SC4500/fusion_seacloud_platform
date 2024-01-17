# Open Source Software Notice summary file generatation
This folder provides scripts to generate the Open Source Software Notice summary file to comply with the Open Source common requirements.

## To generate the notice file
To generate the file, just call the generate_OSS_notices.sh script located in the manifest folder after a build with bitbake is complete (the directory containing all the license files is populated by bitbake).
It will automatically build the needed environment and generate the output in yocto deploy folder (e.g. : SC4500_OSS_Notices.docx).

>./generate_OSS_notices.sh

## To develop

### Script to initialize a python virtual environment
To have all the required dependencies, use the provided virtual environment. The script prepare_virtualenv.sh will create and activate the environment.
>./prepare_virtualenv.sh

### Updating python virtual environment requirements
During development you can require new python modules. In that case, install them (from an activated virtual environment) with:
>pip3 install <module name>

When you have all your requirements installed, update the requirements.txt file accordingly. To do it launch:
>pip3 freeze > requirements.txt
