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


function expected_entry_points() {
    local PYTHON=$(whichever python3 python python2)
    read -r -d'\0' SCRIPT <<EOF
from __future__ import print_function
from tests.cli import ENTRY_POINTS
for name in sorted(ENTRY_POINTS):
    print(name)
EOF
    "$PYTHON" -B -c "$SCRIPT"
}


function expected_standalone() {
    local PYTHON=$(whichever python3 python python2)
    read -r -d'\0' SCRIPT <<EOF
from __future__ import print_function
from tests.standalone import ENTRY_POINTS
for name in sorted(ENTRY_POINTS):
    print(name)
EOF
    "$PYTHON" -B -c "$SCRIPT"
}


function run_nose() {
    echo "Running unit tests:"
    local NOSE=$(whichever nosetests-3 nosetests nosetests-2)
    if [ ! "$NOSE" ] ; then
        echo "No nosetests available on path"
        return 1
    fi

    local DIST=$(rpm --eval '%dist')
    if [[ "$DIST" == ".el6" || "$DIST" > ".fc32" ]] ; then
        # the argparse in Centos6/RHEL6 has slightly weird help output
        # around mutually exclusive options. The argparse in Fedora
        # 33+ has slightly weird help output around nargs=*
        # positionals.
        "$NOSE" -v --all-modules \
                -e 'test_command_help' \
                -e 'test_standalone_help'
    else
        "$NOSE" -v --all-modules
    fi

    echo
}


function verify_koji_cli() {
    echo 'Checking output of koji help:'

    local HELP=$(koji help)
    local RESULT=0

    for E in $(expected_entry_points) ; do
        if ! grep -F "$E" 2>/dev/null <<< "$HELP" ; then
            echo "Subcommand "$E" not present"
            RESULT=1
        fi
    done

    echo
    return $RESULT
}


function verify_standalone() {
    echo 'Checking for standalone scripts:'

    local RESULT=0

    for E in $(expected_standalone) ; do
        if ! "$E" --help | grep "^usage: $E" ; then
            echo "Standalone command "$E" not present"
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
        verify_installed
        verify_koji_cli
        verify_standalone
        run_nose
        echo "==== END RESULTS FOR $PLATFORM ===="
    } 2>&1 | tee -a "$LOGFILE"

    popd >/dev/null
}


ksd_rpm_tests "$@"


#
# The end.
