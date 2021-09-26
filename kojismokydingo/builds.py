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
Koji Smoky Dingo - Build Utilities

Functions for working with Koji builds

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from itertools import chain, repeat
from koji import ClientSession
from operator import itemgetter
from typing import (
    Any, Callable, Dict, Generator, Iterable, Iterator,
    List, Optional, Set, Tuple, Union, cast, )


from . import (
    NoSuchBuild, NoSuchTag,
    as_buildinfo, as_taginfo,
    bulk_load, bulk_load_build_archives, bulk_load_build_rpms,
    bulk_load_builds, bulk_load_buildroots,
    bulk_load_buildroot_archives, bulk_load_buildroot_rpms,
    bulk_load_rpm_sigs, bulk_load_tasks, iter_bulk_load, )
from .common import (
    chunkseq, merge_extend, unique, update_extend, )
from .rpm import evr_compare
from .types import (
    BuildInfo, BuildInfos, BuildState, DecoratedBuildInfo,
    DecoratedBuildInfos, TagSpec, )


__all__ = (
    "BuildFilter",
    "BuildNEVRCompare",
    "NEVRCompare",

    "build_dedup",
    "build_id_sort",
    "build_nvr_sort",
    "bulk_move_builds",
    "bulk_move_nvrs",
    "bulk_tag_builds",
    "bulk_tag_nvrs",
    "bulk_untag_builds",
    "bulk_untag_nvrs",
    "decorate_builds_btypes",
    "decorate_builds_cg_list",
    "decorate_builds_maven",
    "filter_builds_by_state",
    "filter_builds_by_tags",
    "filter_imported_builds",
    "gather_buildroots",
    "gather_rpm_sigkeys",
    "gather_component_build_ids",
    "gather_wrapped_builds",
    "gavgetter",
    "iter_bulk_move_builds",
    "iter_bulk_tag_builds",
    "iter_bulk_untag_builds",
    "iter_latest_maven_builds",
    "latest_maven_builds",
)


class NEVRCompare():
    """
    A comparison for RPM-style Name, Epoch, Version, Release
    sorting. Used by the `nvr_sort` function.
    """

    n: str
    evr: Tuple[str, str, str]


    def __init__(self, name: str,
                 epoch: Optional[str],
                 version: Optional[str],
                 release: Optional[str]):

        self.n = name

        # just to make sure
        self.evr = ("0" if epoch is None else str(epoch),
                    "0" if version is None else str(version),
                    "0" if release is None else str(release))


    def __cmp__(self, other):
        if self.n == other.n:
            return evr_compare(self.evr, other.evr)

        elif self.n < other.n:
            return -1

        else:
            return 1


    def __eq__(self, other):
        return self.__cmp__(other) == 0


    def __ne__(self, other):
        return self.__cmp__(other) != 0


    def __lt__(self, other):
        return self.__cmp__(other) < 0


    def __le__(self, other):
        return self.__cmp__(other) <= 0


    def __gt__(self, other):
        return self.__cmp__(other) > 0


    def __ge__(self, other):
        return self.__cmp__(other) >= 0


class BuildNEVRCompare(NEVRCompare):
    """
    An adapter for RPM-style Name, Epoch, Version, Release comparisons
    of a build info dictionary. Used by the `build_nvr_sort` function.
    """

    build: BuildInfo


    def __init__(self, binfo: BuildInfo):
        self.build = binfo
        super().__init__(binfo["name"],
                         binfo["epoch"], binfo["version"], binfo["release"])


def build_nvr_sort(
        build_infos: BuildInfos,
        dedup: bool = True,
        reverse: bool = False) -> List[BuildInfo]:
    """
    Given a sequence of build info dictionaries, sort them by Name,
    Epoch, Version, and Release using RPM's variation of comparison

    If dedup is True (the default), then duplicate NVRs will be
    omitted.

    All None infos will be dropped.

    :param build_infos: build infos to be sorted and de-duplicated

    :param dedup: remove duplicate entries. Default, True

    :param reverse: reverse the sorting. Default, False
    """

    build_infos = filter(None, build_infos)

    if dedup:
        build_infos = unique(build_infos, key="id")

    return sorted(build_infos, key=BuildNEVRCompare, reverse=reverse)


def build_id_sort(
        build_infos: BuildInfos,
        dedup: bool = True,
        reverse: bool = False) -> List[BuildInfo]:
    """
    Given a sequence of build info dictionaries, return a de-duplicated
    list of same, sorted by the build ID

    All None infos will be dropped.

    :param build_infos: build infos to be sorted and de-duplicated

    :param dedup: remove duplicate entries. Default, True

    :param reverse: reverse the sorting. Default, False
    """

    build_infos = filter(None, build_infos)

    if dedup:
        build_infos = unique(build_infos, key="id")

    return sorted(build_infos, key=itemgetter("id"), reverse=reverse)


