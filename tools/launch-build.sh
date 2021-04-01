#! /bin/bash


# Launches the build script to generate container images for the
# various supported platforms. Platforms are indicated as suffixes to
# the Containerfiles in this directory. Each platform will have an
# image generated. As part of the image build process the KSD SRPM and
# RPM will be created, and the RPM will be installed into the
# image. Previous copies of the platform images will have their layers
# reused if possible, but will be removed and pruned after the new
# images are complete.


. $(readlink -f $(dirname "$0"))/common.sh

for PLATFORM in $(ksd_platforms "$@") ; do
    ksd_build_platform "$PLATFORM" || exit 1
    echo
done

ksd_prune


# The end.
