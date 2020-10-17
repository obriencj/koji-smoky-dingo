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


from mock import MagicMock
from unittest import TestCase

from kojismokydingo.sift import Sifter, SifterError
from kojismokydingo.sift.builds import (
    EVRCompare,
    EVRCompareEQ, EVRCompareNE,
    EVRCompareLT, EVRCompareLE,
    EVRCompareGT, EVRCompareGE,
    build_info_sifter,
)

from ..builds import (
    BUILD_SAMPLE_1, BUILD_SAMPLE_1_1,
    BUILD_SAMPLE_2, BUILD_SAMPLE_3,
    BUILD_SAMPLE_4, BUILD_SAMPLE_5, BUILD_SAMPLES,
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
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)
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
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)
        self.assertFalse(res)

        src = """
        (< 1:0)
        """
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1,
                          BUILD_SAMPLE_2, BUILD_SAMPLE_3])

        src = """
        (< 1:9.9)
        """
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)
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
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)
        self.assertFalse(res)

        src = """
        (<= 1:0)
        """
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1,
                          BUILD_SAMPLE_2, BUILD_SAMPLE_3])

        src = """
        (<= 1:9-9)
        """
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)
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
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)
        self.assertEqual(res["default"], BUILD_SAMPLES)

        src = """
        (> 1:0)
        """
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (> 1:9.9)
        """
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)
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
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)
        self.assertEqual(res["default"], BUILD_SAMPLES)

        src = """
        (>= 1:0)
        """
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)
        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (>= 1:9.9)
        """
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)
        self.assertFalse(res)


    def test_owner(self):
        session = MagicMock()

        get_user = session.getUser
        get_user.side_effect = [USER_SIEGE]

        src = """
        (owner siege)
        """
        sifter = build_info_sifter(src)
        res = sifter(session, BUILD_SAMPLES)

        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1_1, BUILD_SAMPLE_4])


    def test_state(self):
        src = """
        (state 1)
        """
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)

        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_3, BUILD_SAMPLE_4, BUILD_SAMPLE_5])

        src = """
        (state COMPLETE)
        """
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)

        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_3, BUILD_SAMPLE_4, BUILD_SAMPLE_5])
        src = """
        (state 2)
        """
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)

        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1, BUILD_SAMPLE_2])

        src = """
        (state DELETED)
        """
        sifter = build_info_sifter(src)
        res = sifter(None, BUILD_SAMPLES)

        self.assertEqual(res["default"],
                         [BUILD_SAMPLE_1, BUILD_SAMPLE_1_1, BUILD_SAMPLE_2])

        src = """
        (state 999)
        """
        self.assertRaises(SifterError, build_info_sifter, src)

        src = """
        (state INCOMPREHENSIBLE)
        """
        self.assertRaises(SifterError, build_info_sifter, src)


#
# The end.