def build_dedup(
        build_infos: BuildInfos) -> List[BuildInfo]:
    """
    Given a sequence of build info dictionaries, return a de-duplicated
    list of same, with order preserved.

    All None infos will be dropped.

    :param build_infos: build infos to be de-duplicated.
    """

    return unique(filter(None, build_infos), key="id")


def iter_bulk_move_builds(
        session: ClientSession,
        srctag: TagSpec,
        dsttag: TagSpec,
        build_infos: BuildInfos,
        force: bool = False,
        notify: bool = False,
        size: int = 100,
        strict: bool = False) -> Iterator[List[Tuple[BuildInfo, Any]]]:
    """
    Moves a large number of builds from one tag to another using
    multicall invocations of tagBuildBypass and untagBuildBypass.
    Builds are specified by build info dicts.

    yields lists of tuples containing a build info dict and either
    None if tagging/untagging was successful, or a fault dict if the
    tagging or untagging failed. This gives the caller a chance to
    record the results of each multicall and to present feedback to a
    user to indicate that the operations are continuing.

    :param session: an active koji session

    :param srctag: Source tag's name or ID. Builds will be removed
      from this tag.

    :param dsttag: Destination tag's name or ID. Builds will be added
      to this tag.

    :param build_infos: Build infos to be tagged

    :param force: Force tagging/untagging. Re-tags if necessary, bypasses
        policy. Default, False

    :param notify: Send tagging/untagging notifications. Default, False

    :param size: Count of tagging operations to perform in a single
        multicall. Default, 100

    :param strict: Raise an exception and discontinue execution at the
        first error. Default, False

    :raises NoSuchTag: If either the source or destination tag do not
      exist
    """

    srctag = as_taginfo(session, srctag)
    dsttag = as_taginfo(session, dsttag)

    stagid = srctag["id"]
    dtagid = dsttag["id"]

    if strict:
        for build_chunk in chunkseq(build_infos, size):
            session.multicall = True
            for build in build_chunk:
                bid = build["id"]
                session.tagBuildBypass(stagid, bid, force, notify)
                session.untagBuildBypass(dtagid, bid, force, notify)
            session.multiCall(strict=True)
        yield list(zip(build_infos, repeat(None)))

    else:
        for chunk in iter_bulk_tag_builds(session, dsttag, build_infos,
                                          force=force, notify=notify,
                                          size=size, strict=False):

            results: List[Tuple[BuildInfo, Any]] = []
            good = []

            for bld, res in chunk:
                if res and "faultCode" in res:
                    results.append((bld, res))  # type: ignore
                else:
                    good.append(bld)

            # join the initial tagging failure results with the
            # results of untagging the successfully tagged builds
            results.extend(bulk_untag_builds(session, srctag, good,
                                             force=force, notify=notify,
                                             size=size, strict=False))

            yield results


def bulk_move_builds(
        session: ClientSession,
        srctag: TagSpec,
        dsttag: TagSpec,
        build_infos: BuildInfos,
        force: bool = False,
        notify: bool = False,
        size: int = 100,
        strict: bool = False) -> List[Tuple[BuildInfo, Any]]:
    """
    Move a large number of builds using multicalls of tagBuildBypass and
    untagBuildBypass.

    :param session: an active koji session

    :param srctag: Source tag's name or ID. Builds will be removed
      from this tag.

    :param dsttag: Destination tag's name or ID. Builds will be added
      to this tag.

    :param build_infos: Build infos to be tagged

    :param force: Force tagging/untagging. Re-tags if necessary, bypasses
        policy. Default, False

    :param notify: Send tagging/untagging notifications. Default, False

    :param size: Count of tagging operations to perform in a single
        multicall. Default, 100

    :param strict: Raise an exception and discontinue execution at the
        first error. Default, False
    """

    results = []
    for done in iter_bulk_move_builds(session, srctag, dsttag, build_infos,
                                      force=force, notify=notify,
                                      size=size, strict=strict):
        results.extend(done)
    return results


def bulk_move_nvrs(
        session: ClientSession,
        srctag: TagSpec,
        dsttag: TagSpec,
        nvrs: Iterable[Union[int, str]],
        force: bool = False,
        notify: bool = False,
        size: int = 100,
        strict: bool = False) -> List[Tuple[BuildInfo, Any]]:
    """
    Move a large number of NVRs using multicalls of tagBuildBypass and
    untagBuildBypass.

    NVRs will be resolved to builds. If strict is True then any
    missing builds will result in a NoSuchBuild exception being
    raised. Otherwise missing builds will be ignored.

    :param session: an active koji session

    :param srctag: Source tag's name or ID. Builds will be removed
      from this tag.

    :param dsttag: Destination tag's name or ID. Builds will be added
      to this tag.

    :param nvrs: Builds to be tagged, specified by NVR or build ID

    :param force: Force tagging/untagging. Re-tags if necessary, bypasses
        policy. Default, False

    :param notify: Send tagging/untagging notifications. Default, False

    :param size: Count of tagging operations to perform in a single
        multicall. Default, 100

    :param strict: Raise an exception and discontinue execution at the
        first error. Default, False
    """

    loaded = bulk_load_builds(session, unique(nvrs), err=strict)
    builds = build_dedup(loaded.values())

    return bulk_move_builds(session, srctag, dsttag, builds,
                            force=force, notify=notify,
                            size=size, strict=strict)


