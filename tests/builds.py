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

from kojismokydingo.builds import (
    build_dedup, build_id_sort, build_nvr_sort,
    filter_by_state, filter_imported)


# A CG-imported build
BUILD_SAMPLE_1 = {
    "id": 10,
    "state": 2,
    "nvr": "sample-1.0-1",
    "name": "sample",
    "version": "1.0",
    "release": "1",
    "epoch": None,
    "task_id": None,
    "archive_cg_ids": set([901]),
    "archive_cg_names": set(["example-cg"]),
    "archive_btype_ids": set([701]),
    "archive_btype_names": set(["example"]),
}

# A CG-imported build
BUILD_SAMPLE_1_1 = {
    "id": 11,
    "state": 2,
    "nvr": "sample-1.1-1",
    "name": "sample",
    "version": "1.1",
    "release": "1",
    "epoch": None,
    "task_id": None,
    "owner_id": 1,
    "archive_cg_ids": set([901]),
    "archive_cg_names": set(["example-cg"]),
    "archive_btype_ids": set([701]),
    "archive_btype_names": set(["example"]),
}

# A CG-imported build
BUILD_SAMPLE_2 = {
    "id": 20,
    "state": 2,
    "nvr": "sample-2-1",
    "name": "sample",
    "version": "2",
    "release": "1",
    "epoch": None,
    "task_id": None,
    "owner_id": 2,
    "archive_cg_ids": set([902]),
    "archive_cg_names": set(["other-cg"]),
    "archive_btype_ids": set([702]),
    "archive_btype_names": set(["other"]),
}

# A CG-imported build from multiple CGs
BUILD_SAMPLE_3 = {
    "id": 30,
    "state": 1,
    "nvr": "sample-3-1",
    "name": "sample",
    "version": "3",
    "release": "1",
    "epoch": None,
    "task_id": None,
    "owner_id": 3,
    "archive_cg_ids": set([901, 902]),
    "archive_cg_names": set(["example-cg", "other-cg"]),
    "archive_btype_ids": set([701, 702]),
    "archive_btype_names": set(["example", "other"]),
}

# An imported, non-CG build
BUILD_SAMPLE_4 = {
    "id": 40,
    "state": 1,
    "nvr": "sample-4.0-1",
    "name": "sample",
    "version": "4.0",
    "release": "1",
    "epoch": "1",
    "task_id": None,
    "owner_id": 1,
    "archive_cg_ids": set(),
    "archive_cg_names": set(),
    "archive_btype_ids": set([0]),
    "archive_btype_names": set(["rpm"]),
}

# A non-imported build
BUILD_SAMPLE_5 = {
    "id": 55,
    "state": 1,
    "nvr": "sample-5.5.1-1",
    "name": "sample",
    "version": "5.5.1",
    "release": "1",
    "epoch": "1",
    "task_id": 500,
    "owner_id": 99,
    "archive_cg_ids": set(),
    "archive_cg_names": set(),
    "archive_btype_ids": set([0]),
    "archive_btype_names": set(["rpm"]),
}


BUILD_SAMPLES = (
    BUILD_SAMPLE_1,
    BUILD_SAMPLE_1_1,
    BUILD_SAMPLE_2,
    BUILD_SAMPLE_3,
    BUILD_SAMPLE_4,
    BUILD_SAMPLE_5,
)


class TestFilterImported(TestCase):


    def _filter_imported(self, *args, **kwds):
        return tuple(filter_imported(BUILD_SAMPLES, *args, **kwds))


    def test_filter_empty_normal(self):
        match = self._filter_imported()
        expected = (BUILD_SAMPLE_4,)
        self.assertEqual(match, expected)


    def test_filter_empty_negate(self):
        match = self._filter_imported(negate=True)
        expected = (BUILD_SAMPLE_5,)
        self.assertEqual(match, expected)


    def test_filter_any_normal(self):
        match = self._filter_imported(("any",))
        expected = (BUILD_SAMPLE_1, BUILD_SAMPLE_1_1,
                    BUILD_SAMPLE_2, BUILD_SAMPLE_3)
        self.assertEqual(match, expected)


    def test_filter_any_negate(self):
        match = self._filter_imported(("any",), negate=True)
        expected = ()
        self.assertEqual(match, expected)


    def test_filter_example_normal(self):
        match = self._filter_imported(("example-cg",))
        expected = (BUILD_SAMPLE_1, BUILD_SAMPLE_1_1, BUILD_SAMPLE_3)
        self.assertEqual(match, expected)


    def test_filter_example_negate(self):
        match = self._filter_imported(("example-cg",), negate=True)
        expected = (BUILD_SAMPLE_2,)
        self.assertEqual(match, expected)


    def test_filter_other_normal(self):
        match = self._filter_imported(("other-cg",))
        expected = (BUILD_SAMPLE_2, BUILD_SAMPLE_3)
        self.assertEqual(match, expected)


    def test_filter_other_negate(self):
        match = self._filter_imported(("other-cg",), negate=True)
        expected = (BUILD_SAMPLE_1, BUILD_SAMPLE_1_1)
        self.assertEqual(match, expected)


    def test_filter_both_normal(self):
        match = self._filter_imported(("example-cg", "other-cg"))
        expected = (BUILD_SAMPLE_1, BUILD_SAMPLE_1_1,
                    BUILD_SAMPLE_2, BUILD_SAMPLE_3)
        self.assertEqual(match, expected)


    def test_filter_both_negate(self):
        match = self._filter_imported(("example-cg", "other-cg"), negate=True)
        expected = ()
        self.assertEqual(match, expected)


    def test_filter_neither_normal(self):
        match = self._filter_imported(("absent-cg",))
        expected = ()
        self.assertEqual(match, expected)


    def test_filter_neither_negate(self):
        match = self._filter_imported(("absent-cg",), negate=True)
        expected = (BUILD_SAMPLE_1, BUILD_SAMPLE_1_1,
                    BUILD_SAMPLE_2, BUILD_SAMPLE_3)
        self.assertEqual(match, expected)


