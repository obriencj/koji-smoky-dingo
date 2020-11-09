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


import re
import six

from collections import OrderedDict
from unittest import TestCase

from kojismokydingo.sift import (
    DEFAULT_SIEVES,
    AllItems, Flagged, Glob,
    Item, ItemMatch, ItemPath, ItemPathSieve, ItemSieve,
    LogicNot, LogicOr, Null, Number,
    Regex, Sieve, Sifter, SifterError, Symbol, SymbolGroup,
    ensure_all_int_or_str, ensure_all_matcher, ensure_all_symbol,
    ensure_int, ensure_int_or_str, ensure_matcher,
    ensure_str, ensure_symbol,
)


class MatcherTest(TestCase):

    DATA = [
        1, 2, "3", "4", "Hello", "World", (), [], 99, 98, 0, "", None,
        "987", "98",
    ]


    def in_data(self, match, expected_index, expected_value):
        i = self.DATA.index(match)
        v = self.DATA[i] if i >= 0 else None

        self.assertEqual(i, expected_index, repr(match))
        self.assertEqual(v, expected_value, repr(match))


    def not_in_data(self, match):
        try:
            i = self.DATA.index(match)
        except ValueError:
            i = -1
        self.assertEqual(i, -1, repr(match))


    def test_null(self):
        m = Null()
        self.in_data(m, 12, None)


    def test_symbol(self):
        self.in_data(Symbol("Hello"), 4, "Hello")

        self.in_data(Symbol("3"), 2, "3")
        self.in_data(Symbol(""), 11, "")

        self.not_in_data(Symbol("hello"))
        self.not_in_data(Symbol("ell"))
        self.not_in_data(Symbol("1"))
        self.not_in_data(Symbol("()"))
        self.not_in_data(Symbol("[]"))
        self.not_in_data(Symbol("None"))


    def test_glob(self):
        self.in_data(Glob("Hello"), 4, "Hello")
        self.in_data(Glob("*ll*"), 4, "Hello")
        self.in_data(Glob("*o"), 4, "Hello")

        self.in_data(Glob("HELLO", True), 4, "Hello")
        self.in_data(Glob("*LL*", True), 4, "Hello")
        self.in_data(Glob("*O", True), 4, "Hello")
        self.in_data(Glob("hello", True), 4, "Hello")
        self.in_data(Glob("*ll*", True), 4, "Hello")
        self.in_data(Glob("*o", True), 4, "Hello")

        self.in_data(Glob("?o*"), 5, "World")
        self.in_data(Glob("*d"), 5, "World")

        self.in_data(Glob(""), 11, "")

        self.not_in_data(Glob("hello"))
        self.not_in_data(Glob("ll"))
        self.not_in_data(Glob("o"))
        self.not_in_data(Glob("1"))
        self.not_in_data(Glob("()"))
        self.not_in_data(Glob("[]"))
        self.not_in_data(Glob("None"))


    def test_regex(self):
        self.in_data(Regex("Hello"), 4, "Hello")
        self.in_data(Regex("ll"), 4, "Hello")
        self.in_data(Regex("o$"), 4, "Hello")

        self.in_data(Regex("HELLO", "i"), 4, "Hello")
        self.in_data(Regex("LL", "i"), 4, "Hello")
        self.in_data(Regex("O$", "i"), 4, "Hello")
        self.in_data(Regex("hello", "i"), 4, "Hello")
        self.in_data(Regex("ll", "i"), 4, "Hello")
        self.in_data(Regex("o$", "i"), 4, "Hello")

        self.in_data(Regex("^.o"), 5, "World")
        self.in_data(Regex("d$"), 5, "World")

        self.in_data(Regex(r"\d"), 2, "3")
        self.in_data(Regex(r"\d\d\d"), 13, "987")
        self.in_data(Regex(r"^\d{3}$"), 13, "987")
        self.in_data(Regex(r"\d\d"), 13, "987")
        self.in_data(Regex(r"\d{2}"), 13, "987")
        self.in_data(Regex(r"^\d\d$"), 14, "98")
        self.in_data(Regex(r"^\d{2}$"), 14, "98")

        self.in_data(Regex(""), 2, "3")
        self.in_data(Regex("()"), 2, "3")
        self.in_data(Regex("^$"), 11, "")

        self.in_data(Regex(r"\d"), 2, "3")

        self.not_in_data(Regex("hello"))
        self.not_in_data(Regex(r"\(\)"))
        self.not_in_data(Regex(r"\[\]"))
        self.not_in_data(Regex("None"))

        self.assertRaises(re.error, Regex, "[")


    def test_number(self):
        self.in_data(Number(1), 0, 1)
        self.in_data(Number(2), 1, 2)
        self.in_data(Number(3), 2, "3")

        self.not_in_data(Number(9))

        self.assertRaises(ValueError, Number, "Hello")


