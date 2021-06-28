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


from configparser import ConfigParser
from contextlib import contextmanager
from datetime import datetime
from mock import MagicMock, patch
from operator import itemgetter
from pkg_resources import resource_filename
from unittest import TestCase

from kojismokydingo.common import (
    chunkseq, escapable_replace, fnmatches,
    find_config_dirs, find_config_files, get_plugin_config,
    globfilter, load_full_config, load_plugin_config, merge_extend,
    parse_datetime, unique, update_extend)


class TestRelace(TestCase):


    def test_escapable_replace(self):
        data = [
            ("%", "foo", "foo"),
            ("%.txt", "foo", "foo.txt"),
            ("foo-%.txt", "bar", "foo-bar.txt"),
            ("foo-%", "bar", "foo-bar"),
            ("%%", "wut", "%"),
            ("%%.txt", "wut", "%.txt"),
            ("foo-%%.txt", "wut", "foo-%.txt"),
            ("foo-%%", "wut", "foo-%"),
            ("", "wut", ""),
            ("foo", "wut", "foo"),
        ]

        for orig, repl, expect in data:
            res = escapable_replace(orig, "%", repl)
            self.assertEqual(res, expect)


class TestExtend(TestCase):


    def test_update_extend(self):
        A = {'a': [1, 2], 'b': [7], 'c': [10]}
        B = {'a': [3], 'b': [8, 9], 'd': [11]}

        C = {'a': [1, 2, 3], 'b': [7, 8, 9], 'c': [10], 'd': [11]}

        Z = {'a': [3], 'b': [8, 9], 'd': [11]}

        r = update_extend(A, B)

        self.assertEqual(A, C)
        self.assertTrue(A is r)

        # verify that B wasn't modified
        self.assertEqual(B, Z)


    def test_merge_extend(self):
        A = {'a': [1, 2], 'b': [7], 'c': [10]}
        B = {'a': [3], 'b': [8, 9], 'd': [11]}

        C = {'a': [1, 2, 3], 'b': [7, 8, 9], 'c': [10], 'd': [11]}

        Y = {'a': [1, 2], 'b': [7], 'c': [10]}
        Z = {'a': [3], 'b': [8, 9], 'd': [11]}

        r = merge_extend(A, B)

        self.assertEqual(r, C)
        self.assertTrue(A is not r)

        # verify that neither A nor B were modified
        self.assertEqual(A, Y)
        self.assertEqual(B, Z)


class TestUnique(TestCase):

    def test_unique(self):
        data = ["one", "two", "one", "two", "three",
                "three", "three", "one", "two", "three", "four",
                "four", "three", "two", "one"]

        expect = ["one", "two", "three", "four"]

        self.assertEqual(unique(data), expect)


    def test_unique_key(self):

        origin = ["one", "two", "three", "four"]

        def make_data(series):
            return [{"id": origin.index(val), "val": val} for val in series]

        data = make_data(["one", "two", "one", "two", "three",
                          "three", "three", "one", "two", "three", "four",
                          "four", "three", "two", "one"])

        expect = make_data(origin)

        self.assertEqual(unique(data, itemgetter("id")), expect)
        self.assertEqual(unique(data, itemgetter("val")), expect)

        self.assertEqual(unique(data, "id"), expect)
        self.assertEqual(unique(data, "val"), expect)


class TestChunkseq(TestCase):

    def test_chunkseq(self):
        data = list(range(0, 25))
        expect = [list(range(0, 5)),
                  list(range(5, 10)),
                  list(range(10, 15)),
                  list(range(15, 20)),
                  list(range(20, 25))]

        result = list(chunkseq(data, 5))
        self.assertEqual(result, expect)

        data = list(range(0, 27))
        expect = [list(range(0, 5)),
                  list(range(5, 10)),
                  list(range(10, 15)),
                  list(range(15, 20)),
                  list(range(20, 25)),
                  list(range(25, 27))]

        result = list(chunkseq(data, 5))
        self.assertEqual(result, expect)


