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

    if [ $(rpm --eval '%dist') == ".el6" ] ; then
        # the argparse in Centos6/RHEL6 has slightly weird help output
        "$NOSE" -v --all-modules -e 'test_command_help'
    else
        "$NOSE" -v --all-modules
    fi

    echo
}


function verify_koji_cli() {
    echo 'Checking output of koji help:'

    local HELP=$(koji help)
    local EXPECTED=(
        affected-targets
        block-env-var
        block-rpm-macro
        bulk-tag-builds
        cginfo
        check-hosts
        client-config
        filter-builds
        latest-archives
        list-btypes
        list-build-archives
        list-cgs
        list-component-builds
        list-env-vars
        list-rpm-macros
        list-tag-extras
        perminfo
        remove-env-var
        remove-rpm-macro
        renum-tag-inheritance
        set-env-var
        set-rpm-macro
        swap-tag-inheritance
        userinfo
    )

    local RESULT=0

    for E in "${EXPECTED[@]}" ; do
        if ! grep -F "$E" 2>/dev/null <<< "$HELP" ; then
            echo "Subcommand "$E" not present"
            RESULT=1
        fi
    done

    echo
    return $RESULT
}


function verify_installed() {
    echo "Checking to see what is installed:"
    rpm -qa | grep koji | sort
    echo
}


function ksd_rpm_tests() {
    local PLATFORM="$1"

    local BASEDIR=/ksd
    local TESTDIR=$BASEDIR/tests
    local LOGDIR=$BASEDIR/logs

    local LOGFILE="$LOGDIR"/test-"$PLATFORM".log

    pushd "$BASEDIR" >/dev/null
    mkdir -p "$LOGDIR"

    {
        echo "==== BEGIN RESULTS FOR $PLATFORM ===="
        verify_installed 2>&1
        verify_koji_cli 2>&1
        run_nose 2>&1
        echo "==== END RESULTS FOR $PLATFORM ===="
    } | tee -a "$LOGFILE"

    popd >/dev/null
}


ksd_rpm_tests "$@"


# The end.
