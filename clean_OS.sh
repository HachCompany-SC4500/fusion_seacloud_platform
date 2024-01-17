#!/bin/bash

# From .repo/manifests, go back to base folder fusion_seacloud_platform
# Remove build and deploy folders to force a full rebuild
pushd ../.. > /dev/null
[ -d "build" ] && mv build{,_old}
[ -d "deploy" ] && mv deploy{,_old}
rm -rf build_old deploy_old &
popd > /dev/null

