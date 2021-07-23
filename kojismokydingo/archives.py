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
Functions for gathering and transforming Koji datastructures
representing RPMs and build archives

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from koji import ClientSession, PathInfo
from os.path import join
from typing import Iterable, Optional, Union

from . import as_buildinfo, as_taginfo, bulk_load_rpm_sigs
from .types import (
    ArchiveInfos, BuildInfo, DecoratedArchiveInfos, DecoratedRPMInfos,
    ImageArchiveInfos, MavenArchiveInfos, PathSpec, SignedRPMInfo,
    WindowsArchiveInfos, )


__all__ = (
    "as_pathinfo",
    "filter_archives",

    "gather_build_archives",
    "gather_build_image_archives",
    "gather_build_maven_archives",
    "gather_build_rpms",
    "gather_build_win_archives",

    "gather_latest_archives",
    "gather_latest_image_archives",
    "gather_latest_maven_archives",
    "gather_latest_rpms",
    "gather_latest_win_archives",

    "gather_signed_rpms",
)


def as_pathinfo(
        path: PathSpec) -> PathInfo:
    """
    Converts path into a PathInfo if it is not one already

    :param path: path basis for archives
    """

    if isinstance(path, PathInfo):
        return path
    else:
        return PathInfo(path or "")


def filter_archives(
        session: ClientSession,
        archives: ArchiveInfos,
        archive_types: Iterable[str] = (),
        arches: Iterable[str] = ()) -> ArchiveInfos:
    """
    Given a list of archives (or RPMs dressed up like archives),
    return a new list of those archives which are of the given archive
    types.

    :param archives: Archive infos to be filtered

    :param archive_types: Desired archive type extensions

    :param arches: Desired architectures
    """

    if not (archive_types or arches):
        return archives

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

    def filter_fn(a):
        return ((not atypes or a["type_id"] in atypes) and
                (not arches or a.get("arch", "noarch") in arches))

    return filter(filter_fn, archives)


def gather_signed_rpms(
        session: ClientSession,
        archives: ArchiveInfos,
        sigkeys: Iterable[str]) -> DecoratedRPMInfos:
    """
    Given a list of RPM archive dicts, query the session for all the
    pertinent signature headers, then try and find the best matching
    signed copy of each RPM. An empty string at the end of sigkeys
    will allow an unsigned copy to be included if no signed copies
    match.

    :param archives: list of RPM archive dicts

    :param sigkeys: list of signature fingerprints, in order of
      precedence
    """

    if not sigkeys:
        return archives

    results = []

    # an ID: RPM Archive mapping
    rpms = {rpm["id"]: rpm for rpm in archives}

    # now bulk load all the sigs for each RPM ID
    rpm_sigs = bulk_load_rpm_sigs(session, rpms)

    for rpm_id, rpm in rpms.items():
        found = set(sig["sigkey"] for sig in rpm_sigs[rpm_id])
        for wanted in sigkeys:
            if wanted in found:
                rpm["sigkey"] = wanted
                results.append(rpm)
                break

    return results


def gather_build_rpms(
        session: ClientSession,
        binfo: BuildInfo,
        rpmkeys: Iterable[str] = (),
        path: Optional[PathSpec] = None) -> DecoratedRPMInfos:
    """
    Gathers a list of rpm dicts matching the given signature keys from
    the specified build, and augments them with a filepath

    :param session: an active koji client session

    :param binfo: build to gather signed RPMs from

    :param rpmkeys: list of keys, in order of preference

    :param path: base path to prepend to the build RPM's new filepath
      value
    """

    binfo = as_buildinfo(session, binfo)
    bid = binfo["id"]
    path = as_pathinfo(path)

    build_path = path.build(binfo)
    found = session.listRPMs(buildID=bid)

    if rpmkeys:
        found = gather_signed_rpms(session, found, rpmkeys)

    for f in found:
        key = f["sigkey"] if rpmkeys else None
        rpmpath = path.signed(f, key) if key else path.rpm(f)
        f["filepath"] = join(build_path, rpmpath)

        # fake some archive members, since RPMs are missing these
        f["type_id"] = 0
        f["btype_id"] = 1
        f["type_name"] = f["btype"] = "rpm"

    return found


