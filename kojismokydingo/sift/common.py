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
sieves

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from operator import itemgetter
from six.moves import map

from . import Sieve
from ..builds import latest_maven_builds


__all__ = ("CacheMixin", )


class CacheMixin(Sieve):
    """
    Mixin providing some caching interfaces to various koji calls.
    These will store cached results on the instance's sifter. The
    cache is cleared when the sifter's `reset` method is invoked.
    """

    def _mixin_cache(self, name):
        return self.sifter.get_cache("*mixin", name)


    def latest_builds(self, session, tag_id, inherit=True):
        cache = self._mixin_cache("latest_builds")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            found = session.getLatestBuilds(tag_id)
            cache[key] = found

        return found


    def latest_build_ids(self, session, tag_id, inherit=True):
        cache = self._mixin_cache("latest_build_ids")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            blds = self.latest_builds(session, tag_id, inherit)
            found = cache[key] = set(map(itemgetter("id"), blds))

        return found


    def latest_builds_by_name(self, session, tag_id, inherit=True):
        cache = self._mixin_cache("latest_builds_by_name")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            blds = self.latest_builds(session, tag_id, inherit)
            found = cache[key] = dict((b["name"], b) for b in blds)

        return found


    def latest_maven_builds(self, session, tag_id, inherit=True):
        cache = self._mixin_cache("latest_maven_builds")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            found = latest_maven_builds(session, tag_id, inherit=inherit)
            cache[key] = found

        return found


    def latest_maven_build_ids(self, session, tag_id, inherit=True):
        cache = self._mixin_cache("latest_maven_build_ids")

        key = (tag_id, inherit)
        found = cache.get(key)

        if found is None:
            blds = self.latest_maven_builds(session, tag_id, inherit)
            found = cache[key] = set(map(itemgetter("id"), blds))

        return found


    def list_packages(self, session, tag_id, inherited=True):
        cache = self._mixin_cache("list_packages")

        key = (tag_id, inherited)
        found = cache.get(key)

        if found is None:
            found = cache[key] = session.listPackages(tag_id, inherited=True)

        return found


    def allowed_packages(self, session, tag_id, inherited=True):
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
