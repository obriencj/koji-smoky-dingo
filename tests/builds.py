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


from itertools import repeat
from unittest import TestCase
from unittest.mock import MagicMock

from kojismokydingo.builds import (
    build_dedup, build_id_sort, build_nvr_sort,
    bulk_move_builds, bulk_move_nvrs,
    bulk_tag_builds, bulk_tag_nvrs,
    bulk_untag_builds, bulk_untag_nvrs,
    filter_builds_by_state, filter_imported_builds, )


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
    "archive_cg_ids": [901],
    "archive_cg_names": ["example-cg"],
    "archive_btype_ids": [701],
    "archive_btype_names": ["example"],
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
    "archive_cg_ids": [901],
    "archive_cg_names": ["example-cg"],
    "archive_btype_ids": [701],
    "archive_btype_names": ["example"],
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
    "archive_cg_ids": [902],
    "archive_cg_names": ["other-cg"],
    "archive_btype_ids": [702],
    "archive_btype_names": ["other"],
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
    "archive_cg_ids": [901, 902],
    "archive_cg_names": ["example-cg", "other-cg"],
    "archive_btype_ids": [701, 702],
    "archive_btype_names": ["example", "other"],
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
    "archive_cg_ids": [],
    "archive_cg_names": [],
    "archive_btype_ids": [],
    "archive_btype_names": [],
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
    "archive_cg_ids": [],
    "archive_cg_names": [],
    "archive_btype_ids": [1],
    "archive_btype_names": ["rpm"],
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
        return tuple(filter_imported_builds(BUILD_SAMPLES, *args, **kwds))


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
        return tuple(filter_builds_by_state(BUILD_SAMPLES, *args, **kwds))


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


