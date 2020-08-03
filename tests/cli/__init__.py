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

from kojismokydingo.cli import SmokyDingo


ENTRY_POINTS = [
    "affected-targets = kojismokydingo.cli.tags:AffectedTargets",
    "bulk-tag-builds = kojismokydingo.cli.builds:BulkTagBuilds",
    "check-hosts = kojismokydingo.cli.hosts:CheckHosts",
    "client-config = kojismokydingo.cli.clients:ClientConfig",
    "latest-archives = kojismokydingo.cli.archives:LatestArchives",
    "list-build-archives = kojismokydingo.cli.archives:ListBuildArchives",
    "list-cgs = kojismokydingo.cli.users:ListCGs",
    "list-imported = kojismokydingo.cli.builds:ListImported",
    "list-tag-rpm-macros = kojismokydingo.cli.tags:ListTagRPMMacros",
    "perminfo = kojismokydingo.cli.users:PermissionInfo",
    "remove-tag-rpm-macro = kojismokydingo.cli.tags:RemoveTagRPMMacro",
    "renum-tag-inheritance = kojismokydingo.cli.tags:RenumTagInheritance",
    "set-tag-rpm-macro = kojismokydingo.cli.tags:SetTagRPMMacro",
    "swap-tag-inhertance = kojismokydingo.cli.tags:SwapTagInheritance",
    "userinfo = kojismokydingo.cli.users:UserInfo",
]


class TestCommands(TestCase):

    def test_entry_points(self):
        # verify the expected entry points resolve and can be
        # initialized
        for cmd in ENTRY_POINTS:
            ep = EntryPoint.parse(cmd)

            cmd_cls = ep.resolve()
            self.assertTrue(issubclass(cmd_cls, SmokyDingo))

            cmd_inst = cmd_cls(ep.name)
            self.assertTrue(isinstance(cmd_inst, SmokyDingo))


#
# The end.
