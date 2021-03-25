#! /bin/bash


. $(readlink -f $(dirname "$0"))/common.sh


for PLATFORM in $(ksd_platforms "$@") ; do
    ksd_build_platform "$PLATFORM" || exit 1
    echo
done


ksd_prune


# The end.
