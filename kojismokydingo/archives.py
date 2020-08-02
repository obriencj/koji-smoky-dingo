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
Koji Smoky Dingo - working with archives and rpms

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from koji import PathInfo
from os.path import join
from six import iterkeys, iteritems

from . import NoSuchTag, bulk_load_rpm_sigs


def filter_archives(session, archives, archive_types):
    """
    Given a list of archives (or RPMs dressed up like archives),
    return a new list of those archives which are of the given archive
    types.

    archives - list of archive dicts
    archive_types - list of str archive extensions
    """

    # convert the list of string extensions from atypes into a set of
    # archive type IDs
    session.multicall = True
    for t in archive_types:
        session.getArchiveType(t)
    atypes = session.multiCall()
    atypes = set(t[0]["id"] for t in atypes if t and t[0])

    # RPM is a special type, which isn't considered an archive but
    # rather its own first-class type. However, we want to pretend
    # like it's any other archive type, so we'll give it the otherwise
    # unused ID of 0
    if "rpm" in archive_types:
        atypes.add(0)

    # find only those archives whose type_id is in the set of desired
    # archive types
    result = []
    for archive in archives:
        if archive["type_id"] in atypes:
            result.append(archive)

    return result


def gather_signed_rpms(session, archives, sigkeys):
    """
    Given a list of RPM archive dicts, query the session for all the
    pertinent signature headers, then try and find the best matching
    signed copy of each RPM. An empty string at the end of sigkeys
    will allow an unsigned copy to be included if no signed copies
    match.

    archives - list of RPM archive dicts
    sigkeys - list of signature fingerprints, in order of precedence
    """

    if not sigkeys:
        return archives

    results = []

    # an ID: RPM Archive mapping
    rpms = dict((rpm["id"], rpm) for rpm in archives)

    # now bulk load all the sigs for each RPM ID
    rpm_sigs = bulk_load_rpm_sigs(session, iterkeys(rpms))

    for rpm_id, rpm in iteritems(rpms):
        found = set(sig["sigkey"] for sig in rpm_sigs[rpm_id])
        for wanted in sigkeys:
            if wanted in found:
                rpm["sigkey"] = wanted
                results.append(rpm)
                break

    return results


def gather_build_rpms(session, binfo, rpmkeys=(), path=None):

    bid = binfo["id"]
    pathinfo = PathInfo(path or "")

    build_path = pathinfo.build(binfo)
    found = session.listRPMs(buildID=bid)

    if rpmkeys:
        found = gather_signed_rpms(session, found, rpmkeys)

    for f in found:
        key = f["sigkey"] if rpmkeys else None
        rpmpath = pathinfo.signed(f, key) if key else pathinfo.rpm(f)
        f["filepath"] = join(build_path, rpmpath)

        # fake some archive members, since RPMs are missing these
        f["type_id"] = 0
        f["type_name"] = "rpm"

    return found


def gather_build_maven_archives(session, binfo, path=None):

    bid = binfo["id"]
    pathinfo = PathInfo(path or "")

    build_path = pathinfo.mavenbuild(binfo)
    found = session.listArchives(buildID=bid, type="maven")
    for f in found:
        f["filepath"] = join(build_path, pathinfo.mavenfile(f))

    return found


def gather_build_win_archives(session, binfo, path=None):

    bid = binfo["id"]
    pathinfo = PathInfo(path or "")

    build_path = pathinfo.winbuild(binfo)
    found = session.listArchives(buildID=bid, type="win")
    for f in found:
        f["filepath"] = join(build_path, pathinfo.winfile(f))

    return found


def gather_build_image_archives(session, binfo, path=None):

    bid = binfo["id"]
    pathinfo = PathInfo(path or "")

    build_path = pathinfo.imagebuild(binfo)
    found = session.listArchives(buildID=bid, type="image")
    for f in found:
        f["filepath"] = join(build_path, f["filename"])

    return found


def gather_build_archives(session, binfo, btype,
                          rpmkeys=(), path=None):

    """
    Produce a list of archive dicts associated with a build, filtered by
    build-type
    """

    known_types = ("rpm", "maven", "win", "image", )
    found = []

    if btype in (None, "rpm"):
        found.extend(gather_build_rpms(session, binfo, rpmkeys, path))

    if btype in (None, "maven"):
        found.extend(gather_build_maven_archives(session, binfo, path))

    if btype in (None, "win"):
        found.extend(gather_build_win_archives(session, binfo, path))

    if btype in (None, "image"):
        found.extend(gather_build_image_archives(session, binfo, path))

    if btype in known_types:
        return found

    bid = binfo["id"]
    pathinfo = PathInfo(path or "")

    # at this point, btype is either None or not one of the known
    # types. Therefore, we'll pass that directly on to the query, and
    # filter out the known types from the resuls in the event the type
    # was None (as we'll have done special work to load those
    # already).
    archives = session.listArchives(buildID=bid, type=btype)
    for f in archives:
        abtype = f["btype"]
        if abtype in known_types:
            continue

        build_path = pathinfo.typedir(binfo, abtype)
        f["filepath"] = join(build_path, f["filename"])

        found.append(f)

    return found


