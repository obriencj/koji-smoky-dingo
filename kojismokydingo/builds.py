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


from collections import OrderedDict
from six import iteritems, itervalues
from six.moves import filter

from . import (
    NoSuchBuild,
    bulk_load, bulk_load_build_archives, bulk_load_build_rpms,
    bulk_load_builds, bulk_load_buildroots)
from .common import chunkseq, rpm_evr_compare, unique, update_extend
from .tags import as_taginfo


def as_buildinfo(session, build):
    if isinstance(build, (str, int)):
        info = session.getBuild(build)
    elif isinstance(build, dict):
        info = build
    else:
        info = None

    if not info:
        raise NoSuchBuild(build)

    return info


class BuildNEVRCompare(object):
    """
    An adapter for Name, Epoch, Version, Release comparisons of a
    build info dictionary. Used by the nevr_sort_builds function.
    """

    def __init__(self, binfo):
        self.build = binfo
        self.n = binfo["name"]

        evr = (binfo["epoch"], binfo["version"], binfo["release"])
        self.evr = tuple(("0" if x is None else str(x)) for x in evr)


    def __cmp__(self, other):
        # cmp is a python2-ism, and has no replacement in python3 via
        # six, so we'll have to create our own simplistic behavior
        # similarly

        if self.n == other.n:
            return rpm_evr_compare(self.evr, other.evr)

        elif self.n < other.n:
            return -1

        else:
            return 1


    def __eq__(self, other):
        return self.__cmp__(other) == 0


    def __lt__(self, other):
        return self.__cmp__(other) < 0


    def __gt__(self, other):
        return self.__cmp__(other) > 0


def build_nvr_sort(build_infos, dedup=True):
    """
    Given a sequence of build info dictionaries, sort them by Name,
    Epoch, Version, and Release using RPM's variation of comparison

    If dedup is True (the default), then duplicate NVRs will be
    omitted.

    :param build_infos: build infos to be sorted and de-duplicated
    :type build_infos: list[dict]

    :param dedup: remove duplicate entries. Default, True
    :type dedup: bool, optional

    :rtype: list[dict]
    """

    if dedup:
        dd = dict((b["id"], b) for b in build_infos if b)
        build_infos = itervalues(dd)

    return sorted(build_infos, key=BuildNEVRCompare)


def build_id_sort(build_infos, dedup=True):
    """
    Given a sequence of build info dictionaries, return a de-duplicated
    list of same, sorted by the build ID

    :param build_infos: build infos to be sorted and de-duplicated
    :type build_infos: list[dict]

    :param dedup: remove duplicate entries. Default, True
    :type dedup: bool, optional

    :rtype: list[dict]
    """

    if dedup:
        builds = dict((b["id"], b) for b in build_infos if b)
        return [b for _bid, b in sorted(iteritems(builds))]
    else:
        return sorted(builds, key=lambda b: (b["id"], b))


def build_dedup(build_infos):
    """
    Given a sequence of build info dictionaries, return a de-duplicated
    list of same, with order preserved.

    :param build_infos: build infos to be de-duplicated.
    :type build_infos: list[dict]

    :rtype: list[dict]
    """

    dedup = OrderedDict((b["id"], b) for b in build_infos if b)
    return list(itervalues(dedup))


def iter_bulk_tag_builds(session, tag, build_infos,
                         force=False, notify=False,
                         size=100, strict=False):

    """
    Tags a large number of builds using multicall invocations of
    tagBuildBypass. Builds are specified by build info dicts.

    yields lists of tuples containing a build info dict and the result
    of the tagBuildBypass call for that build. This gives the caller a
    chance to record the results of each multicall, and to present
    feedback to a user to indicate that the operations are continuing.

    :param tag: Destination tag's name or ID

    :type tag: str or int

    :param build_infos: Build infos to be tagged

    :type build_infos: list[dict]

    :param force: Force tagging. Re-tags if necessary, bypasses
        policy. Default, False

    :type force: bool, optional

    :param notify: Send tagging notifications. Default, False

    :type notify: bool, optional

    :param size: Count of tagging operations to perform in a single
        multicall. Default, 100

    :type size: int, optional

    :param strict: Raise an exception and discontinue execution at the
        first error. Default, False

    :type strict: bool, optional

    :rtype: Generator[list[tuple]]

    :raises kojismokydingo.NoSuchTag: If tag does not exist
    """

    tag = as_taginfo(session, tag)
    tagid = tag["id"]

    for build_chunk in chunkseq(build_infos, size):
        session.multicall = True
        for build in build_chunk:
            session.tagBuildBypass(tagid, build["id"], force, notify)
        results = session.multiCall(strict=strict)
        yield list(zip(build_chunk, results))