def iter_bulk_tag_builds(
        session: ClientSession,
        tag: TagSpec,
        build_infos: BuildInfos,
        force: bool = False,
        notify: bool = False,
        size: int = 100,
        strict: bool = False) -> Iterator[List[Tuple[BuildInfo, Any]]]:
    """
    Tags a large number of builds using multicall invocations of
    tagBuildBypass. Builds are specified by build info dicts.

    yields lists of tuples containing a build info dict and the result
    of the tagBuildBypass call for that build. This gives the caller a
    chance to record the results of each multicall, and to present
    feedback to a user to indicate that the operations are continuing.

    :param session: an active koji session

    :param tag: Destination tag's name or ID

    :param build_infos: Build infos to be tagged

    :param force: Force tagging. Re-tags if necessary, bypasses
        policy. Default, False

    :param notify: Send tagging notifications. Default, False

    :param size: Count of tagging operations to perform in a single
        multicall. Default, 100

    :param strict: Raise an exception and discontinue execution at the
        first error. Default, False

    :raises NoSuchTag: If tag does not exist
    """

    tag = as_taginfo(session, tag)
    tagid = tag["id"]

    for build_chunk in chunkseq(build_infos, size):
        session.multicall = True
        for build in build_chunk:
            session.tagBuildBypass(tagid, build["id"], force, notify)
        results = session.multiCall(strict=strict)
        yield list(zip(build_chunk, results))


def bulk_tag_builds(
        session: ClientSession,
        tag: TagSpec,
        build_infos: BuildInfos,
        force: bool = False,
        notify: bool = False,
        size: int = 100,
        strict: bool = False) -> List[Tuple[BuildInfo, Any]]:
    """
    :param session: an active koji session

    :param tag: Destination tag's name or ID

    :param build_infos: Build infos to be tagged

    :param force: Force tagging. Re-tags if necessary, bypasses
      policy. Default, False

    :param notify: Send tagging notifications. Default, False

    :param size: Count of tagging operations to perform in a single
      multicall. Default, 100

    :param strict: Raise an exception and discontinue execution at the
      first error. Default, False

    :raises NoSuchTag: If tag does not exist
    """

    results = []
    for done in iter_bulk_tag_builds(session, tag, build_infos,
                                     force=force, notify=notify,
                                     size=size, strict=strict):
        results.extend(done)
    return results


def bulk_tag_nvrs(
        session: ClientSession,
        tag: TagSpec,
        nvrs: Iterable[Union[int, str]],
        force: bool = False,
        notify: bool = False,
        size: int = 100,
        strict: bool = False) -> List[Tuple[BuildInfo, Any]]:
    """
    Tags a large number of builds using multicall invocations of
    tagBuildBypass.

    The entire list of NVRs is validated first, checking that such a
    build exists. If strict is True then a missing build will cause a
    NoSuchBuild exception to be raised. If strict is False, then
    missing builds will be omitted from the tagging operation.

    The list of builds is de-duplicated, preserving order of the first
    instance found in the list of NVRs.

    Returns a list of tuples, pairing build info dicts with the result
    of a tagBuildBypass call for that build.

    :param session: an active koji session

    :param tag: Destination tag's name or ID

    :param nvrs: list of NVRs

    :param force: Bypass policy, retag if necessary. Default, follow
      policy and do not re-tag.

    :param notify: Start tagNotification tasks to send a notification
      email for every tagging event. Default, do not send
      notifications.  Warning, sending hundreds or thousands of
      tagNotification tasks can be overwhelming for the hub and may
      impact the system.

    :param size: Count of tagging calls to make per multicall
      chunk. Default is 100

    :param strict: Stop at the first failure. Default, continue after
      any failures. Errors will be available in the return results.

    :raises NoSuchBuild: If strict and an NVR does not exist

    :raises NoSuchTag: If tag does not exist

    :raises koji.GenericError: If strict and a tag policy prevents
      tagging
    """

    loaded = bulk_load_builds(session, unique(nvrs), err=strict)
    builds = build_dedup(loaded.values())

    return bulk_tag_builds(session, tag, builds,
                           force=force, notify=notify,
                           size=size, strict=strict)