def gather_build_maven_archives(
        session: ClientSession,
        binfo: BuildInfo,
        path: Optional[PathSpec] = None) -> MavenArchiveInfos:
    """
    Gathers a list of maven archives for a given build_info. The
    archive records are augmented with an additional "filepath" entry,
    the value of which is an expanded path to the file itself.

    :param binfo: Build info to fetch archives for

    :param path: The root dir for the archive file paths, default None
    """

    binfo = as_buildinfo(session, binfo)
    bid = binfo["id"]
    path = as_pathinfo(path)

    build_path = path.mavenbuild(binfo)
    found = session.listArchives(buildID=bid, type="maven")
    for f in found:
        f["filepath"] = join(build_path, path.mavenfile(f))

    return found


def gather_build_win_archives(
        session: ClientSession,
        binfo: BuildInfo,
        path: Optional[PathSpec] = None) -> WindowsArchiveInfos:
    """
    Gathers a list of Windows archives for a given build_info. The
    archive records are augmented with an additional "filepath" entry,
    the value of which is an expanded path to the file itself.

    :param binfo: Build info to fetch archives for

    :param path: The root dir for the archive file paths, default None
    """

    binfo = as_buildinfo(session, binfo)
    bid = binfo["id"]
    path = as_pathinfo(path)

    build_path = path.winbuild(binfo)
    found = session.listArchives(buildID=bid, type="win")
    for f in found:
        f["filepath"] = join(build_path, path.winfile(f))

    return found


def gather_build_image_archives(
        session: ClientSession,
        binfo: BuildInfo,
        path: Optional[PathSpec] = None) -> ImageArchiveInfos:
    """
    Gathers a list of image archives for a given build_info. The
    archive records are augmented with an additional "filepath" entry,
    the value of which is an expanded path to the file itself.

    :param binfo: Build info to fetch archives for

    :param path: The root dir for the archive file paths, default None
    """

    binfo = as_buildinfo(session, binfo)
    bid = binfo["id"]
    path = as_pathinfo(path)

    build_path = path.imagebuild(binfo)
    found = session.listArchives(buildID=bid, type="image")
    for f in found:
        f["filepath"] = join(build_path, f["filename"])

    return found


def gather_build_archives(
        session: ClientSession,
        binfo: BuildInfo,
        btype: Optional[str] = None,
        rpmkeys: Iterable[str] = (),
        path: Optional[PathSpec] = None) -> DecoratedArchiveInfos:
    """
    Produce a list of archive dicts associated with a build info,
    optionally filtered by build-type and signing keys (for RPMs). The
    archives will be decorated with an additional "filepath" entry,
    the value of which is an expanded path to the file itself.

    This is very similar to the file listing that is baked into the
    koji buildinfo command.

    Koji does not normally consider RPMs to be archives, but we will
    attempt to homogenize them together.

    :param binfo: Build info to fetch archives for

    :param btype: BType to filter for. Default None for all types.

    :param rpmkeys: RPM signatures to filter for, in order of
        preference. An empty string matches the unsigned copy. Default
        () for no signature filtering.

    :param path: The root dir for the archive file paths, default None
    """

    binfo = as_buildinfo(session, binfo)

    known_types = ("rpm", "maven", "win", "image", )
    found = []

    # Check for a decorated list of build types. If not present, then
    # get it from koji directly. Having this allows us to avoid
    # querying koji for archives of a btype that the build doesn't
    # have.
    build_types = binfo.get("archive_btype_names", None)
    if build_types is None:
        build_types = set(session.getBuildType(binfo["id"]))

    if btype and btype not in build_types:
        # we already know we'll find nothing, so don't bother asking
        return found

    path = as_pathinfo(path)

    if btype in (None, "rpm") and "rpm" in build_types:
        found.extend(gather_build_rpms(session, binfo, rpmkeys, path))

    if btype in (None, "maven") and "maven" in build_types:
        found.extend(gather_build_maven_archives(session, binfo, path))

    if btype in (None, "win") and "win" in build_types:
        found.extend(gather_build_win_archives(session, binfo, path))

    if btype in (None, "image") and "image" in build_types:
        found.extend(gather_build_image_archives(session, binfo, path))

    if btype in known_types:
        return found

    bid = binfo["id"]

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

        build_path = path.typedir(binfo, abtype)
        f["filepath"] = join(build_path, f["filename"])

        found.append(f)

    return found


