#! /bin/bash


function run_nose() {
    nosetests -v --all-modules
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
    local PLATFORM="$1"

    local BASEDIR=/ksd
    local LOGDIR="$BASEDIR"/logs

    local LOGFILE="$LOGDIR"/test-"$PLATFORM".log

    mkdir -p "$LOGDIR"
    cd "$BASEDIR"

    echo "==== BEGIN RESULTS FOR $PLATFORM ====" > "$LOGFILE"
    run_nose >> "$LOGFILE" 2>&1
    verify_koji_cli >> "$LOGFILE" 2>&1
    echo "==== END RESULTS FOR $PLATFORM ====" >> "$LOGFILE"

    # grab a copy of the built SRPM and RPMs as well
    local RPMOUT="dist/$PLATFORM"
    mkdir -p "$RPMOUT"
    cp /root/rpmbuild/SRPMS/*.src.rpm \
       /root/rpmbuild/RPMS/noarch/*.rpm \
       "$RPMOUT"
}


test "$@"


#
# The end.
