#! /bin/bash


. $(readlink -f $(dirname "$0"))/common.sh


for PLATFORM in $(ksd_platforms "$@") ; do
    ksd_build_platform "$PLATFORM"
done


# The end.
