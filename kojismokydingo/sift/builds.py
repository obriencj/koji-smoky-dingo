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
from six import iteritems, itervalues

from . import (
    DEFAULT_SIEVES,
    ItemSieve, Sieve, Sifter, SifterError,
    ensure_int_or_str, ensure_matchers, ensure_str, )
from .. import bulk_load, bulk_load_builds, bulk_load_users
from ..builds import build_dedup
from ..common import rpm_evr_compare
from ..tags import gather_tag_ids


__all__ = (
    "DEFAULT_BUILD_INFO_SIEVES",

    "EpochSieve",
    "EVRCompareEQ",
    "EVRCompareNE",
    "EVRCompareLT",
    "EVRCompareLE",
    "EVRCompareGT",
    "EVRCompareGE",
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
        state = ensure_int_or_str(pattern)

        found = BUILD_STATES.get(state)
        if found is None:
            raise SifterError("Unknown build state: %r" % pattern)

        if isinstance(state, str):
            state = found

        super(ItemSieve, self).__init__(sifter, state)


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
    Valid comparison values are

    * ``==``
    * ``!=``
    * ``>``
    * ``>=``
    * ``<``
    * ``<=``
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


    def check(self, session, binfo):
        other = (binfo["epoch"], binfo["version"], binfo["release"])
        other = tuple((str(x) if x else "0") for x in other)

        ours = (self.epoch, self.version, self.release or other[2])

        relative = rpm_evr_compare(other, ours)
        return self.op(relative, 0)


    def __repr__(self):
        return "".join(("(", self.name, " ", self.token, ")"))


class EVRCompareEQ(EVRCompare):
    """
    Usage: ``(== VER)``

    ``VER`` can be in any of the following forms

    * ``EPOCH:VERSION``
    * ``EPOCH:VERSION-RELEASE``
    * ``VERSION``
    * ``VERSION-RELEASE``

    If ``EPOCH`` is omitted, it is presumed to be ``0``.
    If ``RELEASE`` is omitted, it is presumed to be equivalent.

    Passes builds whose EVR compares as requested.
    """

    name = "=="


class EVRCompareNE(EVRCompare):
    """
    Usage: ``(!= VER)``

    ``VER`` can be in any of the following forms

    * ``EPOCH:VERSION``
    * ``EPOCH:VERSION-RELEASE``
    * ``VERSION``
    * ``VERSION-RELEASE``

    If ``EPOCH`` is omitted, it is presumed to be ``0``.
    If ``RELEASE`` is omitted, it is presumed to be equivalent.

    Passes builds whose EVR compares as requested.
    """

    name = "!="


class EVRCompareGT(EVRCompare):
    """
    Usage: ``(> VER)``

    ``VER`` can be in any of the following forms

    * ``EPOCH:VERSION``
    * ``EPOCH:VERSION-RELEASE``
    * ``VERSION``
    * ``VERSION-RELEASE``

    If ``EPOCH`` is omitted, it is presumed to be ``0``.
    If ``RELEASE`` is omitted, it is presumed to be equivalent.

    Passes builds whose EVR compares as requested.
    """

    name = ">"


class EVRCompareGE(EVRCompare):
    """
    Usage: ``(>= VER)``

    ``VER`` can be in any of the following forms

    * ``EPOCH:VERSION``
    * ``EPOCH:VERSION-RELEASE``
    * ``VERSION``
    * ``VERSION-RELEASE``

    If ``EPOCH`` is omitted, it is presumed to be ``0``.
    If ``RELEASE`` is omitted, it is presumed to be equivalent.

    Passes builds whose EVR compares as requested.
    """

    name = ">="


class EVRCompareLT(EVRCompare):
    """
    Usage: ``(< VER)``

    ``VER`` can be in any of the following forms

    * ``EPOCH:VERSION``
    * ``EPOCH:VERSION-RELEASE``
    * ``VERSION``
    * ``VERSION-RELEASE``

    If ``EPOCH`` is omitted, it is presumed to be ``0``.
    If ``RELEASE`` is omitted, it is presumed to be equivalent.

    Passes builds whose EVR compares as requested.
    """

    name = "<"


class EVRCompareLE(EVRCompare):
    """
    Usage: ``(<= VER)``

    ``VER`` can be in any of the following forms

    * ``EPOCH:VERSION``
    * ``EPOCH:VERSION-RELEASE``
    * ``VERSION``
    * ``VERSION-RELEASE``

    If ``EPOCH`` is omitted, it is presumed to be ``0``.
    If ``RELEASE`` is omitted, it is presumed to be equivalent.

    Passes builds whose EVR compares as requested.
    """

    name = "<="


class TaggedSieve(Sieve):
    """
    usage: (tagged [TAG...])

    If no TAG patterns are specified, matches builds which have any
    tags at all.

    If TAG patterns are specified, then only matches builds which have
    a tag that matches any of the given patterns.
    """

    name = "tagged"


    def __init__(self, sifter, *tagnames):
        super(TaggedSieve, self).__init__(sifter)
        self.tagnames = ensure_matchers(tagnames)


    def prep(self, session, binfos):

        needed = {}
        for binfo in binfos:
            cache = self.get_cache(binfo)
            if "tag_names" not in cache:
                needed[binfo["id"]] = binfo

        if needed:
            fn = lambda i: session.listTags(build=i)
            for bid, tags in iteritems(bulk_load(session, fn, needed)):
                cache = self.get_cache(needed[bid])
                cache["tag_names"] = [t["name"] for t in tags]
                cache["tag_ids"] = [t["id"] for t in tags]


    def check(self, session, binfo):
        cache = self.get_cache(binfo)

        tag_names = cache.get("tag_names", ())
        tag_ids = cache.get("tag_ids", ())

        if not self.tagnames:
            # when used as simply (tagged) then we're checking that
            # there are ANY tags.
            return bool(tag_names)

        for match in self.tagnames:
            # try to validate all of our potential matchers against
            # both names and IDs
            if match in tag_names or match in tag_ids:
                return True

        return False


class InheritedSieve(Sieve):
    """
    usage: (inherited TAG [TAG...])

    Matches builds which are tagged into any of the given tags or
    their parent tags. Each TAG must be a tag name or tag ID, patterns
    are not allowed.
    """

    name = "inherited"


    def __init__(self, sifter, tagname, *tagnames):
        tags = [tagname] + tagnames
        tags = ensure_str(tags)

        super(InheritedSieve, self).__init__(sifter, tags)
        self.tag_ids = None


    def get_cache(self, binfo):
        # let's use the same caches that the Tagged sieve uses
        return self.sifter.get_cache("tagged", binfo)


    def prep(self, session, binfos):
        if self.tag_ids is None:
            self.tag_ids = gather_tag_ids(session, deep=self.tagnames)

        needed = {}
        for binfo in binfos:
            cache = self.get_cache(binfo)
            if "tag_names" not in cache:
                needed[binfo["id"]] = binfo

        if needed:
            fn = lambda i: session.listTags(build=i)
            for bid, tags in iteritems(bulk_load(session, fn, needed)):
                cache = self.get_cache(needed[bid])
                cache["tag_names"] = [t["name"] for t in tags]
                cache["tag_ids"] = [t["id"] for t in tags]


    def check(self, session, binfo):
        inheritance = self.tag_ids
        cache = self.get_cache(binfo)

        for tid in cache.get("tag_ids", ()):
            if tid in inheritance:
                return True

        return False


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
    TaggedSieve,
    InheritedSieve,
]


def build_info_sieves():
    """
    A new list containing the default build-info sieve classes.

    This function is used by `build_info_sifter` when creating its
    `Sifter` instance.

    :rtype: list[type[Sieve]]
    """

    sieves = []

    # TODO: grab some more via entry_points
    sieves.extend(DEFAULT_SIEVES)
    sieves.extend(DEFAULT_BUILD_INFO_SIEVES)

    return sieves


def build_info_sifter(src_str):
    """
    Create a Sifter from the source using the default build-info
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