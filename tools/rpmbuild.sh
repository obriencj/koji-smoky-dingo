#! /bin/bash

# WARNING!  This script is intended to be invoked from inside of a
# container. It will attempt to install dependencies in order to build
# an SRPM from a tarball, rebuild the SRPM into an RPM, and finally
# install those built RPMs. See the various Containerfiles in this
# directory for reference.


. $(readlink -f $(dirname "$0"))/common.sh

ksd_rpmbuild "$@"


# The end.
