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
Koji Smoky Dingo - Sifty Dingo filtering for Koji Tags

This module provides sieves for filtering through koji tag info
dicts.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from abc import abstractmethod
from koji import ClientSession
from operator import itemgetter
from typing import Dict, Iterable, Optional, List, Type, Union

from . import (
    DEFAULT_SIEVES,
    IntStrSieve, ItemSieve, MatcherSieve, Sieve, Sifter,
    SymbolSieve, VariadicSieve,
    ensure_int_or_str, ensure_str, ensure_symbol, )
from .common import CacheMixin, ensure_comparison
from .. import (
    as_buildinfo, bulk_load_builds, bulk_load_tags, iter_bulk_load, )
from ..builds import build_dedup
from ..rpm import evr_compare
from ..tags import (
    gather_tag_ids, tag_dedup, )
from ..types import TagInfo, TagInfos


__all__ = (
    "DEFAULT_TAG_INFO_SIEVES",

    "ArchSieve",
    "BuildTagSieve",
    "CompareLatestSieve",
    "DestTagSieve",
    "ExactArchSieve",
    "HasAncestorSieve",
    "HasChildSieve",
    "HasDescendantSieve",
    "HasParentSieve",
    "GroupSieve",
    "GroupPkgSieve",
    "LatestSieve",
    "LockedSieve",
    "NameSieve",
    "PermissionSieve",
    "PkgAllowedSieve",
    "PkgBlockedSieve",
    "PkgUnlistedSieve",
    "TaggedSieve",

    "tag_info_sieves",
    "tag_info_sifter",
    "sift_tags",
    "sift_tagnames",
)


class NameSieve(ItemSieve):
    """
    Usage: ``(name NAME [NAME...])``

    filters for dict infos whose name matches any of the given
    ``NAME`` matchers.
    """

    name = field = "name"


class ArchSieve(MatcherSieve):
    """
    usage: ``(arch [ARCH...])``

    If no ``ARCH`` patterns are specified, matches tags which have any
    architectures at all.

    If ``ARCH`` patterns are specified, then only matches tags which
    have an architecture that matches any of the given patterns.
    """

    name = "arch"


    def prep(self, session, taginfos):
        for tag in taginfos:
            cache = self.get_info_cache(tag)
            if "arches" not in cache:
                tagarch = tag["arches"]
                cache["arches"] = tagarch.split() if tagarch else ()


    def check(self, session, taginfo):
        wanted = self.tokens

        if not wanted:
            return bool(taginfo["arches"])

        cache = self.get_info_cache(taginfo)
        arches = cache.get("arches", ())

        for arch in arches:
            if arch in wanted:
                return True

        return False


class ExactArchSieve(SymbolSieve):
    """
    usage: ``(exact-arch [ARCH...])``

    If no ``ARCH`` names are specified, matches only tags which have
    no architectures.

    If ``ARCH`` names are specified, they must be specified as
    symbols.  Only matches tags which have the exact same set of
    architectures.
    """

    name = "exact-arch"


    def get_info_cache(self, tinfo):
        # let's use the same caches that the ArchSieve uses
        return self.sifter.get_info_cache("arch", tinfo)


    def check(self, session, taginfo):
        wanted = self.tokens

        if not wanted:
            return not taginfo["arches"]

        cache = self.get_info_cache(taginfo)
        arches = cache.get("arches", ())

        if len(arches) != len(wanted):
            return False

        for tok in wanted:
            if tok not in arches:
                return False

        return True


class LockedSieve(Sieve):
    """
    usage: ``(locked)``

    Matches tags which have been locked
    """

    name = "locked"


    def __init__(self, sifter):
        super().__init__(sifter)


    def check(self, session, taginfo):
        return taginfo["locked"]


class PermissionSieve(MatcherSieve):
    """
    usage: ``(permission [PERM...])```

    If no ``PERM`` is specified, then matches tags which have any
    non-None permission set.

    If any ``PERM`` patters are specified, then matches tags which
    have any of the listed permissions set.
    """

    name = "permission"


    def check(self, session, taginfo):
        return (taginfo["perm"] in self.tokens or
                taginfo["perm_id"] in self.tokens)