class BulkTagging(TestCase):


    def session(self, tag_results=(), untag_results=(), builds=()):

        builds = iter(builds)
        tag_results = iter(tag_results)
        untag_results = iter(untag_results)

        mc_gather = []

        def convert(v):
            if isinstance(v, dict) and "faultCode" in v:
                return v
            else:
                return [v]

        def do_getBuild(*args, **kwds):
            mc_gather.append(convert(next(builds)))

        def do_tagBuildBypass(*args, **kwds):
            mc_gather.append(convert(next(tag_results)))

        def do_untagBuildBypass(*args, **kwds):
            mc_gather.append(convert(next(untag_results)))

        def do_mc(strict=None):
            results = list(mc_gather)
            mc_gather[:] = ()
            return results

        sess = MagicMock()
        sess.getBuild.side_effect = do_getBuild
        sess.tagBuildBypass.side_effect = do_tagBuildBypass
        sess.untagBuildBypass.side_effect = do_untagBuildBypass
        sess.multiCall.side_effect = do_mc

        return sess


    def test_bulk_tag_nvrs(self):
        sess = self.session(builds=BUILD_SAMPLES,
                            tag_results=repeat(None))

        tag = {"id": 1, "name": "some-tag"}
        res = bulk_tag_nvrs(sess, tag, range(0, 6), size=5)

        self.assertEqual(res, list(zip(BUILD_SAMPLES, repeat([None]))))
        self.assertEqual(sess.getBuild.call_count, 6)
        self.assertEqual(sess.tagBuildBypass.call_count, 6)
        self.assertEqual(sess.untagBuildBypass.call_count, 0)
        self.assertEqual(sess.multiCall.call_count, 3)


    def test_bulk_tag_builds(self):
        sess = self.session(tag_results=repeat(None))

        tag = {"id": 1, "name": "some-tag"}
        res = bulk_tag_builds(sess, tag, BUILD_SAMPLES, size=5)

        self.assertEqual(res, list(zip(BUILD_SAMPLES, repeat([None]))))
        self.assertEqual(sess.tagBuildBypass.call_count, 6)
        self.assertEqual(sess.untagBuildBypass.call_count, 0)
        self.assertEqual(sess.multiCall.call_count, 2)


    def test_bulk_tag_builds_err(self):
        err = {"faultCode": 1}
        tres = [None, err, None, None, None, None]
        sess = self.session(tag_results=tres)

        tag = {"id": 1, "name": "some-tag"}
        res = bulk_tag_builds(sess, tag, BUILD_SAMPLES, size=5)

        self.assertEqual(sess.tagBuildBypass.call_count, 6)
        self.assertEqual(sess.untagBuildBypass.call_count, 0)
        self.assertEqual(sess.multiCall.call_count, 2)


    def test_bulk_untag_nvrs(self):
        sess = self.session(builds=BUILD_SAMPLES,
                            untag_results=repeat(None))

        tag = {"id": 1, "name": "some-tag"}
        res = bulk_untag_nvrs(sess, tag, range(0, 6), size=5)

        self.assertEqual(res, list(zip(BUILD_SAMPLES, repeat([None]))))
        self.assertEqual(sess.getBuild.call_count, 6)
        self.assertEqual(sess.tagBuildBypass.call_count, 0)
        self.assertEqual(sess.untagBuildBypass.call_count, 6)
        self.assertEqual(sess.multiCall.call_count, 3)


    def test_bulk_untag_builds(self):
        sess = self.session(untag_results=repeat(None))

        tag = {"id": 1, "name": "some-tag"}
        res = bulk_untag_builds(sess, tag, BUILD_SAMPLES, size=5)

        self.assertEqual(res, list(zip(BUILD_SAMPLES, repeat([None]))))
        self.assertEqual(sess.tagBuildBypass.call_count, 0)
        self.assertEqual(sess.untagBuildBypass.call_count, 6)
        self.assertEqual(sess.multiCall.call_count, 2)


    def test_bulk_untag_builds_err(self):
        err = {"faultCode": 1}
        tres = [None, err, None, None, None, None]
        sess = self.session(untag_results=tres)

        tag = {"id": 1, "name": "some-tag"}
        res = bulk_untag_builds(sess, tag, BUILD_SAMPLES, size=5)

        self.assertEqual(sess.tagBuildBypass.call_count, 0)
        self.assertEqual(sess.untagBuildBypass.call_count, 6)
        self.assertEqual(sess.multiCall.call_count, 2)


    def test_bulk_move_nvrs(self):
        sess = self.session(builds=BUILD_SAMPLES,
                            tag_results=repeat(None),
                            untag_results=repeat(None))

        tag = {"id": 1, "name": "some-tag"}
        res = bulk_move_nvrs(sess, tag, tag, range(0, 6), size=5)

        self.assertEqual(res, list(zip(BUILD_SAMPLES, repeat([None]))))
        self.assertEqual(sess.getBuild.call_count, 6)
        self.assertEqual(sess.tagBuildBypass.call_count, 6)
        self.assertEqual(sess.untagBuildBypass.call_count, 6)
        self.assertEqual(sess.multiCall.call_count, 5)


    def test_bulk_move_builds(self):
        sess = self.session(tag_results=repeat(None),
                            untag_results=repeat(None))

        tag = {"id": 1, "name": "some-tag"}
        res = bulk_move_builds(sess, tag, tag, BUILD_SAMPLES, size=5)

        self.assertEqual(res, list(zip(BUILD_SAMPLES, repeat([None]))))

        self.assertEqual(sess.tagBuildBypass.call_count, 6)
        self.assertEqual(sess.untagBuildBypass.call_count, 6)
        self.assertEqual(sess.multiCall.call_count, 4)


    def test_bulk_move_builds_err(self):
        # one tagging operation fails, thus one less untagging operation
        err = {"faultCode": 1}
        tres = [None, err, None, None, None, None]
        sess = self.session(tag_results=tres, untag_results=repeat(None))

        tag = {"id": 1, "name": "some-tag"}
        res = bulk_move_builds(sess, tag, tag, BUILD_SAMPLES, size=5)

        self.assertEqual(sess.tagBuildBypass.call_count, 6)
        self.assertEqual(sess.untagBuildBypass.call_count, 5)
        self.assertEqual(sess.multiCall.call_count, 4)

        # every tagging operation fails, thus no untagging operations
        sess = self.session(tag_results=repeat(err))

        res = bulk_move_builds(sess, tag, tag, BUILD_SAMPLES, size=5)

        self.assertEqual(sess.tagBuildBypass.call_count, 6)
        self.assertEqual(sess.untagBuildBypass.call_count, 0)
        self.assertEqual(sess.multiCall.call_count, 2)


#
# The end.