def gather_latest_rpms(
        session: ClientSession,
        tagname: str,
        rpmkeys: Iterable[str] = (),
        inherit: bool = True,
        path: Optional[PathSpec] = None) -> DecoratedArchiveInfos:
    """
    Similar to session.getLatestRPMS(tagname) but will filter by
    available signatures, and augments the results to include a new
    "filepath" entry which will point to the matching RPM file
    location.

    :param tagname: Name of the tag to search in for RPMs

    :param rpmkeys: RPM signatures to filter for, in order of
        preference. An empty string matches the unsigned copy. Default
        () for no signature filtering.

    :param inherit: Follow tag inheritance, default True

    :param path: The root dir for the archive file paths, default None
    """

    path = as_pathinfo(path)

    found, builds = session.getLatestRPMS(tagname)

    # decorate the build info with its path data
    for bld in builds:
        bld["build_path"] = path.build(bld)

    builds = {bld["id"]: bld for bld in builds}

    if rpmkeys:
        found = gather_signed_rpms(session, found, rpmkeys)

    for f in found:
        bld = builds[f["build_id"]]
        key = f["sigkey"] if rpmkeys else None
        rpmpath = path.signed(f, key) if key else path.rpm(f)
        f["filepath"] = join(bld["build_path"], rpmpath)

        # fake some archive members, since RPMs are missing these
        f["type_id"] = 0
        f["type_name"] = "rpm"

    return found


def _fake_maven_build(archive, path=None, btype="maven", cache={}):
    """
    produces something that looks like a build info dict based on the
    values from within a maven archive dict. This can then be used
    with a `koji.PathInfo` instance to determine the path to a build
    """

    bid = archive["build_id"]
    bld = cache.get(bid)

    if not bld:
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

        path = as_pathinfo(path)
        bld["build_path"] = path.typedir(bld, btype)

        cache[bid] = bld

    return bld


def gather_latest_maven_archives(
        session: ClientSession,
        tagname: str,
        inherit: bool = True,
        path: Optional[PathSpec] = None) -> MavenArchiveInfos:
    """
    Similar to session.getLatestMavenArchives(tagname) but augments
    the results to include a new "filepath" entry which will point to
    the matching maven artifact's file location.

    :param tagname: Name of the tag to search in for maven artifacts

    :param inherit: Follow tag inheritance, default True
    """

    path = as_pathinfo(path)

    found = session.getLatestMavenArchives(tagname, inherit=inherit)
    for f in found:
        # unlike getLatestRPMs, getLatestMavenArchives only provides
        # the archives themselves. We don't want to have to do a bulk
        # load for all those, so we fake a build info from the values
        # in the archive itself. Since we're only using it to
        # determine paths, the missing fields shouldn't be a problem
        bld = _fake_maven_build(f, path)
        f["filepath"] = join(bld["build_path"], path.mavenfile(f))

    return found


def gather_latest_win_archives(
        session: ClientSession,
        tagname: str,
        inherit: bool = True,
        path: Optional[PathSpec] = None) -> WindowsArchiveInfos:
    """
    Similar to session.listTaggedArchives(tagname, type="win") but
    augments the results to include a new "filepath" entry which will
    point to the matching maven artifact's file location.

    :param tagname: Name of the tag to search in for maven artifacts

    :param inherit: Follow tag inheritance, default True
    """

    path = as_pathinfo(path)

    found = []

    archives, builds = session.listTaggedArchives(tagname,
                                                  inherit=inherit,
                                                  latest=True,
                                                  type="win")

    # decorate the build infos with the type paths for windows
    for bld in builds:
        bld["build_path"] = path.winbuild(bld)

    # convert builds to an id:binfo mapping
    builds = {bld["id"]: bld for bld in builds}

    for archive in archives:
        bld = builds[archive["build_id"]]
        build_path = bld["build_path"]

        # build an archive filepath from that
        archive["filepath"] = join(build_path, path.winfile(archive))
        found.append(archive)

    return found


