# This library free software; you can redistribute it and/or modify
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
from unittest.mock import MagicMock

from kojismokydingo.builds import build_id_sort
from kojismokydingo.sift import Sifter, SifterError
from kojismokydingo.sift.builds import (
    CGImportedSieve, EVRCompare,
    EVRCompareEQ, EVRCompareNE,
    EVRCompareLT, EVRCompareLE,
    EVRCompareGT, EVRCompareGE,
    ImportedSieve, TaggedSieve, InheritedSieve,
    StateSieve, TypeSieve,
    build_info_sifter, sift_builds, sift_nvrs, )

from ..builds import (
    BUILD_SAMPLE_1, BUILD_SAMPLE_1_1,
    BUILD_SAMPLE_2, BUILD_SAMPLE_3,
    BUILD_SAMPLE_4, BUILD_SAMPLE_5, BUILD_SAMPLES, )

from ..tags import (
    TAG_1, TAG_1_CANDIDATE, TAG_1_RELEASED,
    TAG_2, TAG_2_CANDIDATE, TAG_2_RELEASED,
    TAGS, inheritance,
)


BUILD_SAMPLES = list(BUILD_SAMPLES)


USER_SIEGE = {
    "name": "siege",
    "id": 1,
}

USER_ZOE = {
    "name": "zoe",
    "id": 2,
}

USER_SANTA = {
    "name": "santa",
    "id": 3,
}


