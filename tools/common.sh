# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.


# Collection of bash functions for use in building and testing this
# project.

# Author: Christopher O'Brien <obriencj@gmail.com>
# License: GPL v3


function whichever() {
    which "$@" 2>/dev/null | head -n1
}


function ksd_version() {
    local PYTHON=$(whichever python3 python)
    "$PYTHON" -B setup.py --version
}


function ksd_rpmbuild() {
    # this is intended to be invoked inside of a container.  This
    # function will produce an SRPM, install its build dependencies,
    # rebuild the SRPM into RPMS, then install those RPMs and their
    # dependencies.

    local TOPDIR="$1"
    local TARBALL="$2"

    local SRPMS="$TOPDIR"/SRPMS
    local RPMS="$TOPDIR"/RPMS

    function _builddep() {
        dnf builddep --disablerepo=*source -qy "$@"
    }
    function _rpmbuild() {
	rpmbuild --define "_topdir $TOPDIR" "$@"
    }

    rm -rf "$SRPMS" "$RPMS"

    _rpmbuild -ts "$TARBALL" || return 1
    _builddep "$SRPMS"/kojismokydingo-*.src.rpm || return 1
    _rpmbuild --rebuild "$SRPMS"/kojismokydingo-*.src.rpm || return 1
    dnf install -qy "$RPMS"/noarch/*kojismokydingo-*.rpm || return 1
}


function ksd_prune() {

    local PODMAN=$(whichever podman docker)
    if [ ! "$PODMAN" ] ; then
        echo "Neither podman nor docker available, exiting"
        return 1
    else
	echo "Using $PODMAN"
    fi

    echo "Pruning images"
    $PODMAN image prune -f
}


function ksd_clean_platform() {
    # Given a platform, remove its container image.

    local PLATFORM="$1"
    local CFILE=tools/Containerfile."$PLATFORM"

    local PODMAN=$(whichever podman docker)
    if [ ! "$PODMAN" ] ; then
        echo "Neither podman nor docker available, exiting"
        return 1
    else
	echo "Using $PODMAN"
    fi

    if [ ! -f "$CFILE" ] ; then
        echo "File not found $CFILE"
        return 1
    fi

    local NAME=ksd2-test:"$PLATFORM"
    local CURR=$($PODMAN images -a -q "$NAME" 2>/dev/null)

    if [ "$CURR" ] ; then
        echo "Cleaning up image $NAME $CURR"
        $PODMAN image rm -f "$CURR"
    else
        echo "Image not found $NAME"
    fi
}


function ksd_build_platform() {
    # Given a platform, build the relevant container image for it, and
    # tag the image for use. This should as a side effect produce
    # SRPMs and RPMs, which we copy out of the image and into the dist
    # directory.

    # Older rebuilds of the same image will be removed.

    local PLATFORM="$1"
    local CFILE=tools/Containerfile."$PLATFORM"

    local PODMAN=$(whichever podman docker)
    if [ ! "$PODMAN" ] ; then
        echo "Neither podman nor docker available, exiting"
        return 1
    else
	echo "Using $PODMAN"
    fi

    if [ ! -f "$CFILE" ] ; then
        echo "File not found $CFILE"
        return 1
    fi

    local NAME=ksd2-test:"$PLATFORM"

    # let's see if there was a previous image with this tag. We won't
    # remove it yet, we want to try and take cache advantage of any
    # layers in it.
    local PREV=$($PODMAN images -a -q "$NAME" 2>/dev/null)

    echo "Building $NAME from $CFILE"
    local BUILDAH_LAYERS=true
    $PODMAN build \
            --build-arg VERSION=$(ksd_version) \
            -t "$NAME" \
            -f "$CFILE" "$PWD" || return 1

    # now let's see what the new image's ID is. If we had a previous
    # image, and the new image isn't identical, we can safely discard
    # the old to conserve some space.
    local CURR=$($PODMAN images -a -q "$NAME")
    if [ "$PREV" -a "$PREV" != "$CURR" ] ; then
        $PODMAN image rm -f "$PREV"
    fi

    # steal a copy of the RPMs from the image. We have to actually
    # create a temporary container from the image in order to do this,
    # which we subsequently remove
    local RPMOUT="$PWD/dist/$PLATFORM"
    mkdir -p "$RPMOUT"
    local TMPID=$($PODMAN create "$NAME")
    $PODMAN cp "$TMPID":/src/SRPMS/ "$RPMOUT"
    $PODMAN cp "$TMPID":/src/RPMS/ "$RPMOUT"
    $PODMAN rm --force "$TMPID"
    echo "Copied RPMs to $RPMOUT"
}


function ksd_test_platform() {
    # launch a test platform container and run the packaging.sh test
    # script in it. Results will be written to the logs directory.

    local PLATFORM="$1"
    local NAME=ksd2-test:"$PLATFORM"

    local PODMAN=$(whichever podman docker)
    if [ ! "$PODMAN" ] ; then
        echo "Neither podman nor docker available, exiting"
        return 1
    else
	echo "Using $PODMAN"
    fi

    # ensure the logdir exists
    mkdir -p "$PWD/logs"

    echo "Running tests for $NAME"
    $PODMAN run --rm \
            --volume "$PWD"/docs:/ksd/docs \
            --volume "$PWD"/logs:/ksd/logs \
            --volume "$PWD"/tests:/ksd/tests \
            "$NAME" \
            "/ksd/tests/packaging.sh" "$PLATFORM"
}


function ksd_platforms() {
    # hunt through the available platforms and emit the Containerfile
    # for that platform. These will be denoted by the extension of the
    # Containerfile itself. So eg. a platform of centos6 will be
    # Containerfile.centos6. If no arguments are given, emits all the
    # Containerfiles for all the platforms.

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


#
# The end.
