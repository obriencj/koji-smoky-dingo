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
Koji Smoky Dingo - Builds module

Functions for working with builds and build archives in Koji.

:author: cobrien@redhat.com
:license: GPL version 3
"""


from collections import OrderedDict
from six import iteritems, itervalues

from . import bulk_load_build_archives, bulk_load_buildroots
from .common import NEVRCompare


def nevr_sort_builds(build_infos):
    """
    Given a sequence of build info dictionaries, sort them by Name,
    Epoch, Version, and Release using RPM's variation of comparison
    """

    return sorted(build_infos, key=NEVRCompare)


def build_nvr_sort(builds):
    dedup = dict((b["id"], b) for b in builds)
    return nevr_sort_builds(itervalues(dedup))


def build_id_sort(builds):
    dedup = dict((b["id"], b) for b in builds)
    return [b for _bid, b in sorted(iteritems(dedup))]


def build_dedup(builds):
    dedup = OrderedDict((b["id"], b) for b in builds)
    return list(itervalues(dedup))


def decorate_build_cg_list(session, build_infos):
    """
    Augments a list of build_info dicts with two new keys:

    * archive_cg_ids is a set of content generator IDs for each
      archive of the build

    * archive_cg_names is a set of content generator names for each
      archive of the build
    """

    # convert build_infos into an id:info dict
    builds = dict((b["id"], b) for b in build_infos)

    # multicall to fetch the artifacts for all build_infos
    archives = bulk_load_build_archives(session, builds)

    # gather all the buildroot IDs
    root_ids = set()
    for archive_list in itervalues(archives):
        for archive in archive_list:
            root_ids.add(archive["buildroot_id"])

    # multicall to fetch all the buildroots
    buildroots = bulk_load_buildroots(session, list(root_ids))

    # gather the cg_id and cg_name from each buildroot, and associate
    # it back with the original build info
    for build_id, archive_list in iteritems(archives):
        cg_ids = set()
        cg_names = set()

        for archive in archive_list:
            broot = buildroots[archive["buildroot_id"]]

            cg_id = broot.get("cg_id")
            if cg_id:
                cg_ids.add(cg_id)

            cg_name = broot.get("cg_name")
            if cg_name:
                cg_names.add(cg_name)

        bld = builds[build_id]
        bld["archive_cg_ids"] = set(cg_ids)
        bld["archive_cg_names"] = set(cg_names)

    return build_infos


def filter_imported(build_infos, negate=False, by_cg=set()):
    """
    Given a sequence of build info dicts, yield those which are imports.

    if negate is True, then behavior is flipped and only non-imports
    are emitted (and the by_cg parameter is ignored)

    If by_cg is not specified, then only non CG imports are emitted.
    If by_cg is specified, then emit only those imports which are from
    a content generator in that set (or all content generators if
    'all' is in the by_cg set).

    build_infos may have been decorated by the decorate_build_cg_list
    function. This provides an accurate listing of the content
    generators which have been used to import the build (if any). In
    the event that they have not been thus decorated, the cg filtering
    will rely on the cg_name setting on the build itself, which will
    only have been provided if the content generator reserved the
    build ahead of time.
    """

    all_cg = "all" in by_cg

    for build in build_infos:
        build_cgs = build.get("archive_cg_names", set())
        cg_name = build.get("cg_name")
        if cg_name:
            build_cgs.add(cg_name)

        is_import = build.get("task_id", None) is None

        if negate:
            # looking for non-imports, regardless of CG or not
            if not is_import:
                yield build

        elif is_import:
            if build_cgs:
                if all_cg or build_cgs.intersection(by_cg):
                    # this is a CG import, and we wanted either this
                    # specific one or all of them
                    yield build

            elif not by_cg:
                # this isn't a CG import, and we didn't want it to be
                yield build


#
# The end.