class SifterTest(TestCase):

    maxDiff = None


    def test_evr_compare_eq(self):
        src = """
        (== 1.0)
        """
        sifter = build_info_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], EVRCompare))
        self.assertTrue(isinstance(sieves[0], EVRCompareEQ))
        self.assertEqual(repr(sieves[0]), "(== 1.0)")

        res = sifter(None, BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_1])

        src = """
        (== 1:5.5.1-1)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_5])


    def test_evr_compare_ne(self):
        src = """
        (flag nope (not (== 1.0)))
        (!= 1.0)
        """
        sifter = build_info_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 2)
        self.assertTrue(isinstance(sieves[1], EVRCompare))
        self.assertTrue(isinstance(sieves[1], EVRCompareNE))
        self.assertEqual(repr(sieves[1]), "(!= 1.0)")

        res = sifter(None, BUILD_SAMPLES)

        self.assertEqual(res["nope"],
                         [BUILD_SAMPLE_1_1,
                          BUILD_SAMPLE_2, BUILD_SAMPLE_3,
                          BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        self.assertEqual(res["default"], res["nope"])

        src = """
        (!= 9.9)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], BUILD_SAMPLES)


    def test_evr_compare_lt(self):
        src = """
        (< 2.2)
        """
        sifter = build_info_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], EVRCompare))
        self.assertTrue(isinstance(sieves[0], EVRCompareLT))
        self.assertEqual(repr(sieves[0]), "(< 2.2)")

        res = sifter(None, BUILD_SAMPLES)

        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1,
                          BUILD_SAMPLE_2])

        src = """
        (< 0)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertFalse(res)

        src = """
        (< 1:0)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1,
                          BUILD_SAMPLE_2, BUILD_SAMPLE_3])

        src = """
        (< 1:9.9)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], BUILD_SAMPLES)


    def test_evr_compare_le(self):
        src = """
        (<= 2.0)
        """
        sifter = build_info_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], EVRCompare))
        self.assertTrue(isinstance(sieves[0], EVRCompareLE))
        self.assertEqual(repr(sieves[0]), "(<= 2.0)")

        res = sifter(None, BUILD_SAMPLES)

        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1, BUILD_SAMPLE_2])

        src = """
        (<= 0)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertFalse(res)

        src = """
        (<= 1:0)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1,
                          BUILD_SAMPLE_2, BUILD_SAMPLE_3])

        src = """
        (<= 1:9-9)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], BUILD_SAMPLES)


    def test_evr_compare_gt(self):
        src = """
        (> 2.0)
        """
        sifter = build_info_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], EVRCompare))
        self.assertTrue(isinstance(sieves[0], EVRCompareGT))
        self.assertEqual(repr(sieves[0]), "(> 2.0)")

        res = sifter(None, BUILD_SAMPLES)

        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_3, BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (> 0)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], BUILD_SAMPLES)

        src = """
        (> 1:0)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (> 1:9.9)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertFalse(res)


    def test_evr_compare_ge(self):
        src = """
        (>= 2.0)
        """
        sifter = build_info_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], EVRCompare))
        self.assertTrue(isinstance(sieves[0], EVRCompareGE))
        self.assertEqual(repr(sieves[0]), "(>= 2.0)")

        res = sifter(None, BUILD_SAMPLES)

        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_3,
                          BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (>= 0)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], BUILD_SAMPLES)

        src = """
        (>= 1:0)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (>= 1:9.9)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertFalse(res)


    def test_owner(self):
        session = MagicMock()

        get_user = session.getUser
        get_user.side_effect = [USER_SIEGE]

        src = """
        (owner siege)
        """
        res = sift_builds(session, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1_1, BUILD_SAMPLE_4])


    def test_state(self):
        src = """
        (state 1)
        """
        sifter = build_info_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], StateSieve))
        self.assertEqual(repr(sieves[0]), "(state Number(1))")

        res = sifter(None, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_3, BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (state COMPLETE)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_3, BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (state complete)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_3, BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (state "complete")
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_3, BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (state 2)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1, BUILD_SAMPLE_2])

        src = """
        (state DELETED)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1, BUILD_SAMPLE_2])

        src = """
        (state COMPLETE DELETED)
        """
        sifter = build_info_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], StateSieve))
        self.assertEqual(repr(sieves[0]),
                         "(state Symbol('COMPLETE') Symbol('DELETED'))")

        res = sifter(None, BUILD_SAMPLES)
        self.assertEqual(res["default"], BUILD_SAMPLES)

        src = """
        (state 999)
        """
        self.assertRaises(SifterError, build_info_sifter, src)

        src = """
        (state INCOMPREHENSIBLE)
        """
        self.assertRaises(SifterError, build_info_sifter, src)


TAGGED = {
    BUILD_SAMPLE_1["id"]: [],
    BUILD_SAMPLE_1_1["id"]: [],
    BUILD_SAMPLE_2["id"]: [],
    BUILD_SAMPLE_3["id"]: [TAG_1_RELEASED, TAG_1_CANDIDATE],
    BUILD_SAMPLE_4["id"]: [TAG_1_CANDIDATE],
    BUILD_SAMPLE_5["id"]: [TAG_2_CANDIDATE],
}


class InheritedSieveTest(TestCase):


    def get_session(self):

        wanted = []
        inhers = []
        blds = []

        def mc(strict=False):
            if wanted:
                res = [[TAGS.get(w)] for w in wanted]
                wanted[:] = []
            elif inhers:
                res = [[inheritance(TAGS.get(w))] for w in inhers]
                inhers[:] = []
            elif blds:
                res = [[TAGGED.get(b, ())] for b in blds]
                blds[:] = []
            else:
                self.assertFalse(True)
            return res

        sess = MagicMock()
        sess.getTag.side_effect = wanted.append
        sess.getFullInheritance.side_effect = inhers.append
        sess.listTags.side_effect = lambda build: blds.append(build)
        sess.multiCall.side_effect = mc
        sess.getKojiVersion.side_effect = ["1.22"]

        return sess


    def test_inherited(self):
        src = """
        (inherited tag-1.0)
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertFalse(res)

        src = """
        (inherited tag-1.0-released)
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_3])

        src = """
        (inherited tag-2.0-released)
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_3])


class TaggedSieveTest(TestCase):


    def get_session(self, tag_map=TAGGED):

        blds = []

        def get_tags(strict=False):
            return [[tag_map.get(b, ())] for b in blds]

        sess = MagicMock()
        sess.listTags.side_effect = lambda build: blds.append(build)
        sess.multiCall.side_effect = get_tags

        return sess


    def test_tagged(self):
        src = """
        (tagged)
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"], BUILD_SAMPLES[3:])

        src = """
        (!tagged)
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1, BUILD_SAMPLE_2])

        src = """
        (tagged tag-1.0-released)
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_3])

        src = """
        (tagged 1013)
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_3])

        src = """
        (tagged |*-released|)
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_3])

        src = """
        (tagged tag-1.0-candidate tag-2.0-candidate)
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_3, BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (tagged 1012 1022)
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_3, BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (tagged |*-candidate|)
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_3, BUILD_SAMPLE_4, BUILD_SAMPLE_5])


    def test_tagged_symgroup(self):

        src = """
        (tagged {1012,1022})
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_3, BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (tagged {1010..1019})
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_3, BUILD_SAMPLE_4])

        src = """
        (tagged {1020..1029})
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_5])

        src = """
        (tagged tag-{1,2}.0-candidate)
        """
        sifter = build_info_sifter(src)
        res = sifter(self.get_session(), BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_3, BUILD_SAMPLE_4, BUILD_SAMPLE_5])