def gather_latest_image_archives(
        session: ClientSession,
        tagname: str,
        inherit: bool = True,
        path: Optional[PathSpec] = None) -> ImageArchiveInfos:
    """
    :param inherit: Follow tag inheritance, default True
    """

    path = as_pathinfo(path)

    found = []

    # we cannot use listTaggedArchives here, because it only accepts types
    # of win and maven. I should submit a patch to upstream.

    if inherit:
        builds = session.getLatestBuilds(tagname, type="image")
    else:
        builds = session.listTagged(tagname, latest=True, type="image")

    for bld in builds:
        build_path = path.imagebuild(bld)
        archives = session.listArchives(buildID=bld["id"], type="image")
        for archive in archives:
            archive["filepath"] = join(build_path, archive["filename"])
        found.extend(archives)

    return found


def gather_latest_archives(
        session: ClientSession,
        tagname: str,
        btype: Optional[str] = None,
        rpmkeys: Iterable[str] = (),
        inherit: bool = True,
        path: Optional[PathSpec] = None) -> ArchiveInfos:
    """
    Gather the latest archives from a tag heirarchy. Rules for what
    constitutes "latest" may change slightly depending on the archive
    types -- specifically maven.

    :param session: an active koji client session

    :param tagname: Name of the tag to gather archives from

    :param btype: Name of the BType to gather. Default, gather all

    :param rpmkeys: List of RPM signatures to filter by. Only used when
        fetching type of rpm or None (all).

    :param inherit: Follow tag inheritance, default True

    :param path: Path prefix for archive filepaths.

    :raises NoSuchTag: if specified tag doesn't exist
    """

    # we'll cheat a bit and use as_taginfo to verify that the tag
    # exists -- it will raise a NoSuchTag for us if necessary. We
    # aren't doing any such checking in the lower-level per-type
    # gather functions.
    taginfo = as_taginfo(session, tagname)
    tagname = taginfo["name"]

    known_types = ("rpm", "maven", "win", "image")
    found = []

    # the known types have additional metadata when queried, and have
    # pre-defined path structures. We'll be querying those directly
    # first.

    path = as_pathinfo(path)

    if btype in (None, "rpm"):
        found.extend(gather_latest_rpms(session, tagname, rpmkeys,
                                        inherit, path))

    if btype in (None, "maven"):
        found.extend(gather_latest_maven_archives(session, tagname,
                                                  inherit, path))

    if btype in (None, "win"):
        found.extend(gather_latest_win_archives(session, tagname,
                                                inherit, path))

    if btype in (None, "image"):
        found.extend(gather_latest_image_archives(session, tagname,
                                                  inherit, path))

    if btype in known_types:
        return found

    if btype is None:
        # listTaggedArchives is very convenient, but only works with
        # win, maven, and None
        archives, builds = session.listTaggedArchives(tagname,
                                                      inherit=inherit,
                                                      latest=True,
                                                      type=None)

        # convert builds to an id:binfo mapping
        builds = {bld["id"]: bld for bld in builds}

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
            build_path = path.typedir(bld, abtype)

            # build an archive filepath from that
            archive["filepath"] = join(build_path, archive["filename"])
            found.append(archive)

    else:
        # btype is not one of the known ones, and it's also not None.
        if inherit:
            builds = session.getLatestBuilds(tagname, type=btype)
        else:
            builds = session.listTagged(tagname, latest=True, type=btype)

        for bld in builds:
            build_path = path.typedir(bld, btype)
            archives = session.listArchives(buildID=bld["id"], type=btype)
            for archive in archives:
                archive["filepath"] = join(build_path, archive["filename"])
            found.extend(archives)

    return found


#
# The end.
