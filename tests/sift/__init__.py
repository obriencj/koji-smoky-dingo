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

from kojismokydingo.sift import (
    DEFAULT_SIEVES,
    Flagged, Glob, LogicNot, LogicOr,
    ItemSieve, Regex, Sifter, SifterError, Symbol,
)


class NameSieve(ItemSieve):
    name = "name"
    field = "name"


class TypeSieve(ItemSieve):
    name = "type"
    field = "type"


TACOS = {
    "id": 1,
    "type": "food",
    "name": "Tacos",
}

PIZZA = {
    "id": 2,
    "type": "food",
    "name": "Pizza",
}

BEER = {
    "id": 3,
    "type": "drink",
    "name": "Beer",
}

DRAINO = {
    "id": 4,
    "type": "drink",
    "name": "Draino",
}


DATA = [
    TACOS, PIZZA, BEER, DRAINO,
]


class SifterTest(TestCase):


    def compile_sifter(self, src):
        sieves = [NameSieve, TypeSieve]
        sieves.extend(DEFAULT_SIEVES)

        return Sifter(sieves, src)


    def test_symbol_property(self):

        src = """
        (name Pizza)
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], NameSieve))
        self.assertTrue(isinstance(sieves[0], ItemSieve))
        self.assertEqual(sieves[0].name, "name")
        self.assertEqual(sieves[0].field, "name")
        self.assertTrue(isinstance(sieves[0].token, Symbol))
        self.assertEqual(repr(sieves[0]), "(name Symbol('Pizza'))")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue("default" in res)
        self.assertEqual(res["default"], [PIZZA])


    def test_str_property(self):

        src = """
        (name "Pizza")
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], NameSieve))
        self.assertTrue(isinstance(sieves[0], ItemSieve))
        self.assertEqual(sieves[0].name, "name")
        self.assertEqual(sieves[0].field, "name")
        self.assertTrue(isinstance(sieves[0].token, str))
        self.assertEqual(repr(sieves[0]), "(name 'Pizza')")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue("default" in res)
        self.assertEqual(res["default"], [PIZZA])


    def test_regex_property(self):

        src = """
        (name /zza$/)
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], NameSieve))
        self.assertTrue(isinstance(sieves[0], ItemSieve))
        self.assertEqual(sieves[0].name, "name")
        self.assertEqual(sieves[0].field, "name")
        self.assertTrue(isinstance(sieves[0].token, Regex))
        self.assertEqual(repr(sieves[0]), "(name Regex('zza$'))")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue("default" in res)
        self.assertEqual(res["default"], [PIZZA])


    def test_glob_property(self):

        src = """
        (name |P*a|)
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], NameSieve))
        self.assertTrue(isinstance(sieves[0], ItemSieve))
        self.assertEqual(sieves[0].name, "name")
        self.assertEqual(sieves[0].field, "name")
        self.assertTrue(isinstance(sieves[0].token, Glob))
        self.assertEqual(repr(sieves[0]), "(name Glob('P*a'))")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue("default" in res)
        self.assertEqual(res["default"], [PIZZA])


    def test_flag(self):

        src = """
        (flag munch (type food))
        (flag gulp (type drink))
        (flag poison (name Draino))
        (flag yum (flagged munch gulp) (not (flagged poison)))
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 4)

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))

        self.assertFalse("default" in res)
        self.assertTrue("munch" in res)
        self.assertTrue("gulp" in res)
        self.assertTrue("poison" in res)
        self.assertTrue("yum" in res)

        self.assertEqual(res["munch"], [TACOS, PIZZA])
        self.assertEqual(res["gulp"], [BEER, DRAINO])
        self.assertEqual(res["poison"], [DRAINO])
        self.assertEqual(res["yum"], [TACOS, PIZZA, BEER])


    def test_logic(self):

        src = """
        (flag good (or (type food)
                       (and (type drink)
                            (not (name Draino)))))
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))

        self.assertFalse("default" in res)
        self.assertTrue("good" in res)

        self.assertEqual(res["good"], [TACOS, PIZZA, BEER])


    def test_flag_implicit_and(self):

        src = """
        (flag fine (name Pizza) (type food))
        (flagged fine)
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 2)

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))

        self.assertTrue("default" in res)
        self.assertTrue("fine" in res)

        self.assertEqual(res["fine"], [PIZZA])
        self.assertEqual(res["default"], [PIZZA])

        src = """
        (flag gross (name Pizza) (type drink))
        (flagged gross)
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 2)

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))

        self.assertFalse("default" in res)
        self.assertFalse("gross" in res)


    def check_not_aliases(self, src):
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 2)

        self.assertTrue(isinstance(sieves[1], LogicNot))
        self.assertEqual(len(sieves[1]._exprs), 1)
        self.assertTrue(isinstance(sieves[1]._exprs[0], Flagged))

        res = sifter(None, DATA)
        self.assertEqual(res["poison"], [DRAINO])
        self.assertEqual(res["default"], [TACOS, PIZZA, BEER])


    def test_not_aliases(self):
        # these should all be equivalent
        sources = [
            """
            (flag poison (name Draino))
            (!flagged poison)
            """,

            """
            (flag poison (name Draino))
            (not-flagged poison)
            """,

            """
            (flag poison (name Draino))
            (! (flagged poison))
            """,

            """
            (flag poison (name Draino))
            (not (flagged poison))
            """,

            """
            (flag poison (name Draino))
            (!? poison)
            """,

            """
            (flag poison (name Draino))
            (!poison?)
            """,
        ]

        for src in sources:
            self.check_not_aliases(src)


    def check_flagged_aliases(self, src):
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 2)

        self.assertTrue(isinstance(sieves[1], Flagged))

        res = sifter(None, DATA)
        self.assertEqual(res["poison"], [DRAINO])
        self.assertEqual(res["default"], [DRAINO])


    def test_flagged_aliases(self):
        sources = [
            """
            (flag poison (name Draino))
            (flagged poison)
            """,

            """
            (flag poison (name Draino))
            (? poison)
            """,

            """
            (flag poison (name Draino))
            (poison?)
            """,
        ]

        for src in sources:
            self.check_flagged_aliases(src)


    def test_syntax_error(self):
        src = """
        ((name Pizza))
        """
        self.assertRaises(SifterError, self.compile_sifter, src)

        src = """
        ("name" Pizza)
        """
        self.assertRaises(SifterError, self.compile_sifter, src)

        src = """
        (/name/ Pizza)
        """
        self.assertRaises(SifterError, self.compile_sifter, src)

        src = """
        (|name| Pizza)
        """
        self.assertRaises(SifterError, self.compile_sifter, src)

        src = """
        ()
        """
        self.assertRaises(SifterError, self.compile_sifter, src)

        src = """
        name Pizza
        """
        self.assertRaises(SifterError, self.compile_sifter, src)

        src = """
        (name "Pizza
        """
        self.assertRaises(SifterError, self.compile_sifter, src)


    def test_comments(self):
        src = """
        # ()
        """
        sifter = self.compile_sifter(src)
        self.assertEqual(len(sifter.sieve_exprs()), 0)

        src = """
        (name Pizza) # ()
        """
        sifter = self.compile_sifter(src)
        self.assertEqual(len(sifter.sieve_exprs()), 1)

        src = """
        ; this is a comment
        (name Pizza) ; () is as well
        ; so is this
        """
        sifter = self.compile_sifter(src)
        self.assertEqual(len(sifter.sieve_exprs()), 1)


#
# The end.
