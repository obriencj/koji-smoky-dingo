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


from pkg_resources import EntryPoint
from six import iteritems
from unittest import TestCase


ENTRY_POINTS = {
    "ksd-filter-builds": "kojismokydingo.standalone.builds:ksd_filter_builds",
    "ksd-filter-tags": "kojismokydingo.standalone.tags:ksd_filter_tags",
}


class TestExpectedStandalone(TestCase):

    def test_entry_points(self):
        # verify the expected entry points resolve and can be
        # initialized
        for nameref in iteritems(ENTRY_POINTS):
            cmd = "=".join(nameref)
            ep = EntryPoint.parse(cmd)

            if hasattr(ep, "resolve"):
                #new environments
                cmd_inst = ep.resolve()
            else:
                # old environments
                cmd_inst = ep.load(require=False)

            self.assertTrue(callable(cmd_inst))


#
# The end.