def iter_bulk_untag_builds(
        session: ClientSession,
        tag: TagSpec,
        build_infos: BuildInfos,
        force: bool = False,
        notify: bool = False,
        size: int = 100,
        strict: bool = False) -> Iterator[List[Tuple[BuildInfo, Any]]]:
    """
    Untags a large number of builds using multicall invocations of
    untagBuildBypass. Builds are specified by build info dicts.

    yields lists of tuples containing a build info dict and the result
    of the untagBuildBypass call for that build. This gives the caller
    a chance to record the results of each multicall, and to present
    feedback to a user to indicate that the operations are continuing.

    :param session: an active koji session

    :param tag: Tag's name or ID

    :param build_infos: Build infos to be untagged

    :param force: Force untagging, bypasses policy. Default, False

    :param notify: Send untagging notifications. Default, False

    :param size: Count of untagging operations to perform in a single
        multicall. Default, 100

    :param strict: Raise an exception and discontinue execution at the
        first error. Default, False

    :raises NoSuchTag: If tag does not exist
    """

    tag = as_taginfo(session, tag)
    tagid = tag["id"]

    for build_chunk in chunkseq(build_infos, size):
        session.multicall = True
        for build in build_chunk:
            session.untagBuildBypass(tagid, build["id"], force, notify)
        results = session.multiCall(strict=strict)
        yield list(zip(build_chunk, results))


def bulk_untag_builds(
        session: ClientSession,
        tag: TagSpec,
        build_infos: BuildInfos,
        force: bool = False,
        notify: bool = False,
        size: int = 100,
        strict: bool = False) -> List[Tuple[BuildInfo, Any]]:
    """
    :param session: an active koji session

    :param tag: Destination tag's name or ID

    :param build_infos: Build infos to be untagged

    :param force: Force untagging. Bypasses policy. Default, False

    :param notify: Send untagging notifications. Default, False

    :param size: Count of untagging operations to perform in a single
      multicall. Default, 100

    :param strict: Raise an exception and discontinue execution at the
      first error. Default, False

    :raises NoSuchTag: If tag does not exist
    """

    results = []
    for done in iter_bulk_untag_builds(session, tag, build_infos,
                                       force=force, notify=notify,
                                       size=size, strict=strict):
        results.extend(done)
    return results


def bulk_untag_nvrs(
        session: ClientSession,
        tag: TagSpec,
        nvrs: Iterable[Union[int, str]],
        force: bool = False,
        notify: bool = False,
        size: int = 100,
        strict: bool = False) -> List[Tuple[BuildInfo, Any]]:
    """
    Untags a large number of builds using multicall invocations of
    untagBuildBypass.

    The entire list of NVRs is validated first, checking that such a
    build exists. If strict is True then a missing build will cause a
    NoSuchBuild exception to be raised. If strict is False, then
    missing builds will be omitted from the untagging operation.

    The list of builds is de-duplicated, preserving order of the first
    instance found in the list of NVRs.

    Returns a list of tuples, pairing build info dicts with the result
    of an untagBuildBypass call for that build.

    :param session: an active koji session

    :param tag: Tag's name or ID

    :param nvrs: list of NVRs

    :param force: Bypass policy checks

    :param notify: Start tagNotification tasks to send a notification
      email for every untagging event. Default, do not send
      notifications.  Warning, sending hundreds or thousands of
      tagNotification tasks can be overwhelming for the hub and may
      impact the system.

    :param size: Count of untagging calls to make per multicall
      chunk. Default is 100

    :param strict: Stop at the first failure. Default, continue after
      any failures. Errors will be available in the return results.

    :raises NoSuchBuild: If strict and an NVR does not exist

    :raises NoSuchTag: If tag does not exist

    :raises koji.GenericError: If strict and a tag policy prevents
      untagging
    """

    loaded = bulk_load_builds(session, unique(nvrs), err=strict)
    builds = build_dedup(loaded.values())

    return bulk_untag_builds(session, tag, builds,
                             force=force, notify=notify,
                             size=size, strict=strict)


gavgetter = itemgetter("maven_group_id", "maven_artifact_id",
                       "maven_version")


GAV = Tuple[str, str, str]


def iter_latest_maven_builds(
        session: ClientSession,
        tag: TagSpec,
        pkg_names: Optional[Iterable[str]] = None,
        inherit: bool = True) -> Iterator[Tuple[GAV, BuildInfo]]:
    """
    Yields ``((G, A, V), build_info)`` representing the latest build for
    each GAV in the tag.

    If pkg_names is given, then only those builds matching the given
    package names are yielded.

    :param session: an active koji client session

    :param tag: the tag to load latest maven builds from

    :param pkg_names: optional filter for build with the given package name

    :param inherit: if True also yield information for builds in the
      tag's parents

    :raises NoSuchTag: if tag could not be resolved
    """

    taginfo = as_taginfo(session, tag)
    tid = taginfo["id"]

    if pkg_names is None:
        # pkgs = session.listPackages(tid, inherited=True)
        # pkg_names = [p['package_name'] for p in pkgs if not p['blocked']]
        pkg_names = [None]
    else:
        pkg_names = unique(pkg_names)

    latest = set()

    fn = lambda p: session.listTagged(tid, inherit=inherit,
                                      package=p, type="maven")

    for pkg, builds in iter_bulk_load(session, fn, pkg_names):
        for bld in builds:
            gav = gavgetter(bld)
            if gav not in latest:
                latest.add(gav)
                yield gav, bld


