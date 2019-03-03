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


"""
Koji Smoky Dingo - admin command mass-tag

Allows for large numbers of builds to be tagged rapidly, via multicall
to tagBuildBypass

:author: cobrien@redhat.com
:license: GPL version 3
"""


from __future__ import print_function

import sys
from collections import OrderedDict
from functools import partial
from six import iteritems, itervalues

from . import AdminSmokyDingo, NoSuchTag, NoSuchUser, \
    chunkseq, compareEVR, bulk_load_builds, read_clean_lines


SORT_BY_ID = "sort-by-id"
SORT_BY_NVR = "sort-by-nvr"


try:
    cmp

except NameError:
    def cmp(left, right):
        if left == right:
            return 0
        elif left < right:
            return -1
        else:
            return 1


class NEVRCompare(object):

    def __init__(self, binfo):
        self.build = binfo
        self.n = binfo["name"]
        self.e = binfo["epoch"] or "0"
        self.v = binfo["version"]
        self.r = binfo["release"]

    def __cmp__(self, other):
        return cmp(self.n, other.n) or \
            compareEVR((self.e, self.v, self.r), (other.e, other.v, other.r))

    def __eq__(self, other):
        return (self.n, self.e, self.v, self.r) == \
            (other.n, other.e, other.v, other.r)

    def __lt__(self, other):
        return self.__cmp__(other) == -1

    def __gt__(self, other):
        return self.__cmp__(other) == 1


def build_nvr_sort(builds):
    dedup = dict((b["id"], b) for b in builds)
    return sorted(itervalues(dedup), key=NEVRCompare)


def build_id_sort(builds):
    dedup = dict((b["id"], b) for b in builds)
    return [b for _bid, b in sorted(iteritems(dedup))]


def build_dedup(builds):
    dedup = OrderedDict((b["id"], b) for b in builds)
    return list(itervalues(dedup))


def cli_mass_tag(session, tagname, nvrs,
                 sorting=None, strict=False,
                 owner=None, inherit=False,
                 notify=False,
                 verbose=False, test=False):

    # set up the verbose debugging output function
    if test or verbose:
        def debug(message, *args):
            print(message % args, file=sys.stderr)
    else:
        def debug(message, *args):
            pass

    # fetch the destination tag info (and make sure it actually
    # exists)
    taginfo = session.getTag(tagname)
    if not taginfo:
        raise NoSuchTag(tagname)
    tagid = taginfo["id"]

    # figure out how we're going to be dealing with builds that don't
    # have a matching pkg entry already. Someone needs to own them...
    ownerid = None
    if owner:
        ownerinfo = session.getUser(owner)
        if not ownerinfo:
            raise NoSuchUser(owner)
        ownerid = ownerinfo["id"]

    packages = session.listPackages(tagID=tagid,
                                    inherited=inherit)
    packages = set(pkg["package_id"] for pkg in packages)


    # load the buildinfo for all of the NVRs
    debug("fed with %i builds", len(nvrs))

    builds = bulk_load_builds(session, nvrs, err=True)
    print(builds)

    builds = itervalues(builds)

    # sort as requested
    if sorting == SORT_BY_NVR:
        debug("NVR sorting specified")
        builds = build_nvr_sort(builds)
    elif sorting == SORT_BY_ID:
        debug("ID sorting specified")
        builds = build_id_sort(builds)
    else:
        debug("no sorting specified, preserving feed order")
        builds = build_dedup(builds)

    if verbose:
        debug("sorted and trimmed duplicates to %i builds", len(builds))
        for build in builds:
            debug(" %s %i", build["nvr"], build["id"])

    if not builds:
        debug("Nothing to do!")
        return

    # set up the four actions we'll take on the session client. If
    # this is test mode, we don't want to actually call anything, just
    # print some debugging info.
    if test:
        multiCallEnable = partial(debug, "multicall = True")
        packageListAdd = partial(debug, "packageListAdd %r %r %r %r %r %r")
        tagBuildBypass = partial(debug, "tagBuildBypass %r %r %r %r")
        multiCall = partial(debug, "multiCall()")
    else:
        def multiCallEnable():
            session.multicall = True
        packageListAdd = session.packageListAdd
        tagBuildBypass = session.tagBuildBypass
        multiCall = session.multiCall

    # and finally, tag them all in chunks of 100
    debug("begining mass tagging")
    counter = 0
    for build_chunk in chunkseq(builds, 100):
        multiCallEnable()
        for build in build_chunk:
            pkg = build["package_id"]
            if pkg not in packages:
                packages.add(pkg)
                packageListAdd(tagid, pkg,
                               ownerid or build["owner_id"],
                               None, None, True)
            tagBuildBypass(tagid, build["id"], True, notify)
        multiCall()
        counter += len(build_chunk)
        debug(" tagged %i/%i", counter, len(builds))

    debug("All done!")


class cli(AdminSmokyDingo):

    description = "Quickly tag a large number of builds"


    def parser(self):
        argp = super(cli, self).parser()
        addarg = argp.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Tag to associate builds with")

        addarg("-v", "--verbose", action="store_true", default=False,
               help="Print debugging information")

        addarg("--test", action="store_true", default=False,
               help="Print write operatons to stderr without actually"
               " calling the RPC function")

        addarg("--owner", action="store", default=None,
               help="Force missing package listings to be created"
               " with the specified owner")

        addarg("--no-inherit", action="store_false", default=True,
               dest="inherit", help="Do not use parent tags to"
               " determine existing package listing.")

        addarg("--file", action="store", default="-",
               dest="nvr_file", metavar="NVR_FILE",
               help="Read list of builds from file, one NVR per line."
               " Omit for default behavior: read build NVRs from stdin")

        addarg("--strict", action="store_true", default=False,
               help="Ensure all NVRs are valid before tagging any.")

        addarg("--notify", action="store_true", default=False,
               help="Send tagging notifications.")

        group = argp.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--nvr-sort", action="store_const",
               dest="sorting", const=SORT_BY_NVR, default=None,
               help="pre-sort build list by NVR, so highest NVR is"
               " tagged last")

        addarg("--id-sort", action="store_const",
               dest="sorting", const=SORT_BY_ID, default=None,
               help="pre-sort build list by build ID, so most recently"
               " completed build is tagged last")

        return argp


    def handle(self, options):
        nvrs = read_clean_lines(options.nvr_file)

        return cli_mass_tag(self.session, options.tag, nvrs,
                            options.sorting, options.strict,
                            options.owner, options.inherit,
                            options.notify,
                            options.verbose, options.test)


#
# The end.