class ItemPathTest(TestCase):

    DATA = {
        "foo": [1, 9],
        "bar": [2, 3, 4, 5, 6],
        "baz": {"food": True, "drink": False},
        "qux": {"food": False, "drink": True},
    }


    def in_path(self, paths, expected):
        pth = ItemPath(paths)
        self.assertEqual(list(pth.get(self.DATA)), expected)


    def test_symbol(self):
        self.in_path([Symbol("foo")], [[1, 9]])
        self.in_path([Symbol("bar")], [[2, 3, 4, 5, 6]])
        self.in_path([Symbol("baz"), Symbol("food")], [True])
        self.in_path([Symbol("qux"), Symbol("food")], [False])
        self.in_path([Symbol("quxx"), Symbol("food")], [])


    def test_slice(self):
        self.in_path(["foo", slice(None)], [1, 9])
        self.in_path(["bar", slice(None)], [2, 3, 4, 5, 6])

        self.in_path(["foo", slice(1, None)], [9])
        self.in_path(["bar", slice(1, -1)], [3, 4, 5])


class NameSieve(ItemSieve):

    name = field = "name"


class TypeSieve(ItemSieve):

    name = field = "type"


class CategorySieve(ItemSieve):

    name = field = "category"


class BrandSieve(ItemSieve):

    name = field = "brand"


class Poke(Sieve):
    # for testing cache. Increments a poke counter each time it sees a
    # data item. If a maximum value is provided, then filters for only
    # those items which have been poked up-to that many times
    # previously. Thus (poke 0) will poke and then filter for only
    # those items never previously poked.

    name = "poke"

    def __init__(self, sifter, count=-1):
        super(Poke, self).__init__(sifter)
        self._max = ensure_int(count)


    def check(self, _session, data):
        cache = self.get_cache(data)
        seen = cache.get("count", 0)
        cache["count"] = seen + 1

        return (self._max < 0) or (seen <= self._max)


TACOS = {
    "id": 1,
    "type": "food",
    "category": 1,
    "name": "Tacos",
    "keywords": ["yummy", "crunchy", "spicy", "beef", "cheese", "lettuce"],
}

PIZZA = {
    "id": 2,
    "type": "food",
    "category": "1",
    "name": "Pizza",
    "brand": None,
    "keywords": ["yummy", "cheese", "pepperoni"],
}

BEER = {
    "id": 3,
    "type": "drink",
    "category": "1",
    "name": "Beer",
    "keywords": ["yummy", "hops", "alcohol"],
}

DRAINO = {
    "id": 4,
    "type": "drink",
    "category": 2,
    "name": "Draino",
    "brand": "Draino",
    "keywords": ["yucky", "deadly", "poison"],
}


DATA = [
    TACOS, PIZZA, BEER, DRAINO,
]


