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

from kojismokydingo.builds import filter_imported


BUILD_SAMPLE_1 = {
    "id": 1,
    "nvr": "sample-1-1",
    "task_id": None,
    "archive_cg_ids": set([901]),
    "archive_cg_names": set(["example-cg"]),
    "archive_btype_ids": set([701]),
    "archive_btype_names": set(["example"]),
}

BUILD_SAMPLE_2 = {
    "id": 2,
    "nvr": "sample-2-1",
    "task_id": None,
    "archive_cg_ids": set([902]),
    "archive_cg_names": set(["other-cg"]),
    "archive_btype_ids": set([702]),
    "archive_btype_names": set(["other"]),
}

BUILD_SAMPLE_3 = {
    "id": 4,
    "nvr": "sample-4-1",
    "task_id": None,
    "archive_cg_ids": set([901, 902]),
    "archive_cg_names": set(["example-cg", "other-cg"]),
    "archive_btype_ids": set([701, 702]),
    "archive_btype_names": set(["example", "other"]),
}

BUILD_SAMPLE_4 = {
    "id": 4,
    "nvr": "sample-4-1",
    "task_id": None,
    "archive_cg_ids": None,
    "archive_cg_names": None,
    "archive_btype_ids": set([0]),
    "archive_btype_names": set(["rpm"]),
}

BUILD_SAMPLE_5 = {
    "id": 5,
    "nvr": "sample-5-1",
    "task_id": 500,
    "archive_cg_ids": None,
    "archive_cg_names": None,
    "archive_btype_ids": set([0]),
    "archive_btype_names": set(["rpm"]),
}


BUILD_SAMPLES = (
    BUILD_SAMPLE_1,
    BUILD_SAMPLE_2,
    BUILD_SAMPLE_3,
    BUILD_SAMPLE_4,
    BUILD_SAMPLE_5,
)


class TestFilterImported(TestCase):


    def test_filter_empty_normal(self):
        match = filter_imported(BUILD_SAMPLES)
        expected = (BUILD_SAMPLE_4,)
        self.assertEqual(tuple(match), expected)


    def test_filter_empty_negate(self):
        match = filter_imported(BUILD_SAMPLES, negate=True)
        expected = (BUILD_SAMPLE_5,)
        self.assertEqual(tuple(match), expected)


    def test_filter_any_normal(self):
        match = filter_imported(BUILD_SAMPLES, ("any",))
        expected = (BUILD_SAMPLE_1, BUILD_SAMPLE_2, BUILD_SAMPLE_3)
        self.assertEqual(tuple(match), expected)


    def test_filter_any_negate(self):
        match = filter_imported(BUILD_SAMPLES, ("any",), negate=True)
        expected = ()
        self.assertEqual(tuple(match), expected)


    def test_filter_example_normal(self):
        match = filter_imported(BUILD_SAMPLES, ("example-cg",))
        expected = (BUILD_SAMPLE_1, BUILD_SAMPLE_3)
        self.assertEqual(tuple(match), expected)


    def test_filter_example_negate(self):
        match = filter_imported(BUILD_SAMPLES,
                                ("example-cg",), negate=True)
        expected = (BUILD_SAMPLE_2,)
        self.assertEqual(tuple(match), expected)


    def test_filter_other_normal(self):
        match = filter_imported(BUILD_SAMPLES, ("other-cg",))
        expected = (BUILD_SAMPLE_2, BUILD_SAMPLE_3)
        self.assertEqual(tuple(match), expected)


    def test_filter_other_negate(self):
        match = filter_imported(BUILD_SAMPLES,
                                ("other-cg",), negate=True)
        expected = (BUILD_SAMPLE_1,)
        self.assertEqual(tuple(match), expected)


    def test_filter_both_normal(self):
        match = filter_imported(BUILD_SAMPLES, ("example-cg", "other-cg"))
        expected = (BUILD_SAMPLE_1, BUILD_SAMPLE_2, BUILD_SAMPLE_3)
        self.assertEqual(tuple(match), expected)


    def test_filter_both_negate(self):
        match = filter_imported(BUILD_SAMPLES,
                                ("example-cg", "other-cg"), negate=True)
        expected = ()
        self.assertEqual(tuple(match), expected)


    def test_filter_neither_normal(self):
        match = filter_imported(BUILD_SAMPLES, ("absent-cg",))
        expected = ()
        self.assertEqual(tuple(match), expected)


    def test_filter_neither_negate(self):
        match = filter_imported(BUILD_SAMPLES,
                                ("absent-cg",), negate=True)
        expected = (BUILD_SAMPLE_1, BUILD_SAMPLE_2, BUILD_SAMPLE_3)
        self.assertEqual(tuple(match), expected)



# The end.
