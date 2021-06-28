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

from kojismokydingo.rpm import (
    _rpm_str_compare, evr_compare,
    nevra_split, nevr_split, evr_split, )


try:
    from rpm import labelCompare

    def compareVer(v1, v2):
        try:
            return labelCompare(('0', v1, '0'), ('0', v2, '0'))
        except:
            # this is only used to validate our expectations. Some
            # newer versions of RPM (Fedora 34) will actually error on
            # empty comparison values, but older versions will not. If
            # we're in a situation testing empties, don't consider
            # that a failure.
            if v1 and v2:
                raise
            elif v1 == v2:
                return 0
            elif v1 > v2:
                return 1
            elif v1 < v2:
                return -1
            else:
                raise

except ImportError:
    labelCompare = None
    compareVer = None


# these all cmp to 0
RPM_STR_CMP_0 = [
    ("", ""),
    ("0", "0"),
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


    def test_rpm_evr_compare_cmp_0(self):
        for vl, vr in RPM_STR_CMP_0:
            evr_l = ("0", vl, "1")
            evr_r = ("0", vr, "1")
            self.assertEqual(evr_compare(evr_l, evr_r), 0)
            self.assertEqual(evr_compare(evr_r, evr_l), 0)


    def test_rpm_evr_compare_cmp_1(self):
        for vl, vr in RPM_STR_CMP_1:
            evr_l = ("0", vl, "1")
            evr_r = ("0", vr, "1")
            self.assertEqual(evr_compare(evr_l, evr_r), 1)
            self.assertEqual(evr_compare(evr_r, evr_l), -1)


NEVRA_SPLITS = [
    ("bind-32:9.10.2-2.P1.fc22.x86_64",
     ("bind", "32", "9.10.2", "2.P1.fc22", "x86_64")),
    ("bind-9.10.2-2.P1.fc22.x86_64",
     ("bind", None, "9.10.2", "2.P1.fc22", "x86_64")),
    ("bind-32:9.10.2-2",
     ("bind", "32", "9.10.2", "2", None)),
    ("bind-9.10.2-2",
     ("bind", None, "9.10.2", "2", None)),
    ("bind-32:9.10.2",
     ("bind", "32", "9.10.2", None, None)),
    ("bind-9.10.2",
     ("bind", None, "9.10.2", None, None)),
    ("bind",
     ("bind", None, None, None, None)),

    # these should be the only cases where we have no name, very odd
    # structure but discernable
    ("32:9.10.2-2.P1.fc22.x86_64",
     (None, "32", "9.10.2", "2.P1.fc22", "x86_64")),
    ("32:9.10.2",
     (None, "32", "9.10.2", None, None)),

    ("",
     ("", None, None, None, None)),
]


NEVR_SPLITS = [
    ("bind-32:9.10.2-2.P1.fc22.x86_64",
     ("bind", "32", "9.10.2", "2.P1.fc22.x86_64")),
    ("bind-9.10.2-2.P1.fc22.x86_64",
     ("bind", None, "9.10.2", "2.P1.fc22.x86_64")),
    ("bind-32:9.10.2-2",
     ("bind", "32", "9.10.2", "2")),
    ("bind-9.10.2-2",
     ("bind", None, "9.10.2", "2")),
    ("bind-32:9.10.2",
     ("bind", "32", "9.10.2", None)),
    ("bind-9.10.2",
     ("bind", None, "9.10.2", None)),
    ("bind",
     ("bind", None, None, None)),

    # these should be the only cases where we have no name, very odd
    # structure but discernable
    ("32:9.10.2-2.P1.fc22.x86_64",
     (None, "32", "9.10.2", "2.P1.fc22.x86_64")),
    ("32:9.10.2",
     (None, "32", "9.10.2", None)),

    ("",
     ("", None, None, None)),
]


class TestSplits(TestCase):


    def test_nevra_split(self):
        for src, expect in NEVRA_SPLITS:
            self.assertEqual(nevra_split(src), expect)


    def test_nevr_split(self):
        for src, expect in NEVR_SPLITS:
            self.assertEqual(nevr_split(src), expect)


#
# The end.
