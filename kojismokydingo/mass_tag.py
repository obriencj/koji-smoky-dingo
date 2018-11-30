# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
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


import sys

from argparse import ArgumentParser
from functools import partial
from six.moves import range as xrange, zip as izip

from . import koji_cli_plugin, printerr, \
    NoSuchTag, NoSuchBuild, NoSuchUser, PermissionException


def raise_nsb(nvr):
    # used as a parameter to iter_mass_load_builds to raise an
    # exception rather than continuing with mass build loading when a
    # result is not found
    raise NoSuchBuild(nvr)


def chunk_seq(seq, chunksize):
    return (seq[offset:offset + chunksize] for
            offset in xrange(0, len(seq), chunksize))


def iter_mass_load_builds(session, nvrs, nsbfn):
    for nvr_chunk in chunk_seq(nvrs, 100):
        session.multicall = True

        for nvr in nvr_chunk:
            session.getBuild(nvr)

        for nvr, binfo in izip(nvr_chunk, session.multiCall()):
            if binfo:
                if "faultCode" in binfo:
                    # koji returned an error dict instead of a list of
                    # builds
                    nsbfn(nvr)
                else:
                    # otherwise it returned a list of matching builds
                    # (usually just 1, but let's make sure)
                    for b in binfo:
                        if not b:
                            nsbfn(nvr)
                        else:
                            yield b
            else:
                nsbfn(nvr)


def mass_load_builds(session, nvrs, nsbfn):
    return list(iter_mass_load_builds(session, nvrs, nsbfn))


def read_builds(options):
    fin = open(options.file, "r") if options.file else sys.stdin

    # note we don't do any de-duping or re-ordering here, just cleaning
    # whitespace and dropping blank lines
    builds = [line for line in (l.strip() for l in fin) if line]

    if options.file:
        fin.close()

    return builds


def build_dedup(builds):
    dedup = dict()
    for index, b in enumerate(builds):
        dedup.setdefault(b["id"], (index, b))
    return [b for index, b in sorted(dedup.itervalues())]


def nvrcmp(left, right):
    from rpmUtils.miscutils import compareEVR

    ln, le, lv, lr, lb = left
    rn, re, rv, rr, rb = right

    return cmp(ln, rn) or compareEVR((le, lv, lr), (re, rv, rr))


def build_nvr_sort(builds):
    dedup = dict()
    for b in builds:
        nevrb = (b["name"], b["epoch"] or "0", b["version"], b["release"], b)
        dedup.setdefault(b["id"], nevrb)
    return [b for n, e, v, r, b in sorted(dedup.itervalues(), cmp=nvrcmp)]


def build_id_sort(builds):
    dedup = dict()
    for b in builds:
        dedup.setdefault(b["id"], b)
    return [b for bid, b in sorted(dedup.iteritems())]


def debug_on(message, *args):
    printerr(message % args)


def debug_off(message, *args):
    pass


def cli_mass_tag(options):

    session = options.session
    tagname = options.tagname

    test = options.test
    if test:
        options.debug = True

    debug = debug_on if options.debug else debug_off

    # the tagBuildBypass calls require admin, so let's make sure
    # we have that first.
    userinfo = session.getLoggedInUser()
    userperms = session.getUserPerms(userinfo["id"]) or ()

    if "admin" not in userperms:
        raise PermissionException()

    taginfo = session.getTag(tagname)
    if not taginfo:
        raise NoSuchTag(tagname)
    tagid = taginfo["id"]

    ownerid = None
    ownername = options.owner
    if ownername:
        ownerinfo = session.getUser(ownername)
        if not ownerinfo:
            raise NoSuchUser(ownername)
        ownerid = ownerinfo["id"]

    packages = session.listPackages(tagID=tagid,
                                    inherited=options.inherit)
    packages = set(pkg["package_id"] for pkg in packages)

    nvrs = read_builds(options)
    debug("fed with %i builds", len(nvrs))

    if options.cont:
        nsbfn = partial(debug, "no such build: %s")
    else:
        nsbfn = raise_nsb
    builds = mass_load_builds(session, nvrs, nsbfn)

    if options.nvr_sort:
        debug("NVR sorting specified")
        builds = build_nvr_sort(builds)
    elif options.id_sort:
        debug("ID sorting specified")
        builds = build_id_sort(builds)
    else:
        debug("no sorting specified, preserving feed order")
        builds = build_dedup(builds)

    if options.debug:
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
        tagBuildBypass = partial(debug, "tagBuildBypass %r %r %r")
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
    for build_chunk in chunk_seq(builds, 100):
        multiCallEnable()
        for build in build_chunk:
            pkg = build["package_id"]
            if pkg not in packages:
                packages.add(pkg)
                packageListAdd(tagid, pkg,
                               ownerid or build["owner_id"],
                               None, None, True)
            tagBuildBypass(tagid, build["id"], True)
        multiCall()
        counter += len(build_chunk)
        debug(" tagged %i/%i", counter, len(builds))

    debug("All done!")


def options_mass_tag(name):
    """
    [admin] Quickly tag a large number of builds
    """

    parser = ArgumentParser(prog=name)
    addarg = parser.add_argument

    addarg("tag", action="store", metavar="TAG",
           help="Tag to associate builds with")

    addarg("--debug", action="store_true", default=False,
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

    addarg("--file", action="store", default=None,
           help="Read list of builds from file, one NVR per line."
           " Omit for default behavior: read build NVRs from stdin")

    addarg("--continue", action="store_true", default=False,
           dest="cont", help="Continue with tagging operations,"
           " even after encountering a malformed or non-existing"
           " NVR")

    group = parser.add_mutually_exclusive_group()
    addarg = group.add_argument

    addarg("--nvr-sort", action="store_true", default=False,
           help="pre-sort build list by NVR, so highest NVR is"
           " tagged last")

    addarg("--id-sort", action="store_true", default=False,
           help="pre-sort build list by build ID, so most recently"
           " completed build is tagged last")

    return parser


# provide the function that entry_points will want
cli = koji_cli_plugin(options_mass_tag, cli_mass_tag)


# The end.
