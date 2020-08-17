

function whichever() {
    which "$@" 2>/dev/null | head -n1
}


function ksd_version() {
    local PYTHON=$(whichever python python2 python3)
    read -r -d'\0' SCRIPT <<EOF
from __future__ import print_function
import setup
print(setup.config()["version"])
EOF
     "$PYTHON" -B -c "$SCRIPT"
}


function ksd_rpmbuild() {
    local TOPDIR="$1"
    local TARBALL="$2"

    local SRPMS="$TOPDIR"/SRPMS
    local RPMS="$TOPDIR"/RPMS

    if [ `which dnf 2>/dev/null` ] ; then
        function ksd_install() {
            dnf install -qy "$@"
        }
        function ksd_builddep() {
            dnf builddep -qy "$@"
        }
    else
        function ksd_install() {
            yum install -q -y "$@"
        }
        function ksd_builddep() {
            yum-builddep -q -y "$@"
        }
    fi

    function ksd_rpmbuild() {
        rpmbuild --define "_topdir $TOPDIR" "$@"
    }

    rm -rf "$SRPMS" "$RPMS"

    ksd_rpmbuild -ts "$TARBALL"
    ksd_builddep "$SRPMS"/kojismokydingo-*.src.rpm
    ksd_rpmbuild --rebuild "$SRPMS"/kojismokydingo-*.src.rpm
    ksd_install "$RPMS"/noarch/*kojismokydingo-*.rpm
}


function ksd_build_platform() {
    local PLATFORM="$1"
    local CFILE=tools/Containerfile."$PLATFORM"

    local PODMAN=$(whichever podman docker)
    if [ $? != 0 ] ; then
       echo "Neither podman not docker available, exiting"
       return 1
    else
	echo "Using $PODMAN"
    fi

    if [ ! -f "$CFILE" ] ; then
        echo "File not found $CFILE"
        return 1
    fi

    local NAME=ksd-test:"$PLATFORM"

    # let's see if there was a previous image with this tag. We won't
    # remove it yet, we want to try and take cache advantage of any
    # layers in it.
    local PREV=$(podman images -a -q "$NAME")

    echo "Building $NAME from $CFILE"
    $PODMAN build \
            --build-arg VERSION=$(ksd_version) \
            --layers \
            -t "$NAME" \
            -f "$CFILE" "$PWD" || return 1

    # now let's see what the new image's ID is. If we had a previous
    # image, and the new image isn't identical, we can safely discard
    # the old to conserve some space.
    local CURR=$($PODMAN images -a -q "$NAME")
    if [ "$PREV" -a "$PREV" != "$CURR" ] ; then
        $PODMAN image rm -f "$PREV"
    fi

    # steal a copy of the RPMs from the image
    local RPMOUT="$PWD/dist/$PLATFORM"
    mkdir -p "$RPMOUT"
    local TMPID=$($PODMAN create "$NAME")
    $PODMAN cp "$TMPID":/src/SRPMS/ "$RPMOUT"
    $PODMAN cp "$TMPID":/src/RPMS/ "$RPMOUT"
    $PODMAN rm --force "$TMPID"
    echo "Copied RPMs to $RPMOUT"
}


function ksd_test_platform() {
    local PLATFORM="$1"
    local NAME=ksd-test:"$PLATFORM"

    local PODMAN=$(whichever podman docker)
    if [ $? != 0 ] ; then
       echo "Neither podman not docker available, exiting"
       return 1
    else
	echo "Using $PODMAN"
    fi

    echo "Running tests for $NAME"
    $PODMAN run --rm \
            --volume "$PWD"/logs:/ksd-logs \
            --volume "$PWD"/tests:/ksd-tests \
            "$NAME" \
            "/ksd-tests/packaging.sh" "$PLATFORM" || return 1
}


function ksd_platforms() {
    local BASE="tools/Containerfile"

    if [ ! "$@" ] ; then
        for N in $(ls "$BASE".* | grep -v '~$\|^#') ; do
            echo "$N" | rev | cut -f1 -d. | rev
        done

    else
        for N in "$@" ; do
            local FN="$BASE"."$N"
            if [ -f "$FN" ] ; then
                echo "$N"
            fi
        done
    fi
}


# The end.
