#! /bin/bash


# Launches the test suite inside containers created from the
# already-built kst-test images. The platforms specified as optional
# arguments must correlate to the suffixes of the Containerfiles in
# this directory.


. $(readlink -f $(dirname "$0"))/common.sh

for PLATFORM in $(ksd_platforms "$@") ; do
    ksd_test_platform "$PLATFORM" || exit 1
    echo
done


# The end.