class SifterTest(TestCase):

    def compile_sifter(self, src):
        sieves = [NameSieve, TypeSieve, BrandSieve, CategorySieve, Poke]
        sieves.extend(DEFAULT_SIEVES)

        return Sifter(sieves, src)


    def test_int_item(self):
        src = """
        (category 1)
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], CategorySieve))
        self.assertTrue(isinstance(sieves[0], ItemSieve))
        self.assertEqual(repr(sieves[0]), "(category Number(1))")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue("default" in res)
        self.assertEqual(res["default"], [TACOS, PIZZA, BEER])

        src = """
        (category 2)
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], CategorySieve))
        self.assertTrue(isinstance(sieves[0], ItemSieve))
        self.assertEqual(repr(sieves[0]), "(category Number(2))")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue("default" in res)
        self.assertEqual(res["default"], [DRAINO])


    def test_has_item(self):

        src = """
        (brand)
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], BrandSieve))
        self.assertTrue(isinstance(sieves[0], ItemSieve))
        self.assertEqual(repr(sieves[0]), "(brand)")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue("default" in res)
        self.assertEqual(res["default"], [DRAINO])


    def test_null_item(self):

        src = """
        (brand null)
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], BrandSieve))
        self.assertTrue(isinstance(sieves[0], ItemSieve))
        self.assertEqual(repr(sieves[0]), "(brand Null())")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue("default" in res)
        self.assertEqual(res["default"], [PIZZA])


    def test_symbol_item(self):

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


    def test_str_item(self):

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

        src = r"""
        (name "Pizza\nBeer")
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], NameSieve))
        self.assertTrue(isinstance(sieves[0], ItemSieve))
        self.assertEqual(sieves[0].name, "name")
        self.assertEqual(sieves[0].field, "name")
        self.assertTrue(isinstance(sieves[0].token, six.text_type))

        if six.PY3:
            self.assertEqual(repr(sieves[0]), r"(name 'Pizza\nBeer')")
        elif six.PY2:
            self.assertEqual(repr(sieves[0]), r"(name u'Pizza\nBeer')")

        res = sifter(None, DATA)
        self.assertFalse(res)


    def test_regex_item(self):

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

        src = """
        (name /ZZA$/i)
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], NameSieve))
        self.assertTrue(isinstance(sieves[0], ItemSieve))
        self.assertEqual(sieves[0].name, "name")
        self.assertEqual(sieves[0].field, "name")
        self.assertTrue(isinstance(sieves[0].token, Regex))
        self.assertEqual(repr(sieves[0]), "(name Regex('ZZA$', flags='i'))")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue("default" in res)
        self.assertEqual(res["default"], [PIZZA])

        src = r"""
        (category /\d/)
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)
        self.assertTrue(isinstance(sieves[0], CategorySieve))
        self.assertTrue(isinstance(sieves[0], ItemSieve))
        self.assertEqual(sieves[0].name, "category")
        self.assertEqual(sieves[0].field, "category")
        self.assertTrue(isinstance(sieves[0].token, Regex))
        self.assertEqual(repr(sieves[0]), r"(category Regex('\\d'))")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue("default" in res)
        self.assertEqual(res["default"], [PIZZA, BEER])


    def test_glob_item(self):

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
        self.assertEqual(repr(sieves[0]),
                         "(flag Symbol('munch') (type Symbol('food')))")

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


    def test_not(self):

        src = """
        (not (type))
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)

        self.assertEqual(repr(sieves[0]),
                         "(not (type))")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))
        self.assertFalse(res)

        src = """
        (flag everything)
        (not (everything?) (or (type food drink)))
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 2)

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))

        self.assertFalse("default" in res)
        self.assertTrue("everything" in res)
        self.assertEqual(res["everything"], DATA)


    def test_or(self):
        src = """
        (or (name) (type))
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 1)

        self.assertEqual(repr(sieves[0]),
                         "(or (name) (type))")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))
        self.assertEqual(res["default"], DATA)


    def test_flag_implicit_and(self):

        src = """
        (flag fine (name Pizza) (type food))
        (flagged fine)
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 2)

        self.assertEqual(repr(sieves[1]),
                         "(flagged Symbol('fine'))")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))

        self.assertTrue("default" in res)
        self.assertTrue("fine" in res)

        self.assertEqual(res["fine"], [PIZZA])
        self.assertEqual(res["default"], [PIZZA])

        src = """
        (flag gross (name Pizza) (type drink) (type food))
        (flagged gross)
        """
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 2)

        self.assertEqual(repr(sieves[1]),
                         "(flagged Symbol('gross'))")

        res = sifter(None, DATA)
        self.assertTrue(isinstance(res, dict))

        self.assertFalse("default" in res)
        self.assertFalse("gross" in res)


    def check_not_aliases(self, src):
        sifter = self.compile_sifter(src)

        sieves = sifter.sieve_exprs()
        self.assertEqual(len(sieves), 2)

        self.assertTrue(isinstance(sieves[1], LogicNot))
        self.assertEqual(len(sieves[1].tokens), 1)
        self.assertTrue(isinstance(sieves[1].tokens[0], Flagged))

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


    def test_sifter_error(self):

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
        (999 Pizza)
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

        src = """
        (blame Pizza)
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


    def test_item(self):

        src = """
        (item name Pizza)
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], [PIZZA])

        src = """
        (item name Pizza Tacos)
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], [TACOS, PIZZA])

        src = """
        ([])
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], [TACOS, PIZZA, BEER, DRAINO])

        src = """
        ([])
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, [{}])
        self.assertFalse(res)

        src = """
        (keywords[] spicy)
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], [TACOS])

        src = """
        (item keywords[] spicy)
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], [TACOS])

        src = """
        (not (.keywords[] spicy poison))
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], [PIZZA, BEER])

        src = """
        (!item .keywords[] spicy poison)
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], [PIZZA, BEER])

        src = """
        (.keywords[0] yummy)
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], [TACOS, PIZZA, BEER])

        src = """
        (.keywords[{0,1}] cheese)
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], [PIZZA])

        src = """
        (keywords[] |c*|)
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], [TACOS, PIZZA])

        src = """
        (keywords[] /mm/)
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], [TACOS, PIZZA, BEER])

        src = """
        ([0])
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, [[], []])
        self.assertFalse(res)

        src = """
        ([{0..1}][/ran/])
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, [[], []])
        self.assertFalse(res)

        src = """
        ([0])
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, [])
        self.assertFalse(res)

        src = """
        (.foo[{0..1}])
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, [])
        self.assertFalse(res)

        src = """
        ([/ran/])
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], [DRAINO])


    def test_cache(self):

        src = """
        (poke)
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], DATA)

        res = sifter(None, DATA)
        self.assertEqual(res["default"], DATA)

        src = """
        (poke 0)
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)
        self.assertEqual(res["default"], DATA)

        res = sifter(None, DATA)
        self.assertFalse(res)

        sifter.reset()
        res = sifter(None, DATA)
        self.assertEqual(res["default"], DATA)

        src = """
        (flag 1st (type food) (poke))
        (flag 2nd (name Draino) (poke))
        (flag 3rd (type drink) (poke 0))
        (flag keep (poke 1))
        (!poke 2)
        """
        sifter = self.compile_sifter(src)
        res = sifter(None, DATA)

        self.assertEqual(res["1st"], [TACOS, PIZZA])
        self.assertEqual(res["2nd"], [DRAINO])
        self.assertEqual(res["3rd"], [BEER])
        self.assertEqual(res["keep"], [TACOS, PIZZA, BEER])
        self.assertEqual(res["default"], [DRAINO])

        che = sifter.get_cache("poke", TACOS)
        self.assertEqual(che["count"], 3)

        che = sifter.get_cache("poke", PIZZA)
        self.assertEqual(che["count"], 3)

        che = sifter.get_cache("poke", BEER)
        self.assertEqual(che["count"], 3)

        che = sifter.get_cache("poke", DRAINO)
        self.assertEqual(che["count"], 4)


class EnsureTypeTest(TestCase):

    def test_ensure_int(self):
        values = (1, Number(5))
        for val in values:
            self.assertTrue(int(val) is ensure_int(val))

        bad_values = (None, Null(), Glob("*"), Regex(".*"),
                      Symbol("100"), "100", [], ())
        for val in bad_values:
            self.assertRaises(SifterError, ensure_int, val)


    def test_ensure_int_or_str(self):
        int_values = (1, Number(5))
        for val in int_values:
            res = ensure_int_or_str(val)
            self.assertTrue(type(res), int)
            self.assertTrue(val == res)

        str_values = ("hello", Symbol("hello"))
        for val in str_values:
            res = ensure_int_or_str(val)
            self.assertTrue(type(res), str)
            self.assertTrue(val == res)

        bad_values = (None, Null(), Glob("*"), Regex(".*"), [], ())
        for val in bad_values:
            self.assertRaises(SifterError, ensure_int_or_str, val)

        good_values = []
        good_values.extend(int_values)
        good_values.extend(str_values)

        self.assertEqual(good_values, ensure_all_int_or_str(good_values))
        self.assertRaises(SifterError, ensure_all_int_or_str, bad_values)


    def test_ensure_matcher(self):
        values = ("hello", Null(), Number(5), Symbol("hello"),
                  Glob("*"), Regex(".*"))
        for val in values:
            self.assertTrue(val is ensure_matcher(val))

        bad_values = (None, [], (), 123)
        for val in bad_values:
            self.assertRaises(SifterError, ensure_matcher, val)

        self.assertEqual(list(values), ensure_all_matcher(values))
        self.assertRaises(SifterError, ensure_all_matcher, bad_values)


    def test_ensure_str(self):
        values = (1, Number(5), "1", Symbol("hello"))
        for val in values:
            self.assertEqual(str(val), ensure_str(val))

        bad_values = (None, Null(), Glob("*"), Regex(".*"), [], ())
        for val in bad_values:
            self.assertRaises(SifterError, ensure_str, val)


    def test_ensure_symbol(self):
        val = Symbol("Hello")
        self.assertTrue(val is ensure_symbol(val))

        good_values = [val]

        bad_values = (None, Null(), 123, Number(5), "wut",
                      Glob("*"), Regex(".*"), [], ())
        for val in bad_values:
            self.assertRaises(SifterError, ensure_symbol, val)

        self.assertEqual(good_values, ensure_all_symbol(good_values))
        self.assertRaises(SifterError, ensure_all_symbol, bad_values)


#
# The end.