def _fake_maven_build(archive, pathinfo, btype="maven", cache={}):
    """
    produces something that looks like a build info dict based on the
    values from within a maven archive dict. This can then be used
    with a koji.PathInfo instance to determine the path to a build
    """

    bid = archive["build_id"]
    if bid in cache:
        return cache[bid]

    bld = {
        "id": bid,
        "name": archive["build_name"],
        "version": archive["build_version"],
        "release": archive["build_release"],
        "epoch": archive["build_epoch"],
        "volume_id": archive["volume_id"],
        "volume_name": archive["volume_name"],
        "package_id": archive["pkg_id"],
        "package_name": archive["build_name"],
    }
    bld["build_path"] = pathinfo.typedir(bld, btype)
    cache[bid] = bld

    return bld


def gather_latest_rpms(session, tagname, rpmkeys=(), path=None):

    pathinfo = PathInfo(path or "")

    found, builds = session.getLatestRPMS(tagname)

    # decorate the build info with its path data
    for bld in builds:
        bld["build_path"] = pathinfo.build(bld)

    builds = dict((bld["id"], bld) for bld in builds)

    if rpmkeys:
        found = gather_signed_rpms(session, found, rpmkeys)

    for f in found:
        bld = builds[f["build_id"]]
        key = f["sigkey"] if rpmkeys else None
        rpmpath = pathinfo.signed(f, key) if key else pathinfo.rpm(f)
        f["filepath"] = join(bld["build_path"], rpmpath)

        # fake some archive members, since RPMs are missing these
        f["type_id"] = 0
        f["type_name"] = "rpm"

    return found


def gather_latest_maven_archives(session, tagname, path=None):

    pathinfo = PathInfo(path or "")

    found = session.getLatestMavenArchives(tagname)
    for f in found:
        bld = _fake_maven_build(f, pathinfo)
        f["filepath"] = join(bld["build_path"], pathinfo.mavenfile(f))

    return found


def gather_latest_win_archives(session, tagname, path=None):

    pathinfo = PathInfo(path or "")

    found = []

    archives, builds = session.listTaggedArchives(tagname,
                                                  inherit=True,
                                                  latest=True,
                                                  type="win")

    # decorate the build infos with the type paths for windows
    for bld in builds:
        bld["build_path"] = pathinfo.winbuild(bld)

    # convert builds to an id:binfo mapping
    builds = dict((bld["id"], bld) for bld in builds)

    for archive in archives:
        bld = builds[archive["build_id"]]
        build_path = bld["build_path"]

        # build an archive filepath from that
        archive["filepath"] = join(build_path, pathinfo.winfile(archive))
        found.append(archive)

    return found


def gather_latest_image_archives(session, tagname, path=None):

    pathinfo = PathInfo(path or "")

    found = []

    builds = session.getLatestBuilds(tagname, type="image")
    for bld in builds:
        build_path = pathinfo.imagebuild(bld)
        archives = session.listArchives(buildID=bld["id"], type="image")
        for archive in archives:
            archive["filepath"] = join(build_path, archive["filename"])
        found.extend(archives)

    return found


def gather_latest_archives(session, tagname, btype,
                           rpmkeys=(), path=None):

    taginfo = session.getTag(tagname)
    if not taginfo:
        raise NoSuchTag(tagname)

    known_types = ("rpm", "maven", "win", "image")
    found = []

    # the known types have additional metadata when queried, and have
    # pre-defined path structures. We'll be querying those directly
    # first.

    if btype in (None, "rpm"):
        found.extend(gather_latest_rpms(session, tagname, rpmkeys, path))

    if btype in (None, "maven"):
        found.extend(gather_latest_maven_archives(session, tagname, path))

    if btype in (None, "win"):
        found.extend(gather_latest_win_archives(session, tagname, path))

    if btype in (None, "image"):
        found.extend(gather_latest_image_archives(session, tagname, path))

    if btype in known_types:
        return found

    pathinfo = PathInfo(path or "")

    if btype is None:
        # listTaggedArchives is very convenient, but only works with
        # win, maven, and None
        archives, builds = session.listTaggedArchives(tagname,
                                                      inherit=True,
                                                      latest=True,
                                                      type=None)

        # convert builds to an id:binfo mapping
        builds = dict((bld["id"], bld) for bld in builds)

        for archive in archives:
            abtype = archive["btype"]
            if abtype in known_types:
                # filter out any of the types we would have queried on
                # their own earlier. Unfortunately there doesn't seem
                # to be a way to get around throwing away this
                # duplicate data for cases where btype is None
                continue

            # determine the path specific to this build and the
            # discovered archive btype
            bld = builds[archive["build_id"]]
            build_path = pathinfo.typedir(bld, abtype)

            # build an archive filepath from that
            archive["filepath"] = join(build_path, archive["filename"])
            found.append(archive)

    else:
        # btype is not one of the known ones, and it's also not None.
        builds = session.getLatestBuilds(tagname, type=btype)
        for bld in builds:
            build_path = pathinfo.typedir(bld, btype)
            archives = session.listArchives(buildID=bld["id"], type=btype)
            for archive in archives:
                archive["filepath"] = join(build_path, archive["filename"])
            found.extend(archives)

    return found


#
# The end.