class TargetSieve(MatcherSieve):
    """
    Base class for BuildTagSieve and DestTagSieve. Both operate on the
    same principal, but use slightly different queries.
    """

    @abstractmethod
    def prep_targets(self, session, tagids):
        pass


    def prep(self, session, taginfos):
        needed = {}
        for tag in taginfos:
            cache = self.get_info_cache(tag)
            if "target_names" not in cache:
                needed[tag["id"]] = cache

        for tid, targs in self.prep_targets(session, needed):
            cache = needed[tid]
            cache["target_names"] = [t["name"] for t in targs]
            cache["target_ids"] = [t["id"] for t in targs]


    def check(self, session, taginfo):
        cache = self.get_info_cache(taginfo)
        target_names = cache.get("target_names", ())

        if not (self.tokens and target_names):
            return bool(target_names)

        target_ids = cache.get("target_ids", ())

        for match in self.tokens:
            if match in target_names or match in target_ids:
                return True

        return False


class BuildTagSieve(TargetSieve):
    """
    usage: ``(build-tag [TARGET...])``

    If no ``TARGET`` is specified, then matches tags which are used as
    the build tag for any target.

    If any ``TARGET`` patterns are specified, then matches tags which
    are used as the build tag for a target with a name matching any of
    the patterns.
    """

    name = "build-tag"


    def prep_targets(self, session, tagids):
        fn = lambda i: session.getBuildTargets(buildTagID=i)
        return iter_bulk_load(session, fn, tagids)


class DestTagSieve(TargetSieve):
    """
    usage: ``(dest-tag [TARGET...])``

    If no ``TARGET`` is specified, then matches tags which are used as
    the destination tag for any target.

    If any ``TARGET`` patterns are specified, then matches tags which
    are used as the destination tag for a target with a name matching
    any of the patterns.
    """

    name = "dest-tag"


    def prep_targets(self, session, tagids):
        fn = lambda i: session.getBuildTargets(destTagID=i)
        return iter_bulk_load(session, fn, tagids)


class InheritanceSieve(MatcherSieve):
    """
    Base class for inheritance-checking sieves. The ``prep_inheritance``
    method must be implemented to load the relevant inheritance links
    for the given predicate.
    """

    @abstractmethod
    def prep_inheritance(self, session, tagids):
        pass


    def prep(self, session, taginfos):
        needed = {}

        for tag in taginfos:
            cache = self.get_info_cache(tag)
            if "parents" not in cache:
                needed[tag["id"]] = cache

        for tid, parents in self.prep_inheritance(session, needed):
            cache = needed[tid]
            cache["tag_names"] = [t["name"] for t in parents]
            cache["tag_ids"] = [t["parent_id"] for t in parents]


    def check(self, session, taginfo):
        cache = self.get_info_cache(taginfo)
        tag_names = cache.get("tag_names", ())

        if not (self.tokens and tag_names):
            return bool(tag_names)

        tag_ids = cache.get("tag_ids", ())

        for match in self.tokens:
            if match in tag_names or match in tag_ids:
                return True

        return False


class HasParentSieve(InheritanceSieve):
    """
    usage: ``(has-parent [TAG...])``
    alias: ``(child-of [TAG...])``

    If no ``TAG`` patterns are specified, matches tags which have any
    parents.

    If ``TAG`` patterns are specified, matchs tags which have any
    direct parent matching any of the given patterns.
    """

    name = "has-parent"

    aliases = ["child-of", ]


    def prep_inheritance(self, session, tagids):
        return iter_bulk_load(session, session.getInheritanceData, tagids)


class HasAncestorSieve(InheritanceSieve):
    """
    usage: ``(has-ancestor [TAG...])``
    alias: ``(inherits-from [TAG...])``

    If no ``TAG`` patterns are specified, matches tags which have any
    parents.

    If ``TAG`` patterns are specified, matches tags which have a
    parent at any depth matching any of the given patterns.
    """

    name = "has-ancestor"

    aliases = ["inherits-from", ]


    def prep_inheritance(self, session, tagids):
        return iter_bulk_load(session, session.getFullInheritance, tagids)


