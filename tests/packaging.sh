#! /bin/bash


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
              -e renum-tag-inheritance \
              -e set-rpm-macro \
              -e swap-tag-inheritance \
              -e unset-rpm-macro \
              -e bulk-tag-builds \
              -e affected-targets \
              -e check-hosts \
              -e client-config \
              -e latest-archives \
              -e list-build-archives \
              -e list-cgs \
              -e list-imported \
              -e list-rpm-macros \
              -e perminfo \
              -e userinfo

    if [ "$?" != 0 ] ; then
        echo "Subcommands not found in `koji help` output"
        return 1
    fi
    echo
}


function verify_installed() {
    echo "Checking to see what is installed:"
    rpm -qa | grep koji
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