class TestFilterState(TestCase):


    def _filter_by_state(self, *args, **kwds):
        return tuple(filter_by_state(BUILD_SAMPLES, *args, **kwds))


    def test_filter_none(self):
        res = self._filter_by_state(None)
        self.assertEqual(res, BUILD_SAMPLES)


    def test_filter_completed(self):
        res = self._filter_by_state(1)
        expected = (BUILD_SAMPLE_3, BUILD_SAMPLE_4, BUILD_SAMPLE_5)
        self.assertEqual(res, expected)


    def test_filter_deleted(self):
        res = self._filter_by_state(2)
        expected = (BUILD_SAMPLE_1, BUILD_SAMPLE_1_1, BUILD_SAMPLE_2)
        self.assertEqual(res, expected)


    def test_filter_failed(self):
        res = self._filter_by_state(3)
        expected = ()
        self.assertEqual(res, expected)


UNSORTED_BUILDS = (
    BUILD_SAMPLE_5,
    BUILD_SAMPLE_3,
    BUILD_SAMPLE_5,
    BUILD_SAMPLE_1_1,
    BUILD_SAMPLE_1,
    BUILD_SAMPLE_4,
    BUILD_SAMPLE_2,
    BUILD_SAMPLE_1,
)

SORTED_BUILDS = (
    BUILD_SAMPLE_1,
    BUILD_SAMPLE_1,
    BUILD_SAMPLE_1_1,
    BUILD_SAMPLE_2,
    BUILD_SAMPLE_3,
    BUILD_SAMPLE_4,
    BUILD_SAMPLE_5,
    BUILD_SAMPLE_5,
)

DEDUP_BUILDS = (
    BUILD_SAMPLE_5,
    BUILD_SAMPLE_3,
    BUILD_SAMPLE_1_1,
    BUILD_SAMPLE_1,
    BUILD_SAMPLE_4,
    BUILD_SAMPLE_2,
)


class TestSorting(TestCase):


    def test_id_sort(self):

        res = build_id_sort(BUILD_SAMPLES)
        self.assertEqual([b["id"] for b in res],
                         [b["id"] for b in BUILD_SAMPLES])
        self.assertTrue(res is not BUILD_SAMPLES)

        res = build_id_sort(UNSORTED_BUILDS, dedup=True)
        self.assertEqual([b["id"] for b in res],
                         [b["id"] for b in BUILD_SAMPLES])
        self.assertTrue(res is not UNSORTED_BUILDS)

        res = build_id_sort(UNSORTED_BUILDS, dedup=False)
        self.assertEqual([b["id"] for b in res],
                         [b["id"] for b in SORTED_BUILDS])
        self.assertTrue(res is not SORTED_BUILDS)


    def test_nvr_sort(self):

        res = build_nvr_sort(BUILD_SAMPLES)
        self.assertEqual([b["nvr"] for b in res],
                         [b["nvr"] for b in BUILD_SAMPLES])
        self.assertTrue(res is not BUILD_SAMPLES)

        res = build_nvr_sort(UNSORTED_BUILDS, dedup=True)
        self.assertEqual([b["nvr"] for b in res],
                         [b["nvr"] for b in BUILD_SAMPLES])
        self.assertTrue(res is not UNSORTED_BUILDS)

        res = build_nvr_sort(UNSORTED_BUILDS, dedup=False)
        self.assertEqual([b["nvr"] for b in res],
                         [b["nvr"] for b in SORTED_BUILDS])
        self.assertTrue(res is not SORTED_BUILDS)


    def test_dedup(self):

        res = build_dedup(BUILD_SAMPLES)
        self.assertEqual([b["id"] for b in res],
                         [b["id"] for b in BUILD_SAMPLES])
        self.assertTrue(res is not BUILD_SAMPLES)

        res = build_dedup(UNSORTED_BUILDS)
        self.assertEqual([b["id"] for b in res],
                         [b["id"] for b in DEDUP_BUILDS])
        self.assertTrue(res is not UNSORTED_BUILDS)


# The end.
