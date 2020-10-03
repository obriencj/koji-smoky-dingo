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
from six.moves import StringIO
from unittest import TestCase

from kojismokydingo.cli import (
    SmokyDingo, clean_lines, resplit, space_normalize, tabulate)


ENTRY_POINTS = {
    "affected-targets": "kojismokydingo.cli.tags:AffectedTargets",
    "block-env-var": "kojismokydingo.cli.tags:BlockEnvVar",
    "block-rpm-macro": "kojismokydingo.cli.tags:BlockRPMMacro",
    "bulk-tag-builds": "kojismokydingo.cli.builds:BulkTagBuilds",
    "cginfo": "kojismokydingo.cli.users:CGInfo",
    "check-hosts": "kojismokydingo.cli.hosts:CheckHosts",
    "client-config": "kojismokydingo.cli.clients:ClientConfig",
    "filter-builds": "kojismokydingo.cli.builds:FilterBuilds",
    "latest-archives": "kojismokydingo.cli.archives:LatestArchives",
    "list-btypes": "kojismokydingo.cli.builds:ListBTypes",
    "list-build-archives": "kojismokydingo.cli.archives:ListBuildArchives",
    "list-cgs": "kojismokydingo.cli.builds:ListCGs",
    "list-component-builds": "kojismokydingo.cli.builds:ListComponents",
    "list-env-vars": "kojismokydingo.cli.tags:ListEnvVars",
    "list-rpm-macros": "kojismokydingo.cli.tags:ListRPMMacros",
    "list-tag-extras": "kojismokydingo.cli.tags:ListTagExtras",
    "perminfo": "kojismokydingo.cli.users:PermissionInfo",
    "remove-env-var": "kojismokydingo.cli.tags:RemoveEnvVar",
    "remove-rpm-macro": "kojismokydingo.cli.tags:RemoveRPMMacro",
    "renum-tag-inheritance": "kojismokydingo.cli.tags:RenumTagInheritance",
    "set-env-var": "kojismokydingo.cli.tags:SetEnvVar",
    "set-rpm-macro": "kojismokydingo.cli.tags:SetRPMMacro",
    "swap-tag-inheritance": "kojismokydingo.cli.tags:SwapTagInheritance",
    "userinfo": "kojismokydingo.cli.users:UserInfo",
}


def default_koji_config(profile="koji"):
    return {
        'profile': profile,
        'server': 'http://localhost/kojihub',
        'weburl': 'http://localhost/koji',
        'topurl': None,
        'pkgurl': None,
        'topdir': '/mnt/koji',
        'max_retries': None,
        'retry_interval': None,
        'anon_retry': None,
        'offline_retry': None,
        'offline_retry_interval': None,
        'timeout': 60 * 60 * 12,
        'auth_timeout': 60,
        'use_fast_upload': False,
        'upload_blocksize': 1048576,
        'poll_interval': 6,
        'principal': None,
        'keytab': None,
        'cert': None,
        'serverca': None,
        'no_ssl_verify': False,
        'authtype': None,
        'debug': False,
        'debug_xmlrpc': False,
        'pyver': None,
        'plugin_paths': None,
    }


class Object(object):
    pass


def default_koji_goptions(profile="koji"):
    result = Object()
    result.__dict__ = default_koji_config(profile)
    return result


class TestExpectedEntryPoints(TestCase):


    def test_entry_points(self):
        # verify the expected entry points resolve and can be
        # initialized
        for nameref in iteritems(ENTRY_POINTS):
            cmd = "=".join(nameref)
            ep = EntryPoint.parse(cmd)

            if hasattr(ep, "resolve"):
                #new environments
                cmd_cls = ep.resolve()
            else:
                # old environments
                cmd_cls = ep.load(require=False)

            self.assertTrue(issubclass(cmd_cls, SmokyDingo))

            cmd_inst = cmd_cls(ep.name)
            self.assertTrue(isinstance(cmd_inst, SmokyDingo))


class TestUtils(TestCase):


    def test_resplit(self):
        data = ["a", "b,c", "", "d,", ",e", "f, g, h", ",", "i", "  "]
        expect = list("abcdefghi")

        self.assertEqual(resplit(data), expect)


    def test_clean_lines(self):
        data = [
            "This is a  ",
            "# skip me",
            "list of strings  # yup",
            "",
            "  We are testing #",
            "     for cleaning up   ",
            "     ",
            "#long pause",
            "#",
            " #",
            " # ",
            "Thanks",
        ]

        expect_1 = [
            "This is a",
            "list of strings",
            "We are testing",
            "for cleaning up",
            "Thanks",
        ]
        self.assertEqual(clean_lines(data, True), expect_1)

        expect_2 = [
            "This is a",
            "# skip me",
            "list of strings  # yup",
            "We are testing #",
            "for cleaning up",
            "#long pause",
            "#",
            "#",
            "#",
            "Thanks",
        ]
        self.assertEqual(clean_lines(data, False), expect_2)

        self.assertEqual(clean_lines(expect_1, True), expect_1)
        self.assertEqual(clean_lines(expect_2, True), expect_1)
        self.assertEqual(clean_lines(expect_2, False), expect_2)


    def test_space_normalize(self):
        data = """
        This is a
        big mess of a string with    all   sorts\tof whitespace
        in it.

        """

        expect = ("This is a big mess of a string with all sorts of"
                  " whitespace in it.")

        self.assertEqual(space_normalize(data), expect)
        self.assertEqual(space_normalize(expect), expect)


class TestTabulate(TestCase):


    def do_tabulate(self, **kwds):

        headings = ("Heading 1", "Heading 2", "Heading 3")

        data = (
            ("Foo", "Bar", "Baz"),
            (1, 2, 3),
            ("Hello", None, None),
            ("", "''", Ellipsis),
        )

        out = StringIO()
        tabulate(headings, data, out=out, **kwds)
        return out.getvalue()


    def test_quiet(self):

        result = self.do_tabulate(quiet=True)

        expected = ("Foo    Bar   Baz     \n"
                    "1      2     3       \n"
                    "Hello  None  None    \n"
                    "       ''    Ellipsis\n")

        self.assertEqual(expected, result)


    def test_non_quiet(self):

        result = self.do_tabulate(quiet=False)

        expected = ("Heading 1  Heading 2  Heading 3\n"
                    "---------  ---------  ---------\n"
                    "Foo        Bar        Baz      \n"
                    "1          2          3        \n"
                    "Hello      None       None     \n"
                    "           ''         Ellipsis \n")

        self.assertEqual(expected, result)


#
# The end.
