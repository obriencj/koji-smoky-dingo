#! /bin/bash


function run_nose() {
    nosetests -v -w tests --all-modules
}


function verify_koji_cli() {
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
    fi
}


function test() {
    local BASEDIR=/ksd
    local LOGDIR="$BASEDIR"/logs

    local TESTNAME=$(rpm --eval '%{dist}')
    local LOGFILE="$LOGDIR"/test"$TESTNAME".log

    mkdir -p "$LOGDIR"
    cd "$BASEDIR"

    echo "Results for $TESTNAME" > "$LOGFILE"
    run_nose >> "$LOGFILE" 2>&1
    verify_koji_cli >> "$LOGFILE" 2>&1
}


test


#
# The end.
