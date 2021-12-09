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
Koji Smoky Dingo - Koji-specific utilities for working with Sifty
Sieves

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import operator

from koji import ClientSession
from operator import itemgetter
from typing import Any, Callable, Dict, Iterable, List, Set, Tuple, cast

from . import SifterError, Sieve
from .. import iter_bulk_load
from ..builds import GAV, latest_maven_builds
from ..types import (
    BuildInfo, TagGroupInfo, TagPackageInfo, )


__all__ = ("CacheMixin", "ensure_comparison", )


_OPMAP = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}


def ensure_comparison(value: str) -> Callable[[Any, Any], bool]:
    """
    Converts a comparison operator symbol into a comparison function.

    :param value: The symbol or string to convert. Should be one of
      '==', '!=', '>', '>=', '<', '<='

    :raises SifterError: if the value isn't one of the known operators
    """

    if value in _OPMAP:
        return _OPMAP[value]

    else:
        raise SifterError(f"Invalid comparison operator: {value!r}")


class CacheMixin(Sieve):
    """
    Mixin providing some caching interfaces to various koji calls.
    These will store cached results on the instance's sifter. The
    cache is cleared when the sifter's `reset` method is invoked.
    """

    def _mixin_cache(self, name: str) -> dict:
        return self.sifter.get_cache("*mixin", name)


    def latest_builds(
            self,
            session: ClientSession,
            tag_id: int,
            inherit: bool = True) -> List[BuildInfo]:
        """
        a caching wrapper for ``session.getLatestBuilds``
        """

        cache = self._mixin_cache("latest_builds")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            found = session.getLatestBuilds(tag_id)
            cache[key] = found

        return found


    def latest_build_ids(
            self,
            session: ClientSession,
            tag_id: int,
            inherit: bool = True) -> Set[int]:
        """
        a caching wrapper for ``session.getLatestBuilds`` which returns a
        set containing only the build IDs
        """

        cache = self._mixin_cache("latest_build_ids")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            blds = self.latest_builds(session, tag_id, inherit)
            found = cache[key] = set(map(itemgetter("id"), blds))

        return found


    def latest_builds_by_name(
            self,
            session: ClientSession,
            tag_id: int,
            inherit: bool = True) -> Dict[str, BuildInfo]:
        """
        a caching wrapper for session.getLatestBuilds which returns a dict
        mapping the build names to the build info
        """

        cache = self._mixin_cache("latest_builds_by_name")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            blds = self.latest_builds(session, tag_id, inherit)
            found = cache[key] = {b["name"]: b for b in blds}

        return found


    def latest_maven_builds(
            self,
            session: ClientSession,
            tag_id: int,
            inherit: bool = True) -> Dict[GAV, BuildInfo]:
        """
        a caching wrapper for `kojismokydingo.builds.latest_maven_builds`
        """

        cache = self._mixin_cache("latest_maven_builds")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            found = latest_maven_builds(session, tag_id, inherit=inherit)
            cache[key] = found

        return found


    def latest_maven_build_ids(
            self,
            session: ClientSession,
            tag_id: int,
            inherit: bool = True) -> Set[int]:
        """
        a caching wrapper for `kojismokydingo.builds.latest_maven_builds`
        which returns a set containing only the build IDs
        """

        cache = self._mixin_cache("latest_maven_build_ids")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            blds = self.latest_maven_builds(session, tag_id, inherit)
            found = cache[key] = set(map(itemgetter("id"), blds))

        return found


    def bulk_list_packages(
            self,
            session: ClientSession,
            tag_ids: Iterable[int],
            inherited: bool = True) -> Dict[int, List[TagPackageInfo]]:
        """
        a multicall caching wrapper for ``session.listPackages``

        shares the same cache as `list_packages` (and therefore
        `allowed_packages` and `blocked_packages`)
        """

        cache = cast(Dict[Tuple[int, bool], List[TagPackageInfo]],
                     self._mixin_cache("list_packages"))

        result: Dict[int, List[TagPackageInfo]] = {}
        needed = []

        for tid in tag_ids:
            if (tid, inherited) not in cache:
                needed.append(tid)
            else:
                result[tid] = cache[(tid, inherited)]

        fn = lambda i: session.listPackages(i, inherited=inherited)
        for tid, pkgs in iter_bulk_load(session, fn, needed):
            result[tid] = cache[(tid, inherited)] = pkgs

        return result


    def list_packages(
            self,
            session: ClientSession,
            tag_id: int,
            inherited: bool = True) -> List[TagPackageInfo]:
        """
        a caching wrapper for ``session.listPackages``
        """

        cache = self._mixin_cache("list_packages")

        key = (tag_id, inherited)
        found = cache.get(key)

        if found is None:
            found = cache[key] = session.listPackages(tag_id,
                                                      inherited=inherited)

        return found


    def allowed_packages(
            self,
            session: ClientSession,
            tag_id: int,
            inherited: bool = True) -> Set[str]:
        """
        a caching wrapper for ``session.listPackages`` which returns a set
        containing only the package names which are not blocked.
        """

        cache = self._mixin_cache("allowed_packages")

        key = (tag_id, inherited)
        found = cache.get(key)

        if found is None:
            found = cache[key] = set()

            for pkg in self.list_packages(session, tag_id, inherited):
                if not pkg["blocked"]:
                    found.add(pkg["package_name"])

        return found


    def blocked_packages(
            self,
            session: ClientSession,
            tag_id: int,
            inherited: bool = True) -> Set[str]:
        """
        a caching wrapper for ``session.listPackages`` which returns a set
        containing only the package names which are blocked.
        """

        cache = self._mixin_cache("blocked_packages")

        key = (tag_id, inherited)
        found = cache.get(key)

        if found is None:
            found = cache[key] = set()

            for pkg in self.list_packages(session, tag_id, inherited):
                if pkg["blocked"]:
                    found.add(pkg["package_name"])

        return found


    def get_tag_groups(
            self,
            session: ClientSession,
            tag_id: int) -> List[TagGroupInfo]:
        """
        a caching wrapper for ``session.getTagGroups``
        """

        cache = self._mixin_cache("groups")

        found = cache.get(tag_id)
        if found is None:
            found = cache[tag_id] = session.getTagGroups(tag_id)

        return found


    def bulk_get_tag_groups(
            self,
            session: ClientSession,
            tag_ids: Iterable[int]) -> Dict[int, List[TagGroupInfo]]:
        """
        a multicall caching wrapper for ``session.getTagGroups``. Shares a
        cache with `get_tag_groups`
        """

        cache = self._mixin_cache("groups")

        result = {}
        needed = []

        for tid in tag_ids:
            if tid in cache:
                result[tid] = cache[tid]
            else:
                needed.append(tid)

        fn = session.getTagGroups
        for tid, found in iter_bulk_load(session, fn, needed):
            result[tid] = cache[tid] = found

        return result


#
# The end.
