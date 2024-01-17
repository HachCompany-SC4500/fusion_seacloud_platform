# Eagle projet

## Setup of developement environment
----------
### Installation of the prerequisites:

For example, for Ubuntu 16.04 (64-bit), do:
```bash
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install g++-4.9-multilib
sudo apt-get install curl dosfstools gawk g++-multilib gcc-multilib lib32z1-dev libcrypto++9v5:i386 libcrypto++-dev:i386 liblzo2-dev:i386 libstdc++-4.9-dev:i386 libusb-1.0-0:i386 libusb-1.0-0-dev:i386 uuid-dev:i386

sudo apt-get install texinfo chrpath libsdl1.2-dev

sudo apt-get install repo diffstat

cd /usr/lib; sudo ln -s libcrypto++.so.9.0.0 libcryptopp.so.6
```
For complete and updated information, please refer to Yocto website:
https://www.yoctoproject.org/docs/2.6/mega-manual/mega-manual.html#ubuntu-packages

### Get the repo
To simplify installation we provide a repo manifest which manages the different git repositories
and the used versions. (more on repo: http://code.google.com/p/git-repo/ )

Install the repo bootstrap binary:
```bash
  mkdir ~/bin
  PATH=~/bin:$PATH
  curl http://commondatastorage.googleapis.com/git-repo-downloads/repo > ~/bin/repo
  chmod a+x ~/bin/repo
```
Create a directory for your oe-core setup to live in and clone the meta information.
```bash
  mkdir oe-core
  cd oe-core
  repo init -u ssh://git@stash.waterqualitytools.com:7999/fcfw/fusion_seacloud_platform.git -b SCR2
  repo sync
```
Source the file export to setup the environment. On first invocation this also copies a sample
configuration to build/conf/*.conf.
```bash
  . export
```

More information on Toradex developer website:

  https://developer.toradex.com/knowledge-base/board-support-package/openembedded-(core)

## Customize build environment
By default, Yocto will store data (downloaded sources, build cache, npm cache) in a local folder to speed-up rebuilds.
The settings are read from /home/<user>/.config/yocto/eagle/site.conf
If this file is missing, it is created with default values from meta-seacloud-bsp/buildconf/site.conf.samples/site.conf.user

You can change these settings:
- Globally for all builds: change the content of /home/<user>/.config/yocto/eagle/site.conf
- Locally per build: Create the following environment variable before sourcing the export script
 - define NO_SITECONF variable to disable usage of site.conf file and only rely on the local settings
 - define CUSTOM_SITECONF to point on the specific site.conf file you want to use for the build

## How to work with the repo
------------
### Branching workflow
Branches are created under the SeaCloud specific layers repositories(meta-seacloud and meta-seacloud-bsp).

Work is done on the branches. When the work is done, the modifications on the branches are merged into the SCR2 branch.

### Update repo manifest
Once modification have been merged into the SCR2 branch, it is needed to generate a manifest from what is currently checked out.
To do so:
```bash
 cd .repo/manifests
 ```
 if you have to update your local branch of the repository "SeaCloud-platform'
 ```bash
 git checkout -b my-branch-name
 ```
 then execute
 ```bash
 repo manifest --suppress-upstream-revision -r -o default_tmp.xml
 cp default_tmp.xml default.xml
 rm default_tmp.xml
 git commit -a -m 'description...'
 git push
 ```

### Force a repo sync on manifest revisions
To reset all the projects/layers back to the manifest revision, use the command :
```bash
repo sync -d
```
It can be useful when swapping between branches etc.

## Troubleshooting
------------
### repo : fail to check repo signature
If your version of repo installed is too old, it will complain it is not able to check signature of lastest version of repo downloaded.
To fix that, just update your local version of repo as described at the beginning of this document.

### repo : repo crashes with syntax errors
This can happens if you have an old version of python running (python 2.7 or python 3.5) that is not supported anymore by repo.
To fix that, remove previous local version or repo and force repo to use v2.9 (the last that support python 2.7) by using the following command:
```bash
  rm -rf .repo/repo
  repo init --repo-branch v2.9 -u ssh://git@stash.waterqualitytools.com:7999/fcfw/fusion_seacloud_platform.git -b SCR2
```

