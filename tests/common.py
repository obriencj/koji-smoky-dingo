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


from unittest import TestCase

from kojismokydingo.common import (
    chunkseq, fnmatches, globfilter,
    merge_extend, unique, update_extend,
    _rpm_str_compare)


try:
    from rpm import labelCompare

    def compareVer(v1, v2):
        return labelCompare(('', v1, ''), ('', v2, ''))

except ImportError:
    labelCompare = None
    compareVer = None


# these all cmp to 0
RPM_STR_CMP_0 = [
    ("", ""),
    ("1", "1"),
    ("1.0", "1.0"),
    ("1.1", "1..1"),
    ("1.1", "1._._._.!!!.1"),
    ("1.1", "1_1"),
    ("1.", "1"),
    ("001", "1"),
    ("010", "10"),
    ("1.Z.0", "1Z0"),
    ("1.0Z", "1_0_Z"),
    ("2~beta", "2..~beta"),
    ("2~beta", "2_~beta!"),
    ("2~beta2", "2~beta02"),
    ("2~beta2", "2~beta.02"),
]

# these all cmp to 1
RPM_STR_CMP_1 = [
    ("0", ""),
    ("A", ""),
    ("1", "0"),
    ("2", "1"),
    ("0", "A"),
    ("0", "Z"),
    ("B", "A"),
    ("1.1", "1.0"),
    ("1.1", "1.A"),
    ("1.B", "1.A"),
    ("1.1", "1.0~beta"),
    ("1.1", "1.1~beta"),
    ("1.2~beta", "1.1"),
    ("1.2~beta0", "1.2~beta"),
    ("1.2~beta.2", "1.2~beta.1"),
    ("1.2~beta02", "1.2~beta01"),
    ("1.1", "1"),
    ("2", "1.1"),
    ("2.0", "2"),
    ("2.0", "2~beta"),
    ("2beta", "2~beta"),
]


class TestEVRSort(TestCase):

    if compareVer:
        # these tests just validate that we're behaving the same as
        # rpm lib. However, not all systems have rpmlib available, so
        # we omit these tests in those environments.

        def test_rpm_compare_ver_0(self):
            for vl, vr in RPM_STR_CMP_0:
                self.assertEqual(compareVer(vl, vr), 0)
                self.assertEqual(compareVer(vr, vl), 0)


        def test_rpm_compare_ver_1(self):
            for vl, vr in RPM_STR_CMP_1:
                self.assertEqual(compareVer(vl, vr), 1)
                self.assertEqual(compareVer(vr, vl), -1)


    def test_rpm_str_cmp_0(self):
        for vl, vr in RPM_STR_CMP_0:
            self.assertEqual(_rpm_str_compare(vl, vr), 0)
            self.assertEqual(_rpm_str_compare(vr, vl), 0)


    def test_rpm_str_cmp_1(self):
        for vl, vr in RPM_STR_CMP_1:
            self.assertEqual(_rpm_str_compare(vl, vr), 1)
            self.assertEqual(_rpm_str_compare(vr, vl), -1)


class TestCommon(TestCase):


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


    def test_unique(self):
        data = ["one", "two", "one", "two", "three",
                "three", "three", "one", "two", "three", "four",
                "four", "three", "two", "one"]

        expect = ["one", "two", "three", "four"]

        self.assertEqual(unique(data), expect)


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


#
# The end.
