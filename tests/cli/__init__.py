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


from io import StringIO
from pkg_resources import EntryPoint
from unittest import TestCase
from unittest.mock import patch

from kojismokydingo.cli import (
    SmokyDingo, clean_lines, int_or_str,
    print_history_results, resplit, space_normalize, tabulate)


ENTRY_POINTS = {
    "affected-targets": "kojismokydingo.cli.tags:AffectedTargets",
    "block-env-var": "kojismokydingo.cli.tags:BlockEnvVar",
    "block-rpm-macro": "kojismokydingo.cli.tags:BlockRPMMacro",
    "bulk-move-builds": "kojismokydingo.cli.builds:BulkMoveBuilds",
    "bulk-tag-builds": "kojismokydingo.cli.builds:BulkTagBuilds",
    "bulk-untag-builds": "kojismokydingo.cli.builds:BulkUntagBuilds",
    "cginfo": "kojismokydingo.cli.users:ShowCGInfo",
    "check-hosts": "kojismokydingo.cli.hosts:CheckHosts",
    "check-repo": "kojismokydingo.cli.tags:CheckRepo",
    "client-config": "kojismokydingo.cli.clients:ClientConfig",
    "filter-builds": "kojismokydingo.cli.builds:FilterBuilds",
    "filter-tags": "kojismokydingo.cli.tags:FilterTags",
    "latest-archives": "kojismokydingo.cli.archives:LatestArchives",
    "list-btypes": "kojismokydingo.cli.builds:ListBTypes",
    "list-build-archives": "kojismokydingo.cli.archives:ListBuildArchives",
    "list-cgs": "kojismokydingo.cli.builds:ListCGs",
    "list-component-builds": "kojismokydingo.cli.builds:ListComponents",
    "list-env-vars": "kojismokydingo.cli.tags:ListEnvVars",
    "list-rpm-macros": "kojismokydingo.cli.tags:ListRPMMacros",
    "list-tag-extras": "kojismokydingo.cli.tags:ListTagExtras",
    "open": "kojismokydingo.cli.clients:ClientOpen",
    "perminfo": "kojismokydingo.cli.users:ShowPermissionInfo",
    "remove-env-var": "kojismokydingo.cli.tags:RemoveEnvVar",
    "remove-rpm-macro": "kojismokydingo.cli.tags:RemoveRPMMacro",
    "renum-tag-inheritance": "kojismokydingo.cli.tags:RenumTagInheritance",
    "set-env-var": "kojismokydingo.cli.tags:SetEnvVar",
    "set-rpm-macro": "kojismokydingo.cli.tags:SetRPMMacro",
    "swap-tag-inheritance": "kojismokydingo.cli.tags:SwapTagInheritance",
    "userinfo": "kojismokydingo.cli.users:ShowUserInfo",
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


class GOptions(object):
    def __init__(self, profile="koji"):
        self.__dict__ = default_koji_config(profile)


class TestExpectedEntryPoints(TestCase):


    def test_entry_points(self):
        # verify the expected entry points resolve and can be
        # initialized
        for nameref in ENTRY_POINTS.items():
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


    def test_int_or_str(self):
        data = "hello"
        res = int_or_str(data)
        self.assertTrue(isinstance(res, str))
        self.assertEqual(res, data)
        self.assertTrue(res is data)

        data = "123 Hello"
        res = int_or_str(data)
        self.assertTrue(isinstance(res, str))
        self.assertEqual(res, data)
        self.assertTrue(res is data)

        data = "123 456"
        res = int_or_str(data)
        self.assertTrue(isinstance(res, str))
        self.assertEqual(res, data)
        self.assertTrue(res is data)

        data = "123"
        res = int_or_str(data)
        self.assertTrue(isinstance(res, int))
        self.assertEqual(res, 123)

        data = "0"
        res = int_or_str(data)
        self.assertTrue(isinstance(res, int))
        self.assertEqual(res, 0)


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


HIST_DATA = {
    'build_target_config': [],
    'group_config': [
        {'active': True,
         'biarchonly': False,
         'blocked': False,
         'create_event': 11030897,
         'create_ts': 1429100033.05122,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'description': None,
         'display_name': 'maven-build',
         'exported': True,
         'group.name': 'maven-build',
         'group_id': 103,
         'is_default': None,
         'langonly': None,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792,
         'uservisible': True}],
    'group_package_listing': [
        {'active': True,
         'basearchonly': None,
         'blocked': False,
         'create_event': 11030898,
         'create_ts': 1429100061.87492,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'group.name': 'maven-build',
         'group_id': 103,
         'package': 'bash',
         'requires': None,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792,
         'type': 'default'},
        {'active': True,
         'basearchonly': None,
         'blocked': False,
         'create_event': 11030899,
         'create_ts': 1429100062.6599,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'group.name': 'maven-build',
         'group_id': 103,
         'package': 'coreutils',
         'requires': None,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792,
         'type': 'default'},
        {'active': True,
         'basearchonly': None,
         'blocked': False,
         'create_event': 11030900,
         'create_ts': 1429100063.13539,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'group.name': 'maven-build',
         'group_id': 103,
         'package': 'git',
         'requires': None,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792,
         'type': 'default'},
        {'active': True,
         'basearchonly': None,
         'blocked': False,
         'create_event': 11030901,
         'create_ts': 1429100063.5119,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'group.name': 'maven-build',
         'group_id': 103,
         'package': 'java-1.7.0-openjdk-devel',
         'requires': None,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792,
         'type': 'default'},
        {'active': True,
         'basearchonly': None,
         'blocked': False,
         'create_event': 11030902,
         'create_ts': 1429100063.94641,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'group.name': 'maven-build',
         'group_id': 103,
         'package': 'liberation-mono-fonts',
         'requires': None,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792,
         'type': 'default'},
        {'active': True,
         'basearchonly': None,
         'blocked': False,
         'create_event': 11030903,
         'create_ts': 1429100064.58404,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'group.name': 'maven-build',
         'group_id': 103,
         'package': 'liberation-sans-fonts',
         'requires': None,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792,
         'type': 'default'},
        {'active': True,
         'basearchonly': None,
         'blocked': False,
         'create_event': 11030904,
         'create_ts': 1429100064.9534,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'group.name': 'maven-build',
         'group_id': 103,
         'package': 'liberation-serif-fonts',
         'requires': None,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792,
         'type': 'default'},
        {'active': True,
         'basearchonly': None,
         'blocked': False,
         'create_event': 11030905,
         'create_ts': 1429100065.32708,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'group.name': 'maven-build',
         'group_id': 103,
         'package': 'maven3',
         'requires': None,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792,
         'type': 'default'},
        {'active': True,
         'basearchonly': None,
         'blocked': False,
         'create_event': 11030906,
         'create_ts': 1429100065.72081,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'group.name': 'maven-build',
         'group_id': 103,
         'package': 'pom-manipulation-ext',
         'requires': None,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792,
         'type': 'default'},
        {'active': True,
         'basearchonly': None,
         'blocked': False,
         'create_event': 11030907,
         'create_ts': 1429100066.14912,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'group.name': 'maven-build',
         'group_id': 103,
         'package': 'shadow-utils',
         'requires': None,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792,
         'type': 'default'},
        {'active': True,
         'basearchonly': None,
         'blocked': False,
         'create_event': 11030908,
         'create_ts': 1429100066.50659,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'group.name': 'maven-build',
         'group_id': 103,
         'package': 'subversion',
         'requires': None,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792,
         'type': 'default'}],
    'group_req_listing': [],
    'tag_config': [
        {'active': True,
         'arches': 'x86_64',
         'create_event': 18591262,
         'create_ts': 1521571604.81926,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'locked': False,
         'maven_include_all': True,
         'maven_support': True,
         'perm_id': None,
         'permission.name': None,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792},
        {'active': None,
         'arches': 'i686 x86_64',
         'create_event': 11030881,
         'create_ts': 1429099889.65355,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'locked': False,
         'maven_include_all': True,
         'maven_support': True,
         'perm_id': None,
         'permission.name': None,
         'revoke_event': 18591262,
         'revoke_ts': 1521571604.81926,
         'revoker_id': 999999,
         'revoker_name': 'obriencj',
         'tag.name': 'example-1.0-build',
         'tag_id': 7792}],
    'tag_external_repos': [],
    'tag_extra': [],
    'tag_inheritance': [
        {'active': None,
         'create_event': 11030889,
         'create_ts': 1429099950.31893,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'intransitive': False,
         'maxdepth': None,
         'noconfig': False,
         'parent.name': 'platform-latest-released',
         'parent_id': 3525,
         'pkg_filter': '',
         'priority': 100,
         'revoke_event': 18591257,
         'revoke_ts': 1521571593.0283,
         'revoker_id': 999999,
         'revoker_name': 'obriencj',
         'tag.name': 'example-1.0-build',
         'tag_id': 7792},
        {'active': True,
         'create_event': 18591257,
         'create_ts': 1521571593.0283,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'intransitive': False,
         'maxdepth': None,
         'noconfig': False,
         'parent.name': 'example-1.0-override',
         'parent_id': 7790,
         'pkg_filter': '',
         'priority': 0,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792},
        {'active': None,
         'create_event': 11030886,
         'create_ts': 1429099905.41295,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'intransitive': False,
         'maxdepth': None,
         'noconfig': False,
         'parent.name': 'example-1.0-override',
         'parent_id': 7790,
         'pkg_filter': '',
         'priority': 0,
         'revoke_event': 18591257,
         'revoke_ts': 1521571593.0283,
         'revoker_id': 999999,
         'revoker_name': 'obriencj',
         'tag.name': 'example-1.0-build',
         'tag_id': 7792},
        {'active': True,
         'create_event': 18591257,
         'create_ts': 1521571593.0283,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'intransitive': False,
         'maxdepth': None,
         'noconfig': False,
         'parent.name': 'example-1.0-todo',
         'parent_id': 7791,
         'pkg_filter': '',
         'priority': 10,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792},
        {'active': None,
         'create_event': 11030888,
         'create_ts': 1429099916.33031,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'intransitive': False,
         'maxdepth': None,
         'noconfig': False,
         'parent.name': 'example-1.0-todo',
         'parent_id': 7791,
         'pkg_filter': '',
         'priority': 10,
         'revoke_event': 18591257,
         'revoke_ts': 1521571593.0283,
         'revoker_id': 999999,
         'revoker_name': 'obriencj',
         'tag.name': 'example-1.0-build',
         'tag_id': 7792},
        {'active': True,
         'create_event': 18591257,
         'create_ts': 1521571593.0283,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'intransitive': False,
         'maxdepth': None,
         'noconfig': False,
         'parent.name': 'platform-build-base',
         'parent_id': 12943,
         'pkg_filter': '',
         'priority': 100,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792},
        {'active': True,
         'create_event': 40364990,
         'create_ts': 1628181811.05895,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'intransitive': True,
         'maxdepth': None,
         'noconfig': False,
         'parent.name': 'example-1.0-something',
         'parent_id': 87021,
         'pkg_filter': '',
         'priority': 66,
         'revoke_event': None,
         'revoke_ts': None,
         'revoker_id': None,
         'revoker_name': None,
         'tag.name': 'example-1.0-build',
         'tag_id': 7792}],
    'tag_listing': [
        {'active': None,
         'build.state': 1,
         'build_id': 1740292,
         'create_event': 41197500,
         'create_ts': 1632323242.84196,
         'creator_id': 999999,
         'creator_name': 'obriencj',
         'epoch': None,
         'name': 'tmux',
         'release': '2.el9_b',
         'revoke_event': 41197508,
         'revoke_ts': 1632323265.5984,
         'revoker_id': 999999,
         'revoker_name': 'obriencj',
         'tag.name': 'example-1.0-build',
         'tag_id': 7792,
         'version': '3.2a'}],
    'tag_package_owners': [],
    'tag_packages': []
}

EXPECTED_HIST = """
Wed Apr 15 08:11:29 2015 new tag: example-1.0-build by obriencj
Wed Apr 15 08:11:45 2015 inheritance line example-1.0-build->example-1.0-override added by obriencj
Wed Apr 15 08:11:56 2015 inheritance line example-1.0-build->example-1.0-todo added by obriencj
Wed Apr 15 08:12:30 2015 inheritance line example-1.0-build->platform-latest-released added by obriencj
Wed Apr 15 08:13:53 2015 group maven-build added to tag example-1.0-build by obriencj [still active]
Wed Apr 15 08:14:21 2015 package bash added to group maven-build in tag example-1.0-build by obriencj [still active]
Wed Apr 15 08:14:22 2015 package coreutils added to group maven-build in tag example-1.0-build by obriencj [still active]
Wed Apr 15 08:14:23 2015 package git added to group maven-build in tag example-1.0-build by obriencj [still active]
Wed Apr 15 08:14:23 2015 package java-1.7.0-openjdk-devel added to group maven-build in tag example-1.0-build by obriencj [still active]
Wed Apr 15 08:14:23 2015 package liberation-mono-fonts added to group maven-build in tag example-1.0-build by obriencj [still active]
Wed Apr 15 08:14:24 2015 package liberation-sans-fonts added to group maven-build in tag example-1.0-build by obriencj [still active]
Wed Apr 15 08:14:24 2015 package liberation-serif-fonts added to group maven-build in tag example-1.0-build by obriencj [still active]
Wed Apr 15 08:14:25 2015 package maven3 added to group maven-build in tag example-1.0-build by obriencj [still active]
Wed Apr 15 08:14:25 2015 package pom-manipulation-ext added to group maven-build in tag example-1.0-build by obriencj [still active]
Wed Apr 15 08:14:26 2015 package shadow-utils added to group maven-build in tag example-1.0-build by obriencj [still active]
Wed Apr 15 08:14:26 2015 package subversion added to group maven-build in tag example-1.0-build by obriencj [still active]
Tue Mar 20 14:46:33 2018 inheritance line example-1.0-build->platform-latest-released removed by obriencj
Tue Mar 20 14:46:33 2018 inheritance line example-1.0-build->example-1.0-override updated by obriencj
Tue Mar 20 14:46:33 2018 inheritance line example-1.0-build->example-1.0-todo updated by obriencj
Tue Mar 20 14:46:33 2018 inheritance line example-1.0-build->platform-build-base added by obriencj [still active]
Tue Mar 20 14:46:44 2018 tag configuration for example-1.0-build altered by obriencj
    arches: i686 x86_64 -> x86_64
Thu Aug  5 12:43:31 2021 inheritance line example-1.0-build->example-1.0-something added by obriencj [still active]
Wed Sep 22 11:07:22 2021 tmux-3.2a-2.el9_b tagged into example-1.0-build by obriencj
Wed Sep 22 11:07:45 2021 tmux-3.2a-2.el9_b untagged from example-1.0-build by obriencj
"""


def cleanup_histlines(lines):
    # the utc option to print_history_results is only supported in
    # koji >= 1.27, and otherwise silently falls back to
    # localtime. Let's make it work in both situations! We'll just
    # trim out the day and hour from the lines. It's kinda weird but
    # it works.
    collect = []
    for line in lines.strip().splitlines():
        collect.append(line[4:8] + line[14:])
    return collect


class TestHistory(TestCase):

    maxDiff = None

    def test_print_history_results(self):
        with patch('sys.stdout', new=StringIO()) as out:
            print_history_results(HIST_DATA, utc=True)

        self.assertEqual(cleanup_histlines(EXPECTED_HIST),
                         cleanup_histlines(out.getvalue()))


#
# The end.
