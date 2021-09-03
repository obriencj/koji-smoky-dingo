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
Koji Smoky Dingo - Sifty Dingo filtering for Koji Builds

This module provides sieves for filtering through koji build info
dicts.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from abc import abstractmethod
from collections import defaultdict
from itertools import islice
from koji import BUILD_STATES, ClientSession
from typing import Dict, Iterable, List, Type, Union
from operator import itemgetter

from . import (
    DEFAULT_SIEVES,
    IntStrSieve, ItemSieve, MatcherSieve, Number, Sieve,
    Sifter, SifterError, VariadicSieve,
    ensure_int, ensure_int_or_str, ensure_str, ensure_symbol, )
from .common import ensure_comparison, CacheMixin
from .. import (
    as_taginfo, bulk_load_builds, bulk_load_tags, bulk_load_users,
    iter_bulk_load, )
from ..builds import (
    BuildNEVRCompare,
    build_dedup, build_nvr_sort,
    decorate_builds_btypes, decorate_builds_cg_list,
    decorate_builds_maven, gather_rpm_sigkeys, gavgetter, )
from ..common import unique
from ..rpm import evr_compare, evr_split
from ..tags import gather_tag_ids
from ..types import BuildInfo, BuildInfos


__all__ = (
    "DEFAULT_BUILD_INFO_SIEVES",

    "CGImportedSieve",
    "CompareLatestIDSieve",
    "CompareLatestNVRSieve",
    "EpochSieve",
    "EVRCompareEQ",
    "EVRCompareNE",
    "EVRCompareLT",
    "EVRCompareLE",
    "EVRCompareGT",
    "EVRCompareGE",
    "EVRHigh",
    "EVRLow",
    "ImportedSieve",
    "InheritedSieve",
    "LatestSieve",
    "LatestMavenSieve",
    "NameSieve",
    "NVRSieve",
    "OwnerSieve",
    "PkgAllowedSieve",
    "PkgBlockedSieve",
    "PkgUnlistedSieve",
    "ReleaseSieve",
    "SignedSieve",
    "StateSieve",
    "TaggedSieve",
    "TypeSieve",
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


class StateSieve(Sieve):
    """
    Usage: ``(state BUILD_STATE [BUILD_STATE...])``

    filters for dict infos whose `state` key matches any of the given
    koji build states. Build states may be specified as either an
    integer or one of the following strings or symbols

    * ``BUILDING``
    * ``COMPLETE``
    * ``DELETED``
    * ``FAILED``
    * ``CANCELED``
    """

    name = "state"


    def __init__(self, sifter, name, *names):
        super().__init__(sifter, name, *names)

        states = []
        for pattern in self.tokens:
            state = ensure_int_or_str(pattern)
            if isinstance(state, str):
                state = state.upper()

            found = BUILD_STATES.get(state)
            if found is None:
                raise SifterError(f"Unknown build state: {pattern!r}")

            if isinstance(state, str):
                state = found

            states.append(state)

        self.states = tuple(states)


    def check(self, session, info):
        return info["state"] in self.states


class OwnerSieve(IntStrSieve):
    """
    Usage: ``(owner USER [USER...])```

    filters for builds whose `owner_name` or `owner_id` key matches
    any of the given USERs.

    The users will be validated at the time of the sieve's first
    invocation, which may result in a NoSuchUser error.
    """

    name = "owner"


    def __init__(self, sifter, user, *users):
        super().__init__(sifter, user, *users)
        self._user_ids = None


    def prep(self, session, _build_infos):
        if self._user_ids is None:
            loaded = bulk_load_users(session, self.tokens)
            self._user_ids = set(u["id"] for u in loaded.values())


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
        version = ensure_str(version)
        super().__init__(sifter, version)

        self.token = version

        epoch, version, self.release = evr_split(version)
        self.epoch = epoch or "0"
        self.version = version or "0"

        self.op = ensure_comparison(self.name)


    def check(self, session, binfo):
        other = (binfo["epoch"], binfo["version"], binfo["release"])
        other = tuple((str(x) if x else "0") for x in other)

        ours = (self.epoch, self.version, self.release or other[2])

        relative = evr_compare(other, ours)
        return self.op(relative, 0)


    def __repr__(self):
        # we don't want to auto-quote the token which the default
        # Sieve impl does.
        return f"({self.name} {self.token})"


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


class EVRSorted(Sieve):


    def __init__(self, sifter, count=1):
        count = ensure_int(count)

        if count < 1:
            raise SifterError("count must be greater than zero")

        self.count = count
        super().__init__(sifter, count=count)


    def run(self, session, binfos):

        collect = defaultdict(list)

        for bld in binfos:
            collect[bld["name"]].append(bld)

        reverse = self._reverse
        count = self.count

        if count == 1:
            for binfos in collect.values():
                yield build_nvr_sort(binfos, reverse=reverse)[0]
        else:
            for binfos in collect.values():
                blds = build_nvr_sort(binfos, reverse=reverse)
                yield from islice(blds, 0, count)


class EVRHigh(EVRSorted):
    """
    usage: (evr-high [count: COUNT])

    Filters to only the builds which are the higest EVR of their given
    package name.

    COUNT if specified is the number of highest EVR builds to
    return. Default is 1
    """

    name = "evr-high"
    _reverse = True


class EVRLow(EVRSorted):
    """
    usage: (evr-low [count: COUNT])

    Filters to only the builds which are the lowest EVR of their given
    package name.

    COUNT if specified is the number of lowest EVR builds to
    return. Default is 1
    """

    name = "evr-low"
    _reverse = False


class TaggedSieve(MatcherSieve):
    """
    usage: (tagged [TAG...])

    If no TAG patterns are specified, matches builds which have any
    tags at all.

    If TAG patterns are specified, then only matches builds which have
    a tag that matches any of the given patterns.
    """

    name = "tagged"


    def prep(self, session, binfos):

        needed = {}
        for binfo in binfos:
            cache = self.get_info_cache(binfo)
            if "tag_names" not in cache:
                needed[binfo["id"]] = cache

        fn = lambda i: session.listTags(build=i)
        for bid, tags in iter_bulk_load(session, fn, needed):
            cache = needed[bid]
            cache["tag_names"] = [t["name"] for t in tags]
            cache["tag_ids"] = [t["id"] for t in tags]


    def check(self, session, binfo):
        cache = self.get_info_cache(binfo)

        tag_names = cache.get("tag_names", ())
        tag_ids = cache.get("tag_ids", ())

        if not self.tokens:
            # when used as simply (tagged) then we're checking that
            # there are ANY tags.
            return bool(tag_names)

        for match in self.tokens:
            # try to validate all of our potential matchers against
            # both names and IDs
            if match in tag_names or match in tag_ids:
                return True

        return False


class InheritedSieve(IntStrSieve):
    """
    usage: (inherited TAG [TAG...])

    Matches builds which are tagged into any of the given tags or
    their parent tags. Each TAG must be a tag name or tag ID, patterns
    are not allowed.
    """

    name = "inherited"


    def __init__(self, sifter, tagname, *tagnames):
        super().__init__(sifter, tagname, *tagnames)
        self.tag_ids = None


    def get_info_cache(self, binfo):
        # let's use the same caches that the Tagged sieve uses
        return self.sifter.get_info_cache("tagged", binfo)


    def prep(self, session, binfos):
        if self.tag_ids is None:
            self.tag_ids = gather_tag_ids(session, deep=self.tokens)

        needed = {}
        for binfo in binfos:
            cache = self.get_info_cache(binfo)
            if "tag_names" not in cache:
                needed[binfo["id"]] = cache

        if needed:
            fn = lambda i: session.listTags(build=i)
            for bid, tags in iter_bulk_load(session, fn, needed):
                cache = needed[bid]
                cache["tag_names"] = [t["name"] for t in tags]
                cache["tag_ids"] = [t["id"] for t in tags]


    def check(self, session, binfo):
        inheritance = self.tag_ids
        cache = self.get_info_cache(binfo)

        for tid in cache.get("tag_ids", ()):
            if tid in inheritance:
                return True

        return False


class PkgListSieve(IntStrSieve, CacheMixin):

    def __init__(self, sifter, tagname, *tagnames):
        super().__init__(sifter, tagname, *tagnames)
        self.tag_ids = None


    def prep(self, session, binfos):
        # look up our tags
        tids = self.tag_ids
        if tids is None:
            loaded = bulk_load_tags(session, self.tokens, err=True)
            self.tag_ids = tids = set(t["id"] for t in loaded.values())

        # pre-load our package lists cache
        for tid in tids:
            self.list_packages(session, tid, True)


class PkgAllowedSieve(PkgListSieve):
    """
    usage: ``(pkg-allowed TAG [TAG...])``

    Matches builds which are have their package listing present and
    not blocked in any of the given tags or their parents.
    """

    name = "pkg-allowed"


    def check(self, session, binfo):
        pkg = binfo["name"]

        for tid in self.tag_ids:
            if pkg in self.allowed_packages(session, tid, True):
                return True
        else:
            return False


class PkgBlockedSieve(PkgListSieve):
    """
    usage: ``(pkg-blocked TAG [TAG...])``

    Matches builds which are have their package name blocked in any of
    the given tags or their parents.
    """

    name = "pkg-blocked"


    def check(self, session, binfo):
        pkg = binfo["name"]

        for tid in self.tag_ids:
            if pkg in self.blocked_packages(session, tid, True):
                return True
        else:
            return False


class PkgUnlistedSieve(PkgListSieve):
    """
    usage: ``(pkg-unlisted TAG [TAG...])``

    Matches builds which have their package name unlisted (neither
    allowed nor blocked) in any of the given tags or their parents.
    """

    name = "pkg-unlisted"

    def check(self, session, binfo):
        pkg = binfo["name"]

        for tid in self.tag_ids:
            if pkg in self.allowed_packages(session, tid, True):
                continue
            elif pkg in self.blocked_packages(session, tid, True):
                continue
            else:
                return True
        else:
            return False


class TypeSieve(MatcherSieve):
    """
    usage: ``(type BTYPE [BTYPE...])``

    Passes build infos that have archives of the given btype. Normal
    btypes are rpm, maven, image, and win.
    """

    name = "type"


    def __init__(self, sifter, btype, *btypes):
        super().__init__(sifter, btype, *btypes)


    def prep(self, session, binfos):
        decorate_builds_btypes(session, binfos)


    def check(self, session, binfo):
        bt_names = binfo.get("archive_btype_names", ())
        bt_ids = binfo.get("archive_btype_ids", ())

        for t in self.tokens:
            if t in bt_names or t in bt_ids:
                return True
        return False


class CGImportedSieve(MatcherSieve):
    """
    usage: ``(cg-imported [CGNAME...])``

    Passes build infos that have been produced via a cg-import by any
    of the named content generators. If no CGs are named, then passes
    build infos that have been produced by any content generator.
    """

    name = "cg-imported"


    def prep(self, session, binfos):
        decorate_builds_cg_list(session, binfos)


    def check(self, session, binfo):
        cg_names = binfo.get("archive_cg_names", ())
        cg_ids = binfo.get("archive_cg_ids", ())

        tokens = self.tokens
        if tokens:
            for t in tokens:
                if t in cg_names or t in cg_ids:
                    return True
            return False

        else:
            return bool(cg_names)


class LatestSieve(IntStrSieve, CacheMixin):
    """
    usage: ``(latest TAG [TAG...])``

    Passes build infos that are the latest build of their package name
    in any of the tags.
    """

    name = "latest"


    def __init__(self, sifter, tagname, *tagnames):
        super().__init__(sifter, tagname, *tagnames)
        self.tag_ids = None


    def prep(self, session, binfos):

        # first we need to convert our tokens into tag IDs
        tids = self.tag_ids
        if tids is None:
            tags = bulk_load_tags(session, self.tokens, err=True)
            tids = self.tag_ids = unique(t["id"] for t in tags.values())

        for tid in tids:
            # pre-fill the caches of build IDs
            self.latest_build_ids(session, tid, inherit=True)


    def check(self, session, binfo):
        bid = binfo["id"]
        for tid in self.tag_ids:
            latest = self.latest_build_ids(session, tid, inherit=True)
            if bid in latest:
                return True
        return False


class LatestMavenSieve(IntStrSieve, CacheMixin):
    """
    usage: ``(latest-maven TAG [TAG...])``

    Passes build infos that have btype maven and are the build of
    their GAV in any of the tags.
    """

    name = "latest-maven"


    def __init__(self, sifter, tagname, *tagnames):
        super().__init__(sifter, tagname, *tagnames)
        self.tag_ids = None


    def prep(self, session, binfos):

        # first we need to convert our tokens into tag IDs
        tids = self.tag_ids
        if tids is None:
            tags = bulk_load_tags(session, self.tokens, err=True)
            tids = self.tag_ids = unique(t["id"] for t in tags.values())

        # in order to perform the GAV comparisons, we need to have
        # loaded the various binfos with their maven fields. This
        # corrects any which were not loaded this way.
        decorate_builds_maven(session, binfos)

        for tid in tids:
            # pre-fill the caches of build IDs
            self.latest_maven_build_ids(session, tid, inherit=True)


    def check(self, session, binfo):
        if "maven_group_info" not in binfo:
            return False

        bid = binfo["id"]
        for tid in self.tag_ids:
            latest = self.latest_maven_build_ids(session, tid, inherit=True)
            if bid in latest:
                return True
        return False


class SignedSieve(MatcherSieve):
    """
    usage: ``(signed [KEY...])``

    Passes builds which have RPMs signed with any of the given keys.
    If no keys are specified then passes builds which have RPMs signed
    with any key at all.
    """

    name = "signed"


    def prep(self, session, binfos):
        needed = {}
        for binfo in binfos:
            cache = self.get_info_cache(binfo)
            if "rpmsigs" not in cache:
                needed[binfo["id"]] = cache

        if not needed:
            return

        for bid, sigs in gather_rpm_sigkeys(session, needed).items():
            # we need to drop the unsigned key, which is an empty
            # string
            cache = needed[bid]
            cache["rpmsigs"] = list(filter(None, sigs)) or None


    def check(self, session, binfo):
        want_keys = self.tokens
        build_keys = self.get_info_cache(binfo).get("rpmsigs")

        if not want_keys:
            return bool(build_keys)

        elif build_keys is None:
            return False

        else:
            for wanted in want_keys:
                if wanted in build_keys:
                    return True
            return False


class CompareLatestSieve(CacheMixin):
    """
    Abstract base for performing sieving comparisons against the
    latest builds in a tag using an operand.

    Valid comparison operands are:

    * ``==``
    * ``!=``
    * ``>``
    * ``>=``
    * ``<``
    * ``<=``

    The data being compared is the result of the abastract
    `comparison_key` method.
    """

    def __init__(self, sifter, comparison, tag):
        op = ensure_comparison(comparison)
        tag = ensure_int_or_str(tag)

        super().__init__(sifter, comparison, tag)
        self.op = op
        self.tag_id = None


    @abstractmethod
    def comparison_key(self, binfo):
        pass


    def prep(self, session, binfos):
        if self.tag_id is None:
            self.tag_id = as_taginfo(session, self.tokens[1])["id"]


    def comparison(self, binfo, latest):
        keyfn = self.comparison_key
        return self.op(keyfn(binfo), keyfn(latest))


class CompareLatestIDSieve(CompareLatestSieve):
    """
    usage: ```(compare-latest-id OP TAG)```

    Filters for builds which have an ID which compares against the
    latest build of the same package from TAG.

    Valid comparison ops are:

    * ``==``
    * ``!=``
    * ``>``
    * ``>=``
    * ``<``
    * ``<=``

    example: ```(compare-latest-id >= foo-1.0-released)``` will filter
    for builds which have an ID that is greater-than-or-equal-to the
    ID of the latest build of the same package name in the
    foo-1.0-released tag.
    """

    name = "compare-latest-id"


    comparison_key = itemgetter("id")


    def check(self, session, binfo):
        blds = self.latest_builds_by_name(session, self.tag_id, inherit=True)
        latest = blds.get(binfo["name"])

        if latest is None:
            return False
        else:
            return self.comparison(binfo, latest)


class CompareLatestNVRSieve(CompareLatestSieve):
    """
    usage: ```(compare-latest-nvr OP TAG)```

    Filters for builds which have an NVR which compares against the
    latest build of the same package from TAG.

    Valid comparison ops are:

    * ``==``
    * ``!=``
    * ``>``
    * ``>=``
    * ``<``
    * ``<=``

    example: ```(compare-latest-nvr >= foo-1.0-released)``` will filter
    for builds which have an NVR that is greater-than-or-equal-to the
    NVR of the latest build of the same package name in the
    foo-1.0-released tag.
    """

    name = "compare-latest-nvr"

    comparison_key = BuildNEVRCompare


    def check(self, session, binfo):
        blds = self.latest_builds_by_name(session, self.tag_id, inherit=True)
        latest = blds.get(binfo["name"])

        if latest is None:
            return False
        else:
            return self.comparison(binfo, latest)


# class CompareLatestMavenSieve(CompareLatest):
#
#     name = "compare-latest-maven"


DEFAULT_BUILD_INFO_SIEVES: List[Type[Sieve]] = [
    CGImportedSieve,
    CompareLatestIDSieve,
    CompareLatestNVRSieve,
    EpochSieve,
    EVRCompareEQ,
    EVRCompareNE,
    EVRCompareGT,
    EVRCompareGE,
    EVRCompareLT,
    EVRCompareLE,
    EVRHigh,
    EVRLow,
    ImportedSieve,
    InheritedSieve,
    LatestSieve,
    LatestMavenSieve,
    NameSieve,
    NVRSieve,
    OwnerSieve,
    PkgAllowedSieve,
    PkgBlockedSieve,
    PkgUnlistedSieve,
    ReleaseSieve,
    SignedSieve,
    StateSieve,
    TaggedSieve,
    TypeSieve,
    VersionSieve,
]


def build_info_sieves() -> List[Type[Sieve]]:
    """
    A new list containing the default build-info sieve classes.

    This function is used by `build_info_sifter` when creating its
    `Sifter` instance.
    """

    sieves: List[Type[Sieve]] = []

    # TODO: grab some more via entry_points
    sieves.extend(DEFAULT_SIEVES)
    sieves.extend(DEFAULT_BUILD_INFO_SIEVES)

    return sieves


def build_info_sifter(
        source: str,
        params: Dict[str, str] = None) -> Sifter:
    """
    Create a Sifter from the source using the default build-info
    Sieves.

    :param source: sieve expressions source

    :param params: sieve parameters
    """

    return Sifter(build_info_sieves(), source, "id", params)


def sift_builds(
        session: ClientSession,
        src_str: str,
        build_infos: BuildInfos,
        params: Dict[str, str] = None) -> Dict[str, List[BuildInfo]]:
    """
    Filter a group of build infos with a sieve compiled from the given
    source string.

    :param session: an active koji client session

    :param src_str: sieve expressions source

    :param build_infos: list of build info dicts to filter

    :param params: sieve parameters

    :returns: mapping of flags to matching build info dicts
    """

    sifter = build_info_sifter(src_str, params)
    return sifter(session, build_infos)


def sift_nvrs(
        session: ClientSession,
        src_str: str,
        nvrs: Iterable[Union[int, str]],
        params: Dict[str, str] = None) -> Dict[str, List[BuildInfo]]:
    """
    Load a group of NVRs as build infos and filter them with a sieve
    compiled from the given source string.

    :param session: an active koji client session

    :param src_str: sieve expressions source

    :param nvrs: list of NVRs to load and filter

    :param params: sieve parameters

    :returns: mapping of flags to matching build info dicts
    """

    loaded = bulk_load_builds(session, nvrs, err=False)
    builds = build_dedup(loaded.values())
    return sift_builds(session, src_str, builds, params)


#
# The end.