def latest_maven_builds(
        session: ClientSession,
        tag: TagSpec,
        pkg_names: Optional[Iterable[str]] = None,
        inherit: bool = True) -> Dict[GAV, BuildInfo]:
    """
    Returns a dict mapping each (G, A, V) to a build_info dict,
    representing the latest build for each GAV in the tag.

    If pkg_names is given, then only those builds matching the given
    package names are returned.

    :param session: an active koji client session

    :param tag: the tag to load latest maven builds from

    :param pkg_names: optional filter for build with the given package name

    :param inherit: if True also yield information for builds in the
      tag's parents

    :raises NoSuchTag: if tag could not be resolved
    """

    builds = iter_latest_maven_builds(session, tag, pkg_names, inherit)
    return dict(builds)


def decorate_builds_maven(
        session: ClientSession,
        build_infos: BuildInfos) -> List[DecoratedBuildInfo]:
    """
    For any build info which does not have a maven_group_id and hasn't
    already been checked for additional btype data, augment the btype
    data.

    :param session: an active koji client session

    :param build_infos: build info dicts to decorate with maven GAV
      info
    """

    if not isinstance(build_infos, list):
        build_infos = list(build_infos)

    wanted = tuple(bld for bld in build_infos if
                   ("maven_group_id" not in bld))

    if wanted:
        return decorate_builds_btypes(session, wanted, with_fields=True)
    else:
        return cast(List[DecoratedBuildInfo], build_infos)


def decorate_builds_btypes(
        session: ClientSession,
        build_infos: BuildInfos,
        with_fields: bool = True) -> List[DecoratedBuildInfo]:
    """
    Augments a list of build_info dicts with two new keys:

    * archive_btype_ids is a list of BType IDs for the build

    * archive_btype_names is a list of BType names for the build

    Returns a tuple of the original input of build_infos. Any
    build_infos which had not been previously decorated will be
    mutated with their new keys.

    If with_fields is True (the default) then any special btype fields
    will be merged into the build info dict as well.

    :param session: an active koji session

    :param build_infos: list of build infos to decorate and return

    :param with_fields: also decorate btype-specific fields. Default,
      True
    """

    build_infos = cast(List[DecoratedBuildInfo], build_infos)

    if not isinstance(build_infos, list):
        build_infos = list(build_infos)

    wanted = {bld["id"]: bld for bld in build_infos if
              "archive_btype_names" not in bld}

    if not wanted:
        return build_infos

    btypes = {bt["name"]: bt["id"] for bt in session.listBTypes()}

    for bid, bts in iter_bulk_load(session, session.getBuildType, wanted):
        bld: DecoratedBuildInfo = wanted[bid]

        bld["archive_btype_names"] = btype_names = list(bts)
        bld["archive_btype_ids"] = [btypes[b] for b in btype_names]

        if not with_fields:
            continue

        for btn, data in bts.items():
            if not data:
                continue

            if btn == "win":
                # the win field doesn't get prefixed with "win_"
                bld["platform"] = data["platform"]
            else:
                # everything else gets prefixed with its type name and
                # an underscore
                if "build_id" in data:
                    del data["build_id"]
                for key, val in data.items():
                    bld["_".join((btn, key))] = val  # type: ignore

    return build_infos


def decorate_builds_cg_list(
        session: ClientSession,
        build_infos: BuildInfos) -> List[DecoratedBuildInfo]:
    """
    Augments a list of build_info dicts with two or four new keys:

    * archive_cg_ids is a list of content generator IDs for each
      archive of the build

    * archive_cg_names is a list of content generator names for each
      archive of the build

    Returns a tuple of the original input of build_infos. Any
    build_infos which had not been previously decorated will be
    mutated with their new keys.

    :param session: an active koji client session

    :param build_infos: list of build infos to decorate and return
    """

    # some of the facets we might consider as a property of the build
    # are in fact stored as properties of the artifacts or of the
    # artifacts' buildroot entries. This means that we have to dig
    # fairly deep to be able to answer simple questions like "what CGs
    # produced this build," or "what are the BTypes of this build?" So
    # we have this decorating utility to find the underlying values
    # and store them back on the build directly. We try to optimize
    # the decoration process such that it as polite to koji as
    # possible while farming all the data, and we also make it so that
    # we do not re-decorate builds which have already been decorated.
    build_infos = cast(List[DecoratedBuildInfo], build_infos)

    if not isinstance(build_infos, list):
        build_infos = list(build_infos)

    wanted = {bld["id"]: bld for bld in build_infos if
              "archive_cg_names" not in bld}

    if not wanted:
        return build_infos

    # multicall to fetch the artifacts and rpms for all build IDs that
    # need decorating
    archives = bulk_load_build_archives(session, wanted)
    rpms = bulk_load_build_rpms(session, wanted)

    # gather all the buildroot IDs, based on both the archives and
    # RPMs of the build.
    root_ids = set()
    for archive_list in archives.values():
        for archive in archive_list:
            broot_id = archive.get("buildroot_id")
            if broot_id:
                # do NOT allow None or 0
                root_ids.add(broot_id)

    for rpm_list in rpms.values():
        for rpm in rpm_list:
            broot_id = rpm.get("buildroot_id")
            if broot_id:
                # do NOT allow None or 0
                root_ids.add(broot_id)

    # multicall to fetch all the buildroots
    buildroots = bulk_load_buildroots(session, root_ids)

    for build_id, archive_list in archives.items():
        bld: DecoratedBuildInfo = wanted[build_id]

        cg_ids: List[int] = []
        cg_names: List[str] = []

        for archive in archive_list:
            broot_id = archive["buildroot_id"]
            if not broot_id:
                # no buildroot, thus no CG info, skip
                continue

            # The CG info is stored on the archive's buildroot, so
            # let's correlate back to a buildroot info from the
            # archive's buildroot_id
            broot = buildroots[broot_id]

            cg_id = broot.get("cg_id")
            if cg_id:
                cg_ids.append(cg_id)

            cg_name = broot.get("cg_name")
            if cg_name:
                cg_names.append(cg_name)

        bld["archive_cg_ids"] = unique(cg_ids)
        bld["archive_cg_names"] = unique(cg_names)

    for build_id, rpm_list in rpms.items():
        if not rpm_list:
            continue

        bld = wanted[build_id]
        cg_ids = bld["archive_cg_ids"]
        cg_names = bld["archive_cg_names"]

        for rpm in rpm_list:
            broot_id = rpm["buildroot_id"]
            if not broot_id:
                # no buildroot, thus no CG info, skip
                continue

            # The CG info is stored on the archive's buildroot, so
            # let's correlate back to a buildroot info from the
            # archive's buildroot_id
            broot = buildroots[broot_id]

            cg_id = broot.get("cg_id")
            if cg_id:
                cg_ids.append(cg_id)

            cg_name = broot.get("cg_name")
            if cg_name:
                cg_names.append(cg_name)

        bld["archive_cg_ids"] = unique(cg_ids)
        bld["archive_cg_names"] = unique(cg_names)

    return build_infos


def filter_builds_by_tags(
        session: ClientSession,
        build_infos: BuildInfos,
        limit_tag_ids: Iterable[int] = (),
        lookaside_tag_ids: Iterable[int] = ()) -> BuildInfos:
    """
    :param session: an active koji client session

    :param build_infos: build infos to filter through

    :param limit_tag_ids: tag IDs that builds must be tagged with to
      pass. Default, do not limit to any tag membership.

    :param lookaside_tag_ids: tag IDs that builds must not be tagged
      with to pass. Default, do not filter against any tag membership.
    """

    limit = set(limit_tag_ids) if limit_tag_ids else None
    lookaside = set(lookaside_tag_ids) if lookaside_tag_ids else None

    if not (limit or lookaside):
        return build_infos

    # a build ID: build_info mapping that we'll use to trim out
    # mismatches
    builds = {b["id"]: b for b in build_infos}

    # for each build ID, load the list of tags for that build
    fn = lambda i: session.listTags(build=i)
    build_tags = bulk_load(session, fn, builds)

    for bid, tags in build_tags.items():
        # convert the list of tags into a set of tag IDs
        tags = set(t["id"] for t in tags)

        if limit and tags.isdisjoint(limit):
            # don't want it, limit was given and this is not tagged in
            # the limit
            builds.pop(bid)

        elif lookaside and not tags.isdisjoint(lookaside):
            # don't want it, it's in the lookaside
            builds.pop(bid)

    return builds.values()


def filter_builds_by_state(
        build_infos: BuildInfos,
        state: BuildState = BuildState.COMPLETE) -> BuildInfos:
    """
    Given a sequence of build info dicts, return a generator of those
    matching the given state.

    Typically only COMPLETE and DELETED will be encountered here, the
    rest will rarely result in a build info dict existing.

    If state is None then no filtering takes place

    :param build_infos: build infos to filter through

    :param state: state value to filter for. Default: only builds in
      the COMPLETE state are returned
    """

    if state is None:
        return build_infos
    else:
        return (b for b in build_infos if (b and b.get("state") == state))