class TestGlob(TestCase):

    def test_fnmatches(self):
        data_matches = [
            ("hello", ["hello"], True),
            ("hello", ["hello"], False),
            ("hello", ["HELLO"], True),
            ("hello", ["h*"], True),
            ("hello", ["h*"], False),
            ("hello", ["H*"], True),
            ("hello", ["world", "h*"], True),
            ("hello", ["world", "h*"], False),
            ("hello", ["WORLD", "H*"], True),
            ("hello", ["*"], True),
            ("hello", ["*"], False),
            ("hello", ["?*"], True),
            ("hello", ["?*"], False),
            ("h", ["?"], True),
            ("h", ["?"], False),
        ]

        data_mismatches = [
            ("Hello", ["hello"], False),
            ("Hello", ["HELLO"], False),
            ("hello", ["world"], True),
            ("hello", ["world"], False),
            ("hello", ["w*"], True),
            ("hello", ["w*"], False),
            ("hello", ["H*"], False),
            ("Hello", ["h*"], False),
            ("hello", ["tacos", "w*"], True),
            ("hello", ["tacos", "w*"], False),
        ]

        for s, p, i in data_matches:
            self.assertTrue(fnmatches(s, p, i), (s, p, i))

        for s, p, i in data_mismatches:
            self.assertFalse(fnmatches(s, p, i), (s, p, i))


    def test_globfilter(self):
        data = ["one", "two", "three", "tacos", "pizza", "beer"]

        def gf(patterns, invert, ignore_case):
            return list(globfilter(data, patterns, key=None,
                                   invert=invert, ignore_case=ignore_case))

        self.assertEqual(gf(["*"], False, False), data)
        self.assertEqual(gf(["*"], False, True), data)
        self.assertEqual(gf(["*"], True, False), [])
        self.assertEqual(gf(["*"], True, True), [])

        self.assertEqual(gf(["?"], False, False), [])
        self.assertEqual(gf(["?"], False, True), [])
        self.assertEqual(gf(["?"], True, False), data)
        self.assertEqual(gf(["?"], True, True), data)

        self.assertEqual(gf(["t*"], False, True),
                         ["two", "three", "tacos"])
        self.assertEqual(gf(["t*"], False, False),
                         ["two", "three", "tacos"])

        self.assertEqual(gf(["T*"], False, True),
                         ["two", "three", "tacos"])
        self.assertEqual(gf(["T*"], False, False), [])

        self.assertEqual(gf(["T*"], True, True),
                         ["one", "pizza", "beer"])
        self.assertEqual(gf(["T*"], True, False), data)


    def test_globfilter_key(self):
        data = ["one", "two", "three", "tacos", "pizza", "beer"]
        data = [{"id": i, "val": v} for (i, v) in enumerate(data)]

        def gf(patterns, invert, ignore_case):
            vals = (globfilter(data, patterns, key="val",
                               invert=invert, ignore_case=ignore_case))
            return [v["val"] for v in vals]

        def dv(vals):
            return [v["val"] for v in vals]

        self.assertEqual(gf(["*"], False, False), dv(data))
        self.assertEqual(gf(["*"], False, True), dv(data))
        self.assertEqual(gf(["*"], True, False), [])
        self.assertEqual(gf(["*"], True, True), [])

        self.assertEqual(gf(["?"], False, False), [])
        self.assertEqual(gf(["?"], False, True), [])
        self.assertEqual(gf(["?"], True, False), dv(data))
        self.assertEqual(gf(["?"], True, True), dv(data))

        self.assertEqual(gf(["t*"], False, True),
                         ["two", "three", "tacos"])
        self.assertEqual(gf(["t*"], False, False),
                         ["two", "three", "tacos"])

        self.assertEqual(gf(["T*"], False, True),
                         ["two", "three", "tacos"])
        self.assertEqual(gf(["T*"], False, False), [])

        self.assertEqual(gf(["T*"], True, True),
                         ["one", "pizza", "beer"])
        self.assertEqual(gf(["T*"], True, False), dv(data))


class TestDates(TestCase):

    def test_parse_datetime(self):
        expected = {
            "year": 2020,
            "month": 9,
            "day": 21,
            "hour": 16,
            "minute": 30,
            "second": 52,
            "microsecond": 313228
        }

        def check_datetime(src, **magic):
            if magic:
                checks = dict(expected)
                checks.update(magic)
            else:
                checks = expected

            dtv = parse_datetime(src)
            self.assertTrue(isinstance(dtv, datetime))

            for key, val in checks.items():
                found = getattr(dtv, key, None)
                if found:
                    self.assertEqual(found, val)

        check_datetime("2020-09-21 16:30:52.313228+00:00")
        check_datetime("2020-09-21 16:30:52.313228+0000")
        check_datetime("2020-09-21 16:30:52+00:00")
        check_datetime("2020-09-21 16:30:52+0000")
        check_datetime("2020-09-21 16:30:52 UTC")
        check_datetime("2020-09-21 16:30:52")
        check_datetime("2020-09-21 16:30")
        check_datetime("2020-09-21")
        check_datetime("2020-09", day=1)
        check_datetime("1600705852")

        # we'll just validate that it doesn't raise an exception
        dtv = parse_datetime("now")
        self.assertTrue(isinstance(dtv, datetime))

        bad = "joey ramone"
        self.assertRaises(Exception, parse_datetime, bad)
        self.assertEqual(parse_datetime(bad, strict=False), None)