class HasChildSieve(InheritanceSieve):
    """
    usage: ``(has-child [TAG...])``
    alias: ``(parent-of [TAG...])``

    If no ``TAG`` patterns are specified, matches tags which are the direct
    parent to any other tag.

    If ``TAG`` patterns are specified, matches tags which are the
    direct parent to any tag matching any of the given patterns.
    """

    name = "has-child"

    aliases = ["parent-of", ]


    def prep_inheritance(self, session, tagids):
        fn = lambda i: session.getFullInheritance(i, reverse=True)
        for tid, inher in iter_bulk_load(session, fn, tagids):
            yield tid, [p for p in inher if p["currdepth"] == 1]


class HasDescendantSieve(InheritanceSieve):
    """
    usage: ``(has-descendant [TAG...])``
    alias: ``(inherited-by [TAG...])``

    If no ``TAG`` patterns are specified, matches tags which are inherited
    by any other tag.

    If ``TAG`` patterns are specified, matches tags which are inherited by
    any tag matching any of the patterns, at any depth.
    """

    name = "has-descendant"

    aliases = ["inherited-by", ]


    def prep_inheritance(self, session, tagids):
        fn = lambda i: session.getFullInheritance(i, reverse=True)
        return iter_bulk_load(session, fn, tagids)


class NVRSieve(VariadicSieve):

    def __init__(self, sifter, nvr=None):
        if nvr is not None:
            nvr = ensure_int_or_str(nvr)

        super().__init__(sifter, nvr)

        self.build_id = None
        self.pkg_name = None


    @abstractmethod
    def prep_tagged(self, session, pkgname, tagids):
        pass


    @abstractmethod
    def prep_count(self, session, tagids):
        pass


    def prep(self, session, taginfos):
        pkg = self.pkg_name

        if pkg is None and self.tokens:
            bld = as_buildinfo(session, self.tokens[0])
            self.build_id = bld["id"]
            self.pkg_name = pkg = bld["name"]

        needed = {}
        for tag in taginfos:
            cache = self.get_info_cache(tag)
            if pkg not in cache:
                needed[tag["id"]] = cache

        if pkg is None:
            # we're not checking for any specific builds, just need a
            # count.
            for tid, found in self.prep_count(session, needed):
                cache = needed[tid]
                cache[pkg] = found, ()

        else:
            # need specific build IDs. count is unused but we may as
            # well gather it too, to be consistent
            for tid, found in self.prep_tagged(session, pkg, needed):
                cache = needed[tid]
                cache[pkg] = len(found), found


    def check(self, session, taginfo):
        pkg = self.pkg_name

        cache = self.get_info_cache(taginfo)
        count, found = cache[pkg]

        if pkg is None:
            return count > 0
        else:
            return self.build_id in found


class TaggedSieve(NVRSieve):
    """
    usage: ``(tagged [NVR...])``

    If no ``NVR`` is specified, matches tags which have any builds tagged
    in them.

    If ``NVR`` is specified, matches tags which have any of the given
    builds tagged in them. Each ``NVR`` must be a valid reference to a
    build in this koji instance, or a NoSuchBuild exception will be
    raised.
    """

    name = "tagged"


    def prep_tagged(self, session, pkgname, tagids):
        fn = lambda i: session.listTagged(i, package=pkgname,
                                          inherit=False, latest=False)
        for tid, blds in iter_bulk_load(session, fn, tagids):
            yield tid, [bld["id"] for bld in blds]


    def prep_count(self, session, tagids):
        fn = lambda i: session.count("listTagged", i,
                                     inherit=False, latest=False)
        return iter_bulk_load(session, fn, tagids)


class LatestSieve(NVRSieve):
    """
    usage: ``(latest [NVR...])``

    If no ``NVR`` is specified, matches tags which have any builds
    tagged in them or inherited from parent tags.

    If ``NVR`` is specified, matches tags which have any of the given
    builds as the latest inherited build of the relevant package name.
    Each ``NVR`` must be valid a reference to a build in this koji
    instance, or a NoSuchBuild exception will be raised.
    """

    name = "latest"


    def prep_tagged(self, session, pkgname, tagids):
        fn = lambda i: session.listTagged(i, package=pkgname,
                                          inherit=True, latest=True)
        for tid, blds in iter_bulk_load(session, fn, tagids):
            yield tid, [bld["id"] for bld in blds]


    def prep_count(self, session, tagids):
        fn = lambda i: session.count("listTagged", i,
                                     inherit=True, latest=True)
        return iter_bulk_load(session, fn, tagids)