def filter_imported_builds(
        build_infos: BuildInfos,
        by_cg: Iterable[str] = (),
        negate: bool = False) -> BuildInfos:
    """
    Given a sequence of build info dicts, yield those which are
    imports.

    build_infos may have been decorated by the
    `decorate_builds_cg_list` function. This provides an accurate
    listing of the content generators which have been used to import
    the build (if any). In the event that they have not been thus
    decorated, the cg filtering will rely on the cg_name setting on
    the build itself, which will only have been provided if the
    content generator reserved the build ahead of time.

    If by_cg is empty and negate is False, then only builds which are
    non-CG imports will be emitted.

    If by_cg is empty and negate is True, then only builds which are
    non-imports will be emitted (ie. those with a task).

    If by_cg is not empty and negate is False, then only builds which
    are CG imports from the listed CGs will be emitted.

    If by_cg is not empty and negate is True, then only builds which
    are CG imports but not from the listed CGs will be emitted.

    by_cg may contain the string "any" to indicate that it matches all
    content generators. "any" should not be used with negate=True,
    as this will always result in no matches.

    :param build_infos: build infos to filter through

    :param by_cg: Content generator names to filter for

    :param negate: whether to negate the test, Default False
    """

    by_cg = set(by_cg)
    any_cg = "any" in by_cg
    disjoint = by_cg.isdisjoint

    for build in build_infos:

        # either get the decorated archive cg names, or start a fresh
        # one based on the possible cg_name associated with this build
        build_cgs = set(build.get("archive_cg_names", ()))  # type: ignore
        cg_name: str = build.get("cg_name")
        if cg_name:
            build_cgs.add(cg_name)

        is_import = not build.get("task_id", None)

        if negate:
            if by_cg:
                # we wanted imports which are NOT from these CGs. The
                # case of "any" is weird here -- because that would
                # mean we're looking for CG imports, and only those
                # which aren't any... so nothing can match this.
                if not any_cg and build_cgs and disjoint(build_cgs):
                    yield build
            else:
                # we wanted non-imports
                if not is_import:
                    yield build

        elif is_import:
            if by_cg:
                # we wanted imports which are from these CGs
                if build_cgs and (any_cg or not disjoint(build_cgs)):
                    yield build

            else:
                # we wanted imports which are not from any CG
                if not build_cgs:
                    yield build


def gather_buildroots(
        session: ClientSession,
        build_ids: Iterable[int]) -> Dict[int, List[dict]]:
    """
    For each build ID given, produce the list of buildroots used to
    create it.

    :param session: an active koji session

    :param build_ids: build IDs to fetch buildroots for
    """

    # multicall to fetch the artifacts for all build IDs
    archives = merge_extend(bulk_load_build_archives(session, build_ids),
                            bulk_load_build_rpms(session, build_ids))

    # gather all the buildroot IDs
    root_ids = set()
    for archive_list in archives.values():
        for archive in archive_list:
            broot_id = archive["buildroot_id"]
            if broot_id:
                # do NOT allow None or 0
                root_ids.add(broot_id)

    # multicall to fetch all the buildroots
    buildroots = bulk_load_buildroots(session, root_ids)

    results: Dict[int, List[dict]] = {}

    for build_id, archive_list in archives.items():
        broots = unique(a["buildroot_id"] for a in archive_list
                        if a["buildroot_id"])
        results[build_id] = [buildroots[b] for b in broots]

    return results


def gather_rpm_sigkeys(
        session: ClientSession,
        build_ids: Iterable[int]) -> Dict[int, Set[str]]:
    """
    Given a sequence of build IDs, collect the available sigkeys for
    each rpm in each build.

    Returns a dict mapping the original build IDs to a set of the
    discovered sigkeys.

    :param session: an active koji session

    :param build_ids: IDs of builds to gather keys from
    """

    # first load a mapping of build_id: [RPMS]
    loaded = bulk_load_build_rpms(session, build_ids)

    # now load a mapping of rpm_id: [SIGS]
    rpmids = (rpm["id"] for rpm in chain(*loaded.values()))
    rpm_sigs = bulk_load_rpm_sigs(session, rpmids)

    results: Dict[int, Set[str]] = {}

    sigs: Set[str]

    # now just correlate the set of sigkeys back to each needed
    # cache entry
    for bid, rpms in loaded.items():
        sigs = results[bid] = set()
        for rpm in rpms:
            sigs.update((sig["sigkey"] for sig in rpm_sigs[rpm["id"]]))

    return results


def gather_wrapped_builds(
        session: ClientSession,
        task_ids: Iterable[int],
        results: Optional[dict] = None) -> Dict[int, BuildInfo]:
    """
    Given a list of task IDs, identify any which are wrapperRPM
    tasks. For each which is a wrapperRPM task, associate the task ID
    with the underlying wrapped build info from the request.

    :param session: an active koji session

    :param task_ids: task IDs to check

    :param results: optional results dict to store mapping of task_ids
      to build dict in. If not specified a new dict will be created
      and returned.
    """

    results = {} if results is None else results

    tasks = bulk_load_tasks(session, task_ids, request=True)

    for tid, task in tasks.items():
        if task["method"] == "wrapperRPM":
            results[tid] = task["request"][2]

    return results