class TestConfig(TestCase):

    def data_dirs(self):
        return (resource_filename(__name__, "data/system"),
                resource_filename(__name__, "data/user"))


    def faux_appdir(self):
        fakes = self.data_dirs()

        obj = MagicMock()

        site_config_dir = obj.site_config_dir
        site_config_dir.side_effect = [fakes[0]]

        user_config_dir = obj.user_config_dir
        user_config_dir.side_effect = [fakes[1]]

        return obj


    @contextmanager
    def patch_appdirs(self):
        fake = self.faux_appdir()
        with patch('kojismokydingo.common.appdirs', new=fake) as meh:
            yield meh


    def test_find_dirs(self):
        with patch('kojismokydingo.common.appdirs', new=None):
            dirs = find_config_dirs()

            self.assertEqual(len(dirs), 2)
            self.assertEqual(dirs[0], "/etc/xdg/ksd/")
            self.assertTrue(dirs[1].endswith(".config/ksd/"))

        with self.patch_appdirs() as meh:
            dirs = find_config_dirs()

            self.assertEqual(len(dirs), 2)
            self.assertEqual(dirs, self.data_dirs())
            self.assertEqual(meh.site_config_dir.call_count, 1)
            self.assertEqual(meh.user_config_dir.call_count, 1)


    def test_find_files(self):

        with self.patch_appdirs() as meh:
            found = find_config_files()

            self.assertEqual(len(found), 3)
            self.assertEqual(meh.site_config_dir.call_count, 1)
            self.assertEqual(meh.user_config_dir.call_count, 1)


    def test_load_full_config(self):
        with self.patch_appdirs():
            conf = load_full_config()

        self.assertTrue(isinstance(conf, ConfigParser))
        self.assertTrue(conf.has_section("example_1"))
        self.assertTrue(conf.has_section("example_2"))
        self.assertTrue(conf.has_section("example_2:test"))
        self.assertTrue(conf.has_section("example_3"))
        self.assertTrue(conf.has_section("example_3:test"))
        self.assertTrue(conf.has_section("example_3:foo"))


    def test_load_plugin_config(self):
        with self.patch_appdirs():
            conf = load_plugin_config("example_1")
            self.assertTrue(conf)
            self.assertEqual(type(conf), dict)
            self.assertEqual(conf["data"], '111')
            self.assertEqual(conf["flavor"], 'tasty')

        with self.patch_appdirs():
            conf = load_plugin_config("example_2")
            self.assertTrue(conf)
            self.assertEqual(type(conf), dict)
            self.assertEqual(conf["data"], '244')
            self.assertEqual(conf["flavor"], 'meh')

        with self.patch_appdirs():
            conf = load_plugin_config("example_2", "test")
            self.assertTrue(conf)
            self.assertEqual(type(conf), dict)
            self.assertEqual(conf["data"], '220')
            self.assertEqual(conf["flavor"], 'meh')

        with self.patch_appdirs():
            conf = load_plugin_config("example_3")
            self.assertTrue(conf)
            self.assertEqual(type(conf), dict)
            self.assertEqual(conf["data"], '300')


    def test_merge(self):
        dirs = self.data_dirs()
        files = find_config_files(dirs)
        full_conf = load_full_config(files)

        conf = get_plugin_config(full_conf, "example_1")
        self.assertTrue(conf)
        self.assertEqual(type(conf), dict)
        self.assertEqual(conf["data"], '111')
        self.assertEqual(conf["flavor"], 'tasty')

        conf = get_plugin_config(full_conf, "example_2")
        self.assertTrue(conf)
        self.assertEqual(type(conf), dict)
        self.assertEqual(conf["data"], '244')
        self.assertEqual(conf["flavor"], 'meh')

        conf = get_plugin_config(full_conf, "example_2", "test")
        self.assertTrue(conf)
        self.assertEqual(type(conf), dict)
        self.assertEqual(conf["data"], '220')
        self.assertEqual(conf["flavor"], 'meh')

        conf = get_plugin_config(full_conf, "example_3")
        self.assertTrue(conf)
        self.assertEqual(type(conf), dict)
        self.assertEqual(conf["data"], '300')


#
# The end.
