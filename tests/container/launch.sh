#! /bin/bash


function launch-test() {
    local CFILE="$1"
    local PLATFORM=$(echo $CFILE | cut -f2- -d.)

    local NAME=ksd-test:"$PLATFORM"

    echo "Building $NAME from $CFILE"
    podman build -t "$NAME" -f "$CFILE" . || return 1

    echo "Running tests for $NAME"
    podman run --volume .:/ksd --rm "$NAME" \
           "/ksd/tests/container/tests.sh" "$PLATFORM"

    podman image rm -f "$NAME"
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
