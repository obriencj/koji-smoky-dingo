#! /bin/bash


function launch-test() {
    local CFILE="$1"
    local PLATFORM=$(echo $CFILE | cut -f2- -d.)

    local NAME=ksd-test:"$PLATFORM"

    echo "Building $NAME from $CFILE"
    podman build -t $NAME -f "$CFILE" . || return 1

    echo "Running tests for $NAME"
    podman run --rm -t $NAME \
           --volume .:/ksd \
           "/ksd/tests/container/tests.sh"
}


function launch-all() {
    local FOUND=$(ls tests/container/Containerfile.* | grep -v '~$|^#')
    for CFILE in $FOUND ; do
        launch-test "$CFILE"
    done
}


launch-all


# The end.
