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
Koji Smoky Dingo - Sifter filtering

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import operator

from koji import BUILD_STATES
from six import itervalues

from . import (
    DEFAULT_SIEVES,
    ItemSieve, Sieve, Sifter, SifterError,
    ensure_int_or_str, ensure_str, )
from .. import bulk_load_builds, bulk_load_users
from ..builds import build_dedup
from ..common import rpm_evr_compare


__all__ = (
    "DEFAULT_BUILD_INFO_SIEVES",

    "EpochSieve",
    "ImportedSieve",
    "NameSieve",
    "NVRSieve",
    "OwnerSieve",
    "ReleaseSieve",
    "SourceSieve",
    "StateSieve",
    "VersionSieve",

    "build_info_sieves",
    "build_info_sifter",
    "sift_builds",
    "sift_nvrs",
)


class NVRSieve(ItemSieve):
    """
    Usage: ``(nvr NVR [NVR...])``

    filters for dict infos whose `nvr` key matches any of the given
    NVR matchers.
    """

    name = field = "nvr"


class NameSieve(ItemSieve):
    """
    Usage: ``(name NAME [NAME...])``

    filters for dict infos whose `name` key matches any of the given
    NAME matchers.
    """

    name = field = "name"


class VersionSieve(ItemSieve):
    """
    Usage: ``(version VER [VER...])``

    filters for dict infos whose `version` key matches any of the given
    VER matchers.
    """

    name = field = "version"


class ReleaseSieve(ItemSieve):
    """
    Usage: ``(release REL [REL...])``

    filters for dict infos whose `release` key matches any of the given
    REL matchers.
    """

    name = field = "release"


class EpochSieve(ItemSieve):
    """
    Usage: ``(epoch EPOCH [EPOCH...])``

    filters for dict infos whose `epoch` key matches any of the given
    EPOCH matchers.
    """

    name = field = "epoch"


class StateSieve(ItemSieve):
    """
    Usage: ``(state BUILD_STATE [BUILD_STATE...])``

    filters for dict infos whose `state` key matches any of the given
    koji build states. Build states may be specified as either an integer
    or one of the following strings or symbols

    * ``BUILDING``
    * ``COMPLETE``
    * ``DELETED``
    * ``FAILED``
    * ``CANCELED``
    """

    name = field = "state"

    def __init__(self, sifter, pattern):
        pattern = ensure_int_or_str(pattern)

        if pattern not in BUILD_STATES:
            raise SifterError("Unknown build state: %r" % pattern)

        if not isinstance(pattern, int):
            pattern = BUILD_STATES[pattern]

        super(ItemSieve, self).__init__(sifter, pattern)


class SourceSieve(ItemSieve):
    """
    Usage: ``(source URI [URI...])``

    filters for dict infos whose `source` key matches any of the given
    URI matchers.
    """

    name = field = "source"


class OwnerSieve(Sieve):
    """
    Usage: ``(owner USER [USER...])```

    filters for builds whose `owner_name` or `owner_id` key matches
    any of the given USERs.

    The users will be validated at the time of the sieve's first
    invocation, which may result in a NoSuchUser error.
    """

    name = "owner"

    def __init__(self, sifter, user, *users):
        self.users = [user]
        self.users.extend(users)
        self._user_ids = None


    def prep(self, session, _build_infos):
        if self._user_ids is None:
            loaded = bulk_load_users(session, self.users)
            self._user_ids = set(u["id"] for u in itervalues(loaded))
            print("user IDs", self._user_ids)


    def check(self, session, binfo):
        return binfo.get("owner_id") in self._user_ids


class ImportedSieve(Sieve):
    """
    Usage: ``(imported)``

    filters for build info dicts whose task ID is empty or null.
    """

    name = "imported"

    def check(self, session, binfo):
        return not binfo.get("task_id")


OPMAP = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}


class EVRCompare(Sieve):
    """
    Usage: ``(COMPARISON VER)``

    Valid COMPARISON values are
    * ``==``
    * ``!=``
    * ``>``
    * ``>=``
    * ``<``
    * ``<=``

    VER can be in any of the following forms
    * EPOCH:VERSION
    * EPOCH:VERSION-RELEASE
    * VERSION
    * VERSION-RELEASE

    If EPOCH is omitted, it is presumed to be 0.
    If RELEASE is omitted, it is presumed to be equivalent.

    Passes builds whose EVR compares as requested.
    """

    def __init__(self, sifter, version):
        super(EVRCompare, self).__init__(sifter)
        self.token = version = ensure_str(version)

        if ":" in version:
            epoch, version = version.split(":", 1)
        else:
            epoch = "0"

        if "-" in version:
            version, release = version.split("-", 1)
        else:
            release = None

        self.epoch = epoch
        self.version = version
        self.release = release

        self.op = OPMAP[self.name]


    def get_cache(self, binfo):
        return self.sifter.get_cache("evr-compare", binfo)


    def check(self, session, binfo):
        other = (binfo["epoch"], binfo["version"], binfo["release"])
        other = tuple((str(x) if x else "0") for x in other)

        ours = (self.epoch, self.version, self.release or other[2])

        relative = rpm_evr_compare(other, ours)
        return self.op(relative, 0)


    def __repr__(self):
        return "".join(("(", self.name, " ", self.token, ")"))


class EVRCompareEQ(EVRCompare):
    name = "=="


class EVRCompareNE(EVRCompare):
    name = "!="


class EVRCompareGT(EVRCompare):
    name = ">"


class EVRCompareGE(EVRCompare):
    name = ">="


class EVRCompareLT(EVRCompare):
    name = "<"


class EVRCompareLE(EVRCompare):
    name = "<="


DEFAULT_BUILD_INFO_SIEVES = [
    EpochSieve,
    ImportedSieve,
    NameSieve,
    NVRSieve,
    OwnerSieve,
    ReleaseSieve,
    SourceSieve,
    StateSieve,
    VersionSieve,
    EVRCompareEQ,
    EVRCompareNE,
    EVRCompareGT,
    EVRCompareGE,
    EVRCompareLT,
    EVRCompareLE,
]


def build_info_sieves():
    """
    :rtype: list[type[Sieve]]
    """

    sieves = []

    # TODO: grab some more via entry_points
    sieves.extend(DEFAULT_SIEVES)
    sieves.extend(DEFAULT_BUILD_INFO_SIEVES)

    return sieves


def build_info_sifter(src_str):
    """
    Create a Sifter from the source using the default build info
    Sieves.

    :param src_str: sieve expressions source
    :type src_str: src

    :rtype: Sifter
    """

    return Sifter(build_info_sieves(), src_str)


def sift_builds(session, src_str, build_infos):
    """
    :param src_str: sieve expressions source
    :type src_str: src

    :param build_infos: list of build info dicts to filter
    :type build_infos: list[dict]

    :rtype: dict[str,list[dict]]
    """

    sifter = build_info_sifter(src_str)
    return sifter(session, build_infos)


def sift_nvrs(session, src_str, nvrs):
    """
    :param src_str: sieve expressions source
    :type src_str: src

    :param nvrs: list of NVRs to load and filter
    :type nvrs: list[str]

    :rtype: dict[str,list[dict]]
    """

    loaded = bulk_load_builds(session, nvrs, err=False)
    builds = build_dedup(itervalues(loaded))
    return sift_builds(session, src_str, builds)


#
# The end.
