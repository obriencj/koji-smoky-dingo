

from unittest import TestCase

from kojismokydingo import _rpm_str_compare


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


class TestNEVRSort(TestCase):

    def test_rpm_str_cmp_0(self):
        for vl, vr in RPM_STR_CMP_0:
            self.assertEqual(_rpm_str_compare(vl, vr), 0)
            self.assertEqual(_rpm_str_compare(vr, vl), 0)


    def test_rpm_str_cmp_1(self):
        for vl, vr in RPM_STR_CMP_1:
            self.assertEqual(_rpm_str_compare(vl, vr), 1)
            self.assertEqual(_rpm_str_compare(vr, vl), -1)


#
# The end.