def gather_component_build_ids(
        session: ClientSession,
        build_ids: Iterable[int],
        btypes: Optional[Iterable[str]] = None) -> Dict[int, List[int]]:
    """
    Given a sequence of build IDs, identify the IDs of the component
    builds used to produce them (installed in the buildroots of the
    archives of the original build IDs)

    Returns a dict mapping the original build IDs to a list of the
    discovered component build IDs.

    If btypes is None, then all component archive types will be
    considered. Otherwise, btypes may be a sequence of btype names and
    only component archives of those types will be considered.

    :param session: an active koji session

    :param build_ids: Build IDs to collect components for

    :param btypes: Component archive btype filter. Default, all types
    """

    # multicall to fetch the artifacts and RPMs for all build IDs
    archives = merge_extend(bulk_load_build_archives(session, build_ids),
                            bulk_load_build_rpms(session, build_ids))

    # gather all the buildroot IDs
    root_ids = set()
    for archive_list in archives.values():
        for archive in archive_list:
            broot_id = archive["buildroot_id"]
            if broot_id:
                # do NOT allow None or 0
                root_ids.add(broot_id)

    if not btypes or None in btypes:
        # in order to query all types, we need to explicitly query for
        # RPMs, and then archives of type None
        btypes = ("rpm", None)

    # dig up the component archives (pretending that RPMs are just
    # another archive type as usual) and map them to the buildroot ID.
    components: Dict[int, list] = {}
    more: Dict[int, list]

    for bt in btypes:
        if bt == "rpm":
            more = bulk_load_buildroot_rpms(session, root_ids)
        else:
            more = bulk_load_buildroot_archives(session, root_ids, btype=bt)
        update_extend(components, more)

    # now associate the components back with the original build IDs
    results = {}

    for build_id, archive_list in archives.items():
        cids: Set[int] = set()
        for archive in archive_list:
            broot_id = archive["buildroot_id"]
            carchives: Iterable[dict] = components.get(broot_id, ())
            cids.update(c["build_id"] for c in carchives)

        results[build_id] = list(cids)

    return results


class BuildFilter():

    def __init__(
            self,
            session: ClientSession,
            limit_tag_ids: Optional[Iterable[int]] = None,
            lookaside_tag_ids: Optional[Iterable[int]] = None,
            imported: Optional[bool] = None,
            cg_list: Optional[Iterable[str]] = None,
            btypes: Optional[Iterable[str]] = None,
            state: Optional[BuildState] = None):
        """
        :param session: an active koji client session

        :param limit_tag_ids: if specified, builds must be tagged with one
          of these tags

        :param lookaside_tag_ids: if specified, builds must not be tagged
          with any of these tags

        :param imported: if True, only imported builds are returned. If
          False, only unimported builds are returned. Default, does not
          test whether a build is imported or not.

        :param cg_list: If specified, only builds which are produced by
          the named content generators will be returned.

        :param btypes: Filter for the given build types, by name. Default,
          any build type is allowed.

        :param state: Filter by the given build state. Default, no
          filtering by state.
        """

        self._session = session

        self._limit_tag_ids = \
            set(limit_tag_ids) if limit_tag_ids else None

        self._lookaside_tag_ids = \
            set(lookaside_tag_ids) if lookaside_tag_ids else None

        self._imported = imported
        self._cg_list = set(cg_list)

        self._btypes = set(btypes or ())
        self._state = state


    def filter_by_tags(self, build_infos: BuildInfos) -> BuildInfos:
        limit = self._limit_tag_ids
        lookaside = self._lookaside_tag_ids

        if limit or lookaside:
            build_infos = filter_builds_by_tags(self._session, build_infos,
                                                limit_tag_ids=limit,
                                                lookaside_tag_ids=lookaside)
        return build_infos


    def filter_by_btype(self, build_infos: BuildInfos) -> BuildInfos:

        bt = self._btypes
        if not bt:
            return build_infos

        def test(b):
            btn = set(b.get("archive_btype_names", ()))
            return btn and not bt.isdisjoint(btn)

        build_infos = decorate_builds_btypes(self._session, build_infos)
        return filter(test, build_infos)


    def filter_imported(self, build_infos: BuildInfos) -> BuildInfos:
        if self._cg_list or self._imported is not None:
            negate = not (self._imported or self._imported is None)

            build_infos = decorate_builds_cg_list(self._session, build_infos)
            return filter_imported_builds(build_infos, self._cg_list, negate)

        else:
            return build_infos


    def filter_by_state(self, build_infos: BuildInfos) -> BuildInfos:
        if self._state is not None:
            build_infos = filter_builds_by_state(build_infos, self._state)

        return build_infos


    def __call__(self, build_infos: BuildInfos) -> BuildInfos:
        # TODO: could we add some caching to this, such that we
        # associate the build ID with a bool indicating whether it's
        # been filtered before and whether it was included (True) or
        # omitted (False).  That might allow us to cut down on the
        # overhead if filtering is used multiple times... However,
        # will filtering ever actually be used multiple times?

        # ensure this is a real list and not a generator of some sort
        work: BuildInfos = list(build_infos)

        work = self.filter_by_state(work)

        # first stage filtering, based on tag membership
        work = self.filter_by_tags(work)

        # filtering by btype (provided by decorated addtl data)
        work = self.filter_by_btype(work)

        # filtering by import or cg (provided by decorated addtl data)
        work = self.filter_imported(work)

        return work


#
# The end.
