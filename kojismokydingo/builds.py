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

from . import (
    bulk_load_build_archives, bulk_load_builds,
    bulk_load_buildroots)
from .common import NEVRCompare, chunkseq, unique


def build_nvr_sort(build_infos):
    """
    Given a sequence of build info dictionaries, deduplicate and then
    sort them by Name, Epoch, Version, and Release using RPM's
    variation of comparison

    :param build_infos: build infos to be sorted and de-duplicated
    :type build_infos: list[dict]

    :rtype: list[dict]
    """

    dedup = dict((b["id"], b) for b in build_infos if b)
    return sorted(itervalues(dedup), key=NEVRCompare)


def build_id_sort(build_infos):
    """
    Given a sequence of build info dictionaries, return a de-duplicated
    list of same, sorted by the build ID

    :param build_infos: build infos to be sorted and de-duplicated
    :type build_infos: list[dict]

    :rtype: list[dict]
    """

    dedup = dict((b["id"], b) for b in build_infos if b)
    return [b for _bid, b in sorted(iteritems(dedup))]


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


def iter_bulk_tag_builds(session, tagid, build_infos,
                         force=False, notify=False,
                         size=100, strict=False):

    """
    Tags a large number of builds using multicall invocations of
    tagBuildBypass. Builds are specified by build info dicts.

    yields lists of tuples containing a build info dict and the result
    of the tagBuildBypass call for that build. This gives the caller a
    chance to record the results of each multicall, and to present
    feedback to a user to indicate that the operations are continuing.

    :param tagid: Destination tag's ID
    :type tagid: int

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
    """

    for build_chunk in chunkseq(build_infos, size):
        session.multicall = True
        for build in build_chunk:
            session.tagBuildBypass(tagid, build["id"], force, notify)
        results = session.multiCall(strict=strict)
        yield list(zip(build_chunk, results))


def bulk_tag_builds(session, tagname, build_infos,
                    force=False, notify=False,
                    size=100, strict=False):

    """
    :param tagid: Destination tag's ID
    :type tagid: int

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
    """

    results = []
    for done in iter_bulk_tag_builds(session, tagname, build_infos,
                                     force=force, notify=notify,
                                     size=size, strict=strict):
        results.extend(done)
    return results


def bulk_tag_nvrs(session, tagname, nvrs,
                  force=False, notify=False,
                  size=100, strict=False):

    """
    Tags a large number of builds using multicall invocations of
    tagBuildBypass.

    The entire list of NVRs is validated first, checking that such
    a build exists. If strict is True then a missing build will cause a
    NoSuchBuild exception to be raised. If strict is False, then missing
    builds will be omitted from the tagging operation.

    The list of builds is de-duplicated, preserving order of the first
    instance found in the list of NVRs.

    Returns a list of tuples, pairing build info dicts with the result of
    a tagBuildBypass call for that build.
    """

    builds = bulk_load_builds(session, unique(nvrs), err=strict)
    builds = build_dedup(itervalues(builds))

    return bulk_tag_builds(session, tagname, builds,
                           force=force, notify=notify,
                           size=size, strict=strict)


def decorate_build_cg_list(session, build_infos):
    """
    Augments a list of build_info dicts with two new keys:

    * archive_cg_ids is a set of content generator IDs for each
      archive of the build

    * archive_cg_names is a set of content generator names for each
      archive of the build

    :param build_infos: list of build infos to decorate and return
    :type build_infos: list[dict]

    :rtype: list[dict]
    """

    # convert build_infos into an id:info dict
    builds = dict((b["id"], b) for b in build_infos)

    # multicall to fetch the artifacts for all build_infos
    archives = bulk_load_build_archives(session, list(builds))

    # gather all the buildroot IDs
    root_ids = set()
    for archive_list in itervalues(archives):
        for archive in archive_list:
            broot_id = archive["buildroot_id"]
            if broot_id:
                # do NOT allow None or 0
                root_ids.add(broot_id)

    # multicall to fetch all the buildroots
    buildroots = bulk_load_buildroots(session, list(root_ids))

    # gather the cg_id and cg_name from each buildroot, and associate
    # it back with the original build info
    for build_id, archive_list in iteritems(archives):
        cg_ids = set()
        cg_names = set()

        for archive in archive_list:
            broot_id = archive["buildroot_id"]
            if not broot_id:
                continue

            broot = buildroots[broot_id]

            cg_id = broot.get("cg_id")
            if cg_id:
                cg_ids.add(cg_id)

            cg_name = broot.get("cg_name")
            if cg_name:
                cg_names.add(cg_name)

        bld = builds[build_id]
        bld["archive_cg_ids"] = cg_ids
        bld["archive_cg_names"] = cg_names

    return build_infos


def filter_imported(build_infos, negate=False, by_cg=()):
    """
    Given a sequence of build info dicts, return those which are
    imports.

    if negate is True, then behavior is flipped and only non-imports
    are emitted (and the by_cg parameter is ignored)

    If by_cg is not specified, then only non CG imports are emitted.
    If by_cg is specified, then emit only those imports which are from
    a content generator in that set (or any content generators if
    'any' is in the by_cg list).

    build_infos may have been decorated by the decorate_build_cg_list
    function. This provides an accurate listing of the content
    generators which have been used to import the build (if any). In
    the event that they have not been thus decorated, the cg filtering
    will rely on the cg_name setting on the build itself, which will
    only have been provided if the content generator reserved the
    build ahead of time.

    :param build_infos: build infos to filter through
    :type build_infos: list[dict]

    :param negate: whether to negate the imported test, Default False
    :type negate: bool, optional

    :param by_cg: Content generator names to filter for
    :type by_cg: list[str], optional

    :rtype: list[dict]
    """

    by_cg = set(by_cg)
    any_cg = "any" in by_cg
    disjoint = by_cg.isdisjoint

    found = []

    for build in build_infos:

        # either get the decorated archive cg names, or start a fresh
        # one based on the possible cg_name associated with this build
        build_cgs = build.get("archive_cg_names", set())
        cg_name = build.get("cg_name")
        if cg_name:
            build_cgs.add(cg_name)

        is_import = build.get("task_id", None) is None

        if negate:
            # looking for non-imports, regardless of CG or not
            if not is_import:
                found.append(build)

        elif is_import:
            if build_cgs:
                # this is a CG import
                if any_cg or not disjoint(build_cgs):
                    # and we wanted either this specific one or any
                    found.append(build)

            else:
                # this is not a CG import
                if not by_cg:
                    # and we didn't want it to be
                    found.append(build)

    return found


#
# The end.
