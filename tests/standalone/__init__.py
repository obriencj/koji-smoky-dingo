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


from sys import version_info
from unittest import TestCase


if version_info < (3, 11):
    from pkg_resources import EntryPoint
else:
    from importlib.metadata import EntryPoint


ENTRY_POINTS = {
    "ksd-filter-builds": "kojismokydingo.standalone.builds:ksd_filter_builds",
    "ksd-filter-tags": "kojismokydingo.standalone.tags:ksd_filter_tags",
}


def get_entry_point(name, group="koji_smoky_dingo"):
    ref = ENTRY_POINTS[name]

    if version_info < (3, 11):
        return EntryPoint.parse("=".join((name, ref)))
    else:
        return EntryPoint(group=group, name=name, value=ref)


def entry_point_load(ep):
    if version_info < (3, 11):
        return ep.resolve()
    else:
        return ep.load()


class TestExpectedStandalone(TestCase):

    def test_entry_points(self):
        # verify the expected entry points resolve and can be
        # initialized
        for name in ENTRY_POINTS:
            ep = get_entry_point(name)
            cmd_inst = entry_point_load(ep)

            self.assertTrue(callable(cmd_inst))


#
# The end.
