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


from six import iteritems, itervalues

from . import (
    DEFAULT_SIEVES,
    ItemSieve, MatcherSieve, Sieve, Sifter, SymbolSieve,
    ensure_all_matcher, ensure_all_symbol, )
from .. import (
    bulk_load_tags, )
from ..tags import (
    gather_tag_ids, tag_dedup, )


__all__ = (
    "DEFAULT_TAG_INFO_SIEVES",

    "tag_info_sieves",
    "tag_info_sifter",
    "sift_tags",
    "sift_tagnames",
)


class NameSieve(ItemSieve):
    """
    Usage: ``(name NAME [NAME...])``

    filters for dict infos whose `name` key matches any of the given
    NAME matchers.
    """

    name = field = "name"


class ArchSieve(MatcherSieve):
    """
    usage: ``(arch [ARCH...])``

    If no ARCH patterns are specified, matches tags which have any
    architectures at all.

    If ARCH patterns are specified, then only matches tags which have
    an architecture that matches any of the given patterns.
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

    If no ARCH names are specified, matches only tags which have no
    architectures.

    If ARCH names are specified, they must be specified as symbols.
    Only matches tags which have the exact same set of architectures.
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
        super(LockedSieve, self).__init__(sifter)


    def check(self, session, taginfo):
        return taginfo["locked"]


class PermissionSieve(MatcherSieve):
    """
    usage: ``(permission [PERM...])```

    If no PERM is specified, then matches tags which have any non-None
    permission set.

    If any PERM patters are specified, then matches tags which have
    any of the listed permissions set.
    """

    name = "permission"


    def check(self, session, taginfo):
        return (taginfo["perm"] in self.tokens or
                taginfo["perm_id"] in self.tokens)


class BuildTagSieve(MatcherSieve):
    """
    usage: ``(build-tag [TARGET...])``

    If no TARGET is specified, then matches tags which are used as the build
    tag for any target.

    If any TARGET patterns are specified, then matches tags which are
    used as the build tag for a target with a name matching any of the
    patterns.
    """

    name = "build-tag"


    def prep(self, session, taginfos):
        pass


    def check(self, session, taginfo):
        pass


class DestTagSieve(MatcherSieve):
    """
    usage: ``(dest-tag [TARGET...])``

    If no TARGET is specified, then matches tags which are used as the
    destination tag for any target.

    If any TARGET patterns are specified, then matches tags which are
    used as the destination tag for a target with a name matching any
    of the patterns.
    """

    name = "dest-tag"


    def prep(self, session, taginfos):
        pass


    def check(self, session, taginfo):
        pass


DEFAULT_TAG_INFO_SIEVES = [
    ArchSieve,
    ExactArchSieve,
    LockedSieve,
    NameSieve,
    PermissionSieve,
]


def tag_info_sieves():
    """
    A new list containing the default tag-info sieve classes.

    This function is used by `tag_info_sifter` when creating its
    `Sifter` instance.

    :rtype: list[type[Sieve]]
    """

    sieves = []
    sieves.extend(DEFAULT_SIEVES)
    sieves.extend(DEFAULT_TAG_INFO_SIEVES)

    return sieves


def tag_info_sifter(source, params=None):
    """
    Create a Sifter from the source using the default tag-info
    Sieves.

    :param source: sieve expressions source
    :type source: stream or str

    :rtype: Sifter
    """

    return Sifter(tag_info_sieves(), source, "id", params)


def sift_tags(session, src_str, tag_infos, params=None):
    """
    :param src_str: sieve expressions source
    :type src_str: src

    :param build_infos: list of tag info dicts to filter
    :type build_infos: list[dict]

    :rtype: dict[str,list[dict]]
    """

    sifter = tag_info_sifter(src_str, params)
    return sifter(session, tag_infos)


def sift_tagnames(session, src_str, names, params=None):
    """
    :param src_str: sieve expressions source
    :type src_str: src

    :param nvrs: list of tag names to load and filter
    :type nvrs: list[str]

    :rtype: dict[str,list[dict]]
    """

    loaded = bulk_load_tags(session, names, err=False)
    tags = tag_dedup(itervalues(loaded))
    return sift_tags(session, src_str, tags, params)


#
# The end.
