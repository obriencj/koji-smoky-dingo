

function whichever() {
    which "$@" 2>/dev/null | head -n1
}


function run_nose() {
    local NOSE=$(whichever nosetests-3 nosetests nosetests-2)
    if [ ! "$NOSE" ] ; then
        echo "No nosetests available on path"
        return 1
    fi
    "$NOSE" -v --all-modules
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
        return 1
    fi
}


function ksd_rpm_tests() {
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


function ksd_launch_container_test() {
    local CFILE="$1"
    local PLATFORM=$(echo $CFILE | cut -f2- -d.)

    local NAME=ksd-test:"$PLATFORM"

    local PODMAN=$(whichever podman docker)
    if [ $? != 0 ] ; then
       echo "Neither podman not docker available, exiting"
       return 1
    else
	echo "Using $PODMAN"
    fi

    # let's see if there was a previous image with this tag. We won't
    # remove it yet, we want to try and take cache advantage of any
    # layers in it.
    local PREV=$(podman images -a -q "$NAME")

    echo "Building $NAME from $CFILE"
    $PODMAN build --layers -t "$NAME" -f "$CFILE" "$PWD" || return 1

    # now let's see what the new image's ID is. If we had a previous
    # image, and the new image isn't identical, we can safely discard
    # the old to conserve some space.
    local CURR=$(podman images -a -q "$NAME")
    if [ "$PREV" -a "$PREV" != "$CURR" ] ; then
        $PODMAN image rm -f "$PREV"
    fi

    echo "Running tests for $NAME"
    $PODMAN run --volume "$PWD":/ksd --rm "$NAME" \
           "/ksd/tests/container/tests.sh" "$PLATFORM" || return 1
}


function ksd_discover() {
    for N in "$@" ; do
        local FN=tests/container/Containerfile."$N"
        if [ -f "$FN" ] ; then
            echo "$FN"
        fi
    done
}


function ksd_launch_container() {
    local FOUND=$(ksd_discover "$@")

    if [ ! "$FOUND" ] ; then
        FOUND=$(ls tests/container/Containerfile.* | grep -v '~$\|^#')
    fi

    for CFILE in $FOUND ; do
        ksd_launch_container_test "$CFILE"
    done
}


# The end.