class CompareLatestSieve(Sieve):
    """
    usage: ``(compare-latest PKG [OP VER])``

    If OP and VER are not specified, matches tags which have any build
    of the given package name as latest.

    If OP and VER are specified, matches tags which have the a latest
    build of the given package name which compare correctly. If tag
    doesn't have any build of the given package name, it will not
    match.
    """

    name = "compare-latest"


    def __init__(self, sifter, pkgname, op='>=', ver='0'):
        pkgname = ensure_str(pkgname)
        opfn = ensure_comparison(op)
        version = ensure_str(ver)

        super().__init__(sifter, pkgname, op, ver)

        if ":" in version:
            epoch, version = version.split(":", 1)
        else:
            epoch = "0"

        if "-" in version:
            version, release = version.split("-", 1)
        else:
            release = None

        self.pkgname = pkgname
        self.op = opfn
        self.epoch = epoch
        self.version = version
        self.release = release


    def prep(self, session, taginfos):
        pkgname = self.pkgname

        needed = {}
        for tag in taginfos:
            cache = self.get_info_cache(tag)
            if pkgname not in cache:
                needed[tag["id"]] = cache

        evr_getter = itemgetter("epoch", "version", "release")

        fn = lambda i: session.getLatestBuilds(i, package=pkgname)
        for tid, latest in iter_bulk_load(session, fn, needed):
            if latest:
                latest = evr_getter(latest[0])
                latest = tuple((str(x) if x else "0") for x in latest)

            cache = needed[tid]
            cache[pkgname] = latest or None


    def check(self, session, taginfo):
        other = self.get_info_cache(taginfo).get(self.pkgname)

        if other is None:
            return False

        ours = (self.epoch, self.version, self.release or other[2])

        relative = evr_compare(other, ours)
        return self.op(relative, 0)


class PkgListSieve(SymbolSieve, CacheMixin):

    def __init__(self, sifter, pkgname, *pkgnames):
        super().__init__(sifter, pkgname, *pkgnames)


    def prep(self, session, taginfos):
        self.bulk_list_packages(session, taginfos, True)


class PkgAllowedSieve(PkgListSieve):
    """
    usage: ``(pkg-allowed PKG [PKG...])``

    Matches tags which have a package listing with any of the given
    ``PKG`` contained therein and not blocked, honoring inheritance.
    """

    name = "pkg-allowed"


    def check(self, session, taginfo):
        pkgs = self.allowed_packages(session, taginfo["id"], True)
        for tok in self.tokens:
            if tok in pkgs:
                return True
        else:
            return False


class PkgBlockedSieve(PkgListSieve):
    """
    usage: ``(pkg-blocked PKG [PKG...])``

    Matches tags which have a package listing with any of the given
    ``PKG`` contained therein and blocked, honoring inheritance.
    """

    name = "pkg-blocked"


    def check(self, session, taginfo):
        pkgs = self.blocked_packages(session, taginfo["id"], True)
        for tok in self.tokens:
            if tok in pkgs:
                return True
        else:
            return False


class PkgUnlistedSieve(PkgListSieve):
    """
    usage: ``(pkg-unlisted PKG [PKG...])``

    Matches tags which have no package listing (neither allowed nor
    blocked) for any of the given ``PKG`` names. Honors inheritance.
    """

    name = "pkg-unlisted"


    def check(self, session, taginfo):
        allowed = self.allowed_packages(session, taginfo["id"], True)
        blocked = self.blocked_packages(session, taginfo["id"], True)

        for tok in self.tokens:
            if tok in allowed:
                continue
            elif tok in blocked:
                continue
            else:
                return True
        else:
            return False


class GroupSieve(SymbolSieve, CacheMixin):
    """
    usage: ``(group GROUP [GROUP...])``

    Matches tags which have any of the given install groups
    configured.  Honors inheritance.
    """

    name = "group"


    def __init__(self, sifter, group, *groups):
        super().__init__(sifter, group, *groups)


    def prep(self, session, taginfos):

        needed = {}
        for tag in taginfos:
            cache = self.get_info_cache(tag)
            if "group_names" not in cache:
                needed[tag["id"]] = cache

        loaded = self.bulk_get_tag_groups(session, needed)
        for tid, groups in loaded.items():
            cache = needed[tid]
            cache["group_names"] = [grp["name"] for grp in groups]


    def check(self, session, taginfo):
        cache = self.get_info_cache(taginfo)
        groups = cache.get("group_names", ())

        for tok in self.tokens:
            if tok in groups:
                return True
        else:
            return False