class ImportedSieveTest(TestCase):


    def test_imported(self):
        src = """
        (imported)
        """
        sifter = build_info_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], ImportedSieve))
        self.assertEqual(repr(sieves[0]), "(imported)")

        res = sifter(None, BUILD_SAMPLES)
        self.assertEqual(res["default"], BUILD_SAMPLES[:-1])

        src = """
        (!imported)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLES[-1]])


class TypeSieveTest(TestCase):

    def test_type(self):
        src = """
        (type rpm)
        """
        sifter = build_info_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], TypeSieve))
        self.assertEqual(repr(sieves[0]), "(type Symbol('rpm'))")

        res = sifter(None, BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_5])

        src = """
        (type)
        """
        self.assertRaises(SifterError, build_info_sifter, src)


class CGImportedSieveTest(TestCase):

    def test_cg_imported(self):
        src = """
        (cg-imported example-cg)
        """
        sifter = build_info_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], CGImportedSieve))
        self.assertEqual(repr(sieves[0]), "(cg-imported Symbol('example-cg'))")

        res = sifter(None, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1, BUILD_SAMPLE_3])

        src = """
        (cg-imported other-cg)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_2, BUILD_SAMPLE_3])

        src = """
        (cg-imported 902)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_2, BUILD_SAMPLE_3])

        src = """
        (!cg-imported)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_4, BUILD_SAMPLE_5])


class EVRHighLowTest(TestCase):


    def test_evr_high(self):

        src = """
        (evr-high)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_5])

        src = """
        (!evr-high)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1, BUILD_SAMPLE_2,
                          BUILD_SAMPLE_3, BUILD_SAMPLE_4])


    def test_evr_high_count(self):

        src = """
        (evr-high count: 1)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_5])

        src = """
        (evr-high count: 2)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_5, BUILD_SAMPLE_4])

        src = """
        (!evr-high count: 1)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1, BUILD_SAMPLE_2,
                          BUILD_SAMPLE_3, BUILD_SAMPLE_4])

        src = """
        (!evr-high count: 2)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1, BUILD_SAMPLE_2,
                          BUILD_SAMPLE_3])

        src = """
        (evr-high count: 0)
        """
        with self.assertRaises(SifterError):
            sift_builds(None, src, BUILD_SAMPLES)

        src = """
        (evr-high count: -1)
        """
        with self.assertRaises(SifterError):
            sift_builds(None, src, BUILD_SAMPLES)

        src = """
        (evr-high count: tacos)
        """
        with self.assertRaises(SifterError):
            sift_builds(None, src, BUILD_SAMPLES)


    def test_evr_low(self):

        src = """
        (evr-low)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_1])

        src = """
        (!evr-low)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1_1, BUILD_SAMPLE_2, BUILD_SAMPLE_3,
                          BUILD_SAMPLE_4, BUILD_SAMPLE_5])


    def test_evr_low_count(self):

        src = """
        (evr-low count: 1)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_1])

        src = """
        (evr-low count: 2)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"], [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1])

        src = """
        (!evr-low count: 1)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1_1, BUILD_SAMPLE_2, BUILD_SAMPLE_3,
                          BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (!evr-low count: 2)
        """
        res = sift_builds(None, src, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_2, BUILD_SAMPLE_3,
                          BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (evr-low count: 0)
        """
        with self.assertRaises(SifterError):
            sift_builds(None, src, BUILD_SAMPLES)

        src = """
        (evr-low count: -1)
        """
        with self.assertRaises(SifterError):
            sift_builds(None, src, BUILD_SAMPLES)

        src = """
        (evr-low count: tacos)
        """
        with self.assertRaises(SifterError):
            sift_builds(None, src, BUILD_SAMPLES)


class SiftNVRsTest(TestCase):


    def test_sift_nvrs(self):
        # most of the interactions with EVR filtering are covered in
        # the SifterTest, this is just verifying that the simplified
        # interface via sift_nvrs (and subsequently sift_builds) works
        # as well

        session = MagicMock()

        mc = session.multiCall
        mc.side_effect = [([bld] for bld in BUILD_SAMPLES), ]

        src = """
        (>= 1:0)
        """

        nvrs = (bld["nvr"] for bld in BUILD_SAMPLES)

        res = sift_nvrs(session, src, nvrs)
        self.assertEqual(res["default"], [BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        self.assertEqual(session.getBuild.call_count, len(BUILD_SAMPLES))
        self.assertEqual(mc.call_count, 1)


#
# The end.
