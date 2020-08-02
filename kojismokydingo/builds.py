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


def filter_imported(build_infos, negate=False, by_cg=set()):
    """
    Given a sequence of build info dicts, yield those which are imports.

    if negate is True, then behavior is flipped and only non-imports
    are emitted (and the by_cg parameter is ignored)

    If by_cg is not specified, then only non CG imports are emitted.
    If by_cg is specified, then emit only those imports which are from
    a content generator in that set (or all content generators if
    'all' is in the by_cg set).
    """

    all_cg = "all" in by_cg

    for build in build_infos:
        extra = build.get("extra", None)
        build_cg = extra.get("build_system", None) if extra else None

        is_import = build.get("task_id", None) is None

        if negate:
            # looking for non-imports, regardless of CG or not
            if not is_import:
                yield build

        elif is_import:
            if build_cg:
                if all_cg or build_cg in by_cg:
                    # this is a CG import, and we wanted either this
                    # specific one or all of them
                    yield build

            elif not by_cg:
                # this isn't a CG import, and we didn't want it to be
                yield build


#
# The end.