class GroupPkgSieve(SymbolSieve, CacheMixin):
    """
    usage: ``(group-pkg GROUP PKG [PKG...] [require_all: False])``

    Matches tags which have the given install group, which also
    contains any of the given ``PKG`` names
    """

    name = "group-pkg"


    def __init__(self, sifter, group, pkg, *pkgs, require_all=False):
        super().__init__(sifter, pkg, *pkgs, require_all=require_all)
        self.group = ensure_symbol(group)
        self.require_all = bool(require_all)


    def prep(self, session, taginfos):

        needed = {}
        for tag in taginfos:
            cache = self.get_info_cache(tag)
            if "group_pkgs" not in cache:
                needed[tag["id"]] = cache

        loaded = self.bulk_get_tag_groups(session, needed)
        for tid, groups in loaded.items():
            cache = needed[tid]
            cache["group_pkgs"] = simple_groups = {}
            for grp in groups:
                name = grp["name"]
                pkglist = grp.get("packagelist", ())
                simple_groups[name] = [p["package"] for p in pkglist]


    def check(self, session, taginfo):
        cache = self.get_info_cache(taginfo)
        groups = cache.get("group_pkgs")

        pkgs = groups.get(self.group)
        if not pkgs:
            return False

        if self.require_all:
            # require all tokens to be present
            for tok in self.tokens:
                if tok not in pkgs:
                    return False
            else:
                return True

        else:
            # if any token is present, we match
            for tok in self.tokens:
                if tok in pkgs:
                    return True
            else:
                return False


DEFAULT_TAG_INFO_SIEVES: List[Type[Sieve]] = [
    ArchSieve,
    BuildTagSieve,
    CompareLatestSieve,
    DestTagSieve,
    ExactArchSieve,
    HasAncestorSieve,
    HasChildSieve,
    HasDescendantSieve,
    HasParentSieve,
    GroupPkgSieve,
    GroupSieve,
    LatestSieve,
    LockedSieve,
    NameSieve,
    PermissionSieve,
    PkgAllowedSieve,
    PkgBlockedSieve,
    PkgUnlistedSieve,
    TaggedSieve,
]


def tag_info_sieves() -> List[Type[Sieve]]:
    """
    A new list containing the default tag-info sieve classes.

    This function is used by `tag_info_sifter` when creating its
    `Sifter` instance.
    """

    sieves: List[Type[Sieve]] = []
    sieves.extend(DEFAULT_SIEVES)
    sieves.extend(DEFAULT_TAG_INFO_SIEVES)

    return sieves


def tag_info_sifter(
        source: str,
        params: Dict[str, str] = None) -> Sifter:
    """
    Create a Sifter from the source using the default tag-info
    Sieves.

    :param source: sieve expressions source

    :param params: sieve parameters
    """

    return Sifter(tag_info_sieves(), source, "id", params)


def sift_tags(
        session: ClientSession,
        src_str: str,
        tag_infos: TagInfos,
        params: Dict[str, str] = None) -> Dict[str, List[TagInfo]]:
    """
    :param session: an active koji client session

    :param src_str: sieve expressions source

    :param build_infos: list of tag info dicts to filter

    :param params: sieve parameters

    :returns: mapping of flags to matching tag info dicts
    """

    sifter = tag_info_sifter(src_str, params)
    return sifter(session, tag_infos)


def sift_tagnames(
        session: ClientSession,
        src_str: str,
        names: Iterable[Union[int, str]],
        params: Dict[str, str] = None) -> Dict[str, List[TagInfo]]:
    """
    :param session: an active koji client session

    :param src_str: sieve expressions source

    :param names: list of tag names to load and filter

    :param params: sieve parameters

    :returns: mapping of flags to matching tag info dicts
    """

    loaded = bulk_load_tags(session, names, err=False)
    tags = tag_dedup(loaded.values())
    return sift_tags(session, src_str, tags, params)


#
# The end.
