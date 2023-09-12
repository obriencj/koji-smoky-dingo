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
from unittest import TestCase

from kojismokydingo.cli import AnonSmokyDingo

from . import ENTRY_POINTS


class TestMetaPlugin(TestCase):


    def test_handlers_exist(self):
        import koji_cli_plugins.kojismokydingometa as ksdmeta

        # verify the expected entry points resolve and can be
        # initialized
        for name, ref in ENTRY_POINTS.items():
            cmd = f"{name}={ref}"
            ep = EntryPoint.parse(cmd)

            cmd_cls = ep.resolve()
            cmd_inst = cmd_cls(name)

            if not (cmd_inst and getattr(cmd_inst, "enabled", True)):
                # we have to check for the enabled setting here
                # because of repoquery in particular which will
                # disable itself if it cannot find dnf
                continue

            if issubclass(cmd_cls, AnonSmokyDingo):
                name = "anon_handle_" + name.replace("-", "_")
            else:
                name = "handle_" + name.replace("-", "_")

            found = getattr(ksdmeta, name)
            self.assertTrue(isinstance(found, cmd_cls))


# The end.
