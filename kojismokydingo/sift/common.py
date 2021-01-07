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

from operator import itemgetter
from six.moves import map

from . import SifterError, Sieve
from ..builds import latest_maven_builds


__all__ = ("CacheMixin", "ensure_comparison", )


_OPMAP = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}


def ensure_comparison(value):
    """
    Converts a comparison operator symbol into a comparison function.

    :param value: The symbol or string to convert. Should be one of
      '==', '!=', '>', '>=', '<', '<='

    :type value: str

    :rtype: callable
    """

    if value in _OPMAP:
        return _OPMAP[value]

    else:
        msg = "Invalid comparison operator: %r" % value
        raise SifterError(msg)


class CacheMixin(Sieve):
    """
    Mixin providing some caching interfaces to various koji calls.
    These will store cached results on the instance's sifter. The
    cache is cleared when the sifter's `reset` method is invoked.
    """

    def _mixin_cache(self, name):
        return self.sifter.get_cache("*mixin", name)


    def latest_builds(self, session, tag_id, inherit=True):
        """
        a caching wrapper for session.getLatestBuilds

        :rtype: list[dict]
        """

        cache = self._mixin_cache("latest_builds")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            found = session.getLatestBuilds(tag_id)
            cache[key] = found

        return found


    def latest_build_ids(self, session, tag_id, inherit=True):
        """
        a caching wrapper for session.getLatestBuilds which returns a set
        containing only the build IDs

        :rtype: set[int]
        """

        cache = self._mixin_cache("latest_build_ids")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            blds = self.latest_builds(session, tag_id, inherit)
            found = cache[key] = set(map(itemgetter("id"), blds))

        return found


    def latest_builds_by_name(self, session, tag_id, inherit=True):
        """
        a caching wrapper for session.getLatestBuilds which returns a dict
        mapping the build names to the build info

        :rtype: dict[str, dict]
        """

        cache = self._mixin_cache("latest_builds_by_name")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            blds = self.latest_builds(session, tag_id, inherit)
            found = cache[key] = dict((b["name"], b) for b in blds)

        return found


    def latest_maven_builds(self, session, tag_id, inherit=True):
        """
        a caching wrapper for `kojismokydingo.builds.latest_maven_builds`

        :rtype: dict[tuple[str], dict]
        """

        cache = self._mixin_cache("latest_maven_builds")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            found = latest_maven_builds(session, tag_id, inherit=inherit)
            cache[key] = found

        return found


    def latest_maven_build_ids(self, session, tag_id, inherit=True):
        """
        a caching wrapper for `kojismokydingo.builds.latest_maven_builds`
        which returns a set containing only the build IDs

        :rtype: set[int]
        """

        cache = self._mixin_cache("latest_maven_build_ids")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            blds = self.latest_maven_builds(session, tag_id, inherit)
            found = cache[key] = set(map(itemgetter("id"), blds))

        return found


    def list_packages(self, session, tag_id, inherited=True):
        """
        a caching wrapper for session.listPackages

        :rtype: list[dict]
        """

        cache = self._mixin_cache("list_packages")

        key = (tag_id, inherited)
        found = cache.get(key)

        if found is None:
            found = cache[key] = session.listPackages(tag_id, inherited=True)

        return found


    def allowed_packages(self, session, tag_id, inherited=True):
        """
        a caching wrapper for session.listPackages which returns a set
        containing only the package names which are not blocked.

        :rtype: set[str]
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


    def blocked_packages(self, session, tag_id, inherited=True):
        """
        a caching wrapper for session.listPackages which returns a set
        containing only the package names which are blocked.

        :rtype: set[str]
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


# The end.