def bulk_tag_builds(session, tag, build_infos,
                    force=False, notify=False,
                    size=100, strict=False):

    """
    :param session: an active koji session

    :type session: koji.ClientSession

    :param tag: Destination tag's name or ID

    :type tag: str or int

    :param build_infos: Build infos to be tagged

    :type build_infos: list[dict]

    :param force: Force tagging. Re-tags if necessary, bypasses
      policy. Default, False

    :type force: bool, optional

    :param notify: Send tagging notifications. Default, False

    :type notify: bool, optional

    :param size: Count of tagging operations to perform in a single
      multicall. Default, 100

    :type size: int, optional

    :param strict: Raise an exception and discontinue execution at the
      first error. Default, False

    :type strict: bool, optional

    :rtype: list[tuple]

    :raises kojismokydingo.NoSuchTag: If tag does not exist
    """

    results = []
    for done in iter_bulk_tag_builds(session, tag, build_infos,
                                     force=force, notify=notify,
                                     size=size, strict=strict):
        results.extend(done)
    return results


def bulk_tag_nvrs(session, tag, nvrs,
                  force=False, notify=False,
                  size=100, strict=False):

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

    :type session: koji.ClientSession

    :param tag: Destination tag's name or ID

    :type tag: str or int

    :param nvrs: list of NVRs

    :type nvrs: list[str]

    :param force: Bypass policy, retag if necessary. Default, follow
      policy and do not re-tag.

    :type force: bool, optional

    :param notify: Start tagNotification tasks to send a notification
      email for every tagging event. Default, do not send
      notifications.  Warning, sending hundreds or thousands of
      tagNotification tasks can be overwhelming for the hub and may
      impact the system.

    :type notify: bool, optional

    :param size: Count of tagging calls to make per multicall
      chunk. Default is 100

    :type size: int, optional

    :param strict: Stop at the first failure. Default, continue after
      any failures. Errors will be available in the return results.

    :type strict: bool, optional

    :raises kojismokydingo.NoSuchBuild: If strict and an NVR does not
      exist

    :raises kojismokydingo.NoSuchTag: If tag does not exist

    :raises koji.GenericError: If strict and a tag policy prevents
      tagging
    """

    builds = bulk_load_builds(session, unique(nvrs), err=strict)
    builds = build_dedup(itervalues(builds))

    return bulk_tag_builds(session, tag, builds,
                           force=force, notify=notify,
                           size=size, strict=strict)


def decorate_build_archive_data(session, build_infos, with_cg=False):
    """
    Augments a list of build_info dicts with four new keys:

    * archive_btype_ids is a set of btype IDs for each archive of the
      build

    * archive_btype_names is a set of btype names for each archive of
      the build

    * archive_cg_ids is a set of content generator IDs for each
      archive of the build if with_cg is True, or None if with_cg is
      False

    * archive_cg_names is a set of content generator names for each
      archive of the build if with_cg is True, or None if with_cg is
      False

    :param session: an active koji session

    :type session: koji.ClientSession

    :param build_infos: list of build infos to decorate and return

    :type build_infos: list[dict] or Iterator[dict]

    :param with_cg: load buildroot data for each archive of each build
      to determine the CG names and IDs. Default, does not load
      buildroot data.

    :type with_cg: bool, optional

    :rtype: Iterator[dict]
    """

    # convert build_infos into an id:info dict
    builds = OrderedDict((b["id"], b) for b in build_infos)

    # multicall to fetch the artifacts for all build IDs
    archives = bulk_load_build_archives(session, list(builds))
    rpms = bulk_load_build_rpms(session, list(builds))

    # gather all the buildroot IDs
    root_ids = set()
    for archive_list in itervalues(archives):
        for archive in archive_list:
            broot_id = archive.get("buildroot_id")
            if broot_id:
                # do NOT allow None or 0
                root_ids.add(broot_id)

    for rpm_list in itervalues(rpms):
        for rpm in rpm_list:
            broot_id = rpm.get("buildroot_id")
            if broot_id:
                # do NOT allow None or 0
                root_ids.add(broot_id)

    if with_cg:
        # multicall to fetch all the buildroots
        buildroots = bulk_load_buildroots(session, list(root_ids))
    else:
        # we aren't collecting CG information, so we don't actually
        # need any buildroots
        buildroots = None

    for build_id, archive_list in iteritems(archives):

        bld = builds[build_id]
        bld["archive_cg_ids"] = cg_ids = set() if with_cg else None
        bld["archive_cg_names"] = cg_names = set() if with_cg else None
        bld["archive_btype_ids"] = btype_ids = set()
        bld["archive_btype_names"] = btype_names = set()

        for archive in archive_list:
            # determine the build's BTypes from the archives
            btype_ids.add(archive["btype_id"])
            btype_names.add(archive["btype"])

            if not with_cg:
                # we don't want the CG info, so skip the rest
                continue

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
                cg_ids.add(cg_id)

            cg_name = broot.get("cg_name")
            if cg_name:
                cg_names.add(cg_name)

    for build_id, rpm_list in iteritems(rpms):
        if not rpm_list:
            continue

        bld = builds[build_id]
        cg_ids = bld["archive_cg_ids"]
        cg_names = bld["archive_cg_names"]

        btype_ids = bld["archive_btype_ids"]
        btype_ids.add(1)

        btype_names = bld["archive_btype_names"]
        btype_names.add("rpm")

        if not with_cg:
            continue

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
                cg_ids.add(cg_id)

            cg_name = broot.get("cg_name")
            if cg_name:
                cg_names.add(cg_name)

    return itervalues(builds)


def filter_by_tags(session, build_infos,
                   limit_tag_ids=(), lookaside_tag_ids=()):

    """
    :param build_infos: build infos to filter through
    :type build_infos: list[dict] or Iterator[dict]

    :param limit_tag_ids: tag IDs that builds must be tagged with to
      pass. Default, do not limit to any tag membership.
    :type limit_tag_ids: list[int]

    :param lookaside_tag_ids: tag IDs that builds must not be tagged with to
      pass. Default, do not filter against any tag membership.
    :type lookaside_tag_ids: list[int]

    :rtype: list[dict] or Iterator[dict]
    """

    if not (limit_tag_ids or lookaside_tag_ids):
        return build_infos

    limit = set(limit_tag_ids) if limit_tag_ids else None
    lookaside = set(lookaside_tag_ids) if lookaside_tag_ids else None

    # a build ID: build_info mapping that we'll use to trim out
    # mismatches
    builds = OrderedDict((b["id"], b) for b in build_infos)

    # for each build ID, load the list of tags for that build
    build_tags = bulk_load(session, session.listTags, list(builds))

    for bid, tags in iteritems(build_tags):
        # convert the list of tags into a set of tag IDs
        tags = set(t["id"] for t in tags)

        if limit and tags.isdisjoint(limit):
            # don't want it, limit was given and this is not tagged in
            # the limit
            builds.pop(bid)

        elif lookaside and not tags.isdisjoint(lookaside):
            # don't want it, it's in the lookaside
            builds.pop(bid)

    return itervalues(builds)


def filter_imported(build_infos, by_cg=(), negate=False):
    """
    Given a sequence of build info dicts, yield those which are
    imports.

    build_infos may have been decorated by the
    decorate_build_archive_data function. This provides an accurate
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
    content generators. "any" should not be used with negate of True,
    as it will always result in no matches.

    :param build_infos: build infos to filter through
    :type build_infos: list[dict] or Iterator[dict]

    :param by_cg: Content generator names to filter for
    :type by_cg: list[str], optional

    :param negate: whether to negate the test, Default False
    :type negate: bool, optional

    :rtype: Generator[dict]
    """

    by_cg = set(by_cg)
    any_cg = "any" in by_cg
    disjoint = by_cg.isdisjoint

    for build in build_infos:

        # either get the decorated archive cg names, or start a fresh
        # one based on the possible cg_name associated with this build
        build_cgs = build.get("archive_cg_names", set())
        cg_name = build.get("cg_name")
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


def gather_buildroots(session, build_ids):

    # multicall to fetch the artifacts for all build IDs
    archives = bulk_load_build_archives(session, build_ids)

    # gather all the buildroot IDs
    root_ids = set()
    for archive_list in itervalues(archives):
        for archive in archive_list:
            broot_id = archive["buildroot_id"]
            if broot_id:
                # do NOT allow None or 0
                root_ids.add(broot_id)

    # multicall to fetch all the buildroots
    buildroots = bulk_load_buildroots(session, root_ids)

    results = {}

    for build_id, archive_list in iteritems(archives):
        broots = (a["buildroot_id"] for a in archive_list)
        broots = unique(b for b in broots if b)
        results[build_id] = [buildroots[b] for b in broots]

    return results


def gather_component_build_ids(session, build_ids, btypes=None):
    """
    Given a sequence of build IDs, identify the IDs of the component
    builds used to produce them (installed in the buildroots of the
    archives of the original build IDs)

    Returns a dict mapping the original build IDs to a list of the
    discovered component build IDs.

    If btypes is None, then all component archive types will be
    considered. Otherwise, btypes may be a sequence of btype names and
    only component archives of those types will be considered.

    :param build_ids: Build IDs to collect components for

    :type build_ids: list[int]

    :param btypes: Component archive btype filter. Default, all types

    :type btypes: list[str], optional

    :rtype: dict[int, list[int]]
    """

    # multicall to fetch the artifacts for all build IDs
    archives = bulk_load_build_archives(session, build_ids)

    # gather all the buildroot IDs
    root_ids = set()
    for archive_list in itervalues(archives):
        for archive in archive_list:
            broot_id = archive["buildroot_id"]
            if broot_id:
                # do NOT allow None or 0
                root_ids.add(broot_id)

    components = {}

    if btypes is None or None in btypes:
        # in order to query all types, we need to explicitly query for
        # RPMs, and then archives of type None
        btypes = ("rpm", None)

    # dig up the component archives (pretending that RPMs are just
    # another archive type as usual) and map them to the buildroot ID.
    for bt in btypes:
        if bt == "rpm":
            find = lambda b: session.listRPMs(componentBuildrootID=b)
        else:
            find = lambda b: session.listArchives(componentBuildrootID=b,
                                                  type=bt)
        update_extend(components, bulk_load(session, find, root_ids))

    results = {}

    # now associate the components back with the original build IDs
    for build_id, archive_list in iteritems(archives):
        cids = set()
        for archive in archive_list:
            broot_id = archive["buildroot_id"]
            archives = components.get(broot_id, ())
            cids.update(c["build_id"] for c in archives)

        results[build_id] = list(cids)

    return results


class BuildFilter(object):

    def __init__(self, session,
                 limit_tag_ids=None, lookaside_tag_ids=None,
                 imported=None, cg_list=None,
                 btypes=None):

        """
        :param limit_tag_ids: if specified, builds must be tagged with one
          of these tags
        :type limit_tag_ids: list[int], optional

        :param lookaside_tag_ids: if specified, builds must not be tagged
          with any of these tags
        :type lookaside_tag_ids: list[int], optional

        :param imported: if True, only imported builds are returned. If
          False, only unimported builds are returned. Default, does not
          test whether a build is imported or not.
        :type imported: bool, optional

        :param cg_list: If specified, only builds which are produced by
          the named content generators will be returned.
        :type cg_list: list[str], optional

        :param btypes: Filter for the given build types, by name
        :type btypes: list[str], optional

        """

        self._session = session

        self._limit_tag_ids = \
            set(limit_tag_ids) if limit_tag_ids else None

        self._lookaside_tag_ids = \
            set(lookaside_tag_ids) if lookaside_tag_ids else None

        self._imported = imported
        self._cg_list = set(cg_list)

        self._btypes = set(btypes or ())


    def filter_by_tags(self, build_infos):
        return filter_by_tags(self._session, build_infos,
                              limit_tag_ids=self._limit_tag_ids,
                              lookaside_tag_ids=self._lookaside_tag_ids)


    def filter_by_btype(self, build_infos):
        bt = self._btypes
        if bt:
            def test(b):
                btn = b.get("archive_btype_names")
                return btn and not bt.isdisjoint(btn)

            build_infos = filter(test, build_infos)

        return build_infos


    def filter_imported(self, build_infos):
        if self._cg_list or self._imported is not None:
            negate = not (self._imported or self._imported is None)
            build_infos = filter_imported(build_infos, self._cg_list, negate)

        return build_infos


    def __call__(self, build_infos):
        # TODO: could we add some caching to this, such that we
        # associate the build ID with a bool indicating whether it's
        # been filtered before and whether it was included (True) or
        # omitted (False).  That might allow us to cut down on the
        # overhead if filtering is used multiple times... However,
        # will filtering ever actually be used multiple times?

        # ensure this is a real list and not a generator of some sort
        work = list(build_infos)

        # first stage filtering, based on tag membership
        work = self.filter_by_tags(work)

        # check if we're going to need the decorated additional data
        # for filtering, and if so decorate
        with_cg = bool(self._cg_list)
        if self._btypes or with_cg or self._imported is not None:
            work = decorate_build_archive_data(self._session, work, with_cg)

        # filtering by btype (provided by decorated addtl data)
        work = self.filter_by_btype(work)

        # filtering by import or cg (provided by decorated addtl data)
        work = self.filter_imported(work)

        return work


#
# The end.
