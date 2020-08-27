#! /bin/bash


# This script is intended to be invoked inside of a container which
# has had koji and koji-smoky-dingo both installed in it, along with
# whatever other deps are needed to support them. See
# tools/launch-build.sh for how such a container is produced, and
# tools/launch-test.sh for how a built container is launched to invoke
# this script.

# Author: Christopher O'Brien <obriencj@gmail.com>
# License: GPL v3


function whichever() {
    which "$@" 2>/dev/null | head -n1
}


function run_nose() {
    echo "Running unit tests:"
    local NOSE=$(whichever nosetests-3 nosetests nosetests-2)
    if [ ! "$NOSE" ] ; then
        echo "No nosetests available on path"
        return 1
    fi
    "$NOSE" -w /ksd-tests -v --all-modules
    echo
}


function verify_koji_cli() {
    echo 'Checking output of `koji help`:'
    koji help \
        | grep \
              -e affected-targets \
              -e bulk-tag-builds \
              -e check-hosts \
              -e client-config \
              -e latest-archives \
              -e list-build-archives \
              -e list-cgs \
              -e list-env-vars \
              -e list-imported \
              -e list-rpm-macros \
              -e list-tag-extras \
              -e perminfo \
              -e renum-tag-inheritance \
              -e set-env-var \
              -e set-rpm-macro \
              -e swap-tag-inheritance \
              -e unset-env-var \
              -e unset-rpm-macro \
              -e userinfo

    if [ "$?" != 0 ] ; then
        echo "Subcommands not found in `koji help` output"
        return 1
    fi
    echo
}


function verify_installed() {
    echo "Checking to see what is installed:"
    rpm -qa | grep koji | sort
    echo
}


function ksd_rpm_tests() {
    local PLATFORM="$1"

    local TESTDIR=/ksd-tests
    local LOGDIR=/ksd-logs

    local LOGFILE="$LOGDIR"/test-"$PLATFORM".log

    mkdir -p "$LOGDIR"
    cd "$BASEDIR"

    {
        echo "==== BEGIN RESULTS FOR $PLATFORM ===="
        verify_installed 2>&1
        verify_koji_cli 2>&1
        run_nose 2>&1
        echo "==== END RESULTS FOR $PLATFORM ===="
    } | tee -a "$LOGFILE"
}


ksd_rpm_tests "$@"


# The end.
