#! /bin/bash


function launch-test() {
    local CFILE="$1"
    local PLATFORM=$(echo $CFILE | cut -f2- -d.)

    local NAME=ksd-test:"$PLATFORM"

    local PODMAN=$(which podman || which docker)
    if [ $? != 0 ] ; then
       echo "Neither podman not docker available, exiting"
       return 1
    else
	echo "Using $PODMAN"
    fi

    echo "Building $NAME from $CFILE"
    $PODMAN build -t "$NAME" -f "$CFILE" "$PWD" || return 1

    echo "Running tests for $NAME"
    $PODMAN run --volume "$PWD":/ksd --rm "$NAME" \
           "/ksd/tests/container/tests.sh" "$PLATFORM"

    local RESULT=$?

    $PODMAN image rm -f "$NAME"

    return "$RESULT"
}


function discover() {
    for N in "$@" ; do
        local FN=tests/container/Containerfile."$N"
        if [ -f "$FN" ] ; then
            echo "$FN"
        fi
    done
}


function launch() {
    local FOUND=$(discover "$@")

    if [ ! "$FOUND" ] ; then
        FOUND=$(ls tests/container/Containerfile.* | grep -v '~$\|^#')
    fi

    for CFILE in $FOUND ; do
        launch-test "$CFILE"
    done
}


launch "$@"


# The end.
