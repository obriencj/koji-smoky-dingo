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
    AllItems, Flagged, Glob,
    Item, ItemMatch, ItemPath, ItemPathSieve, ItemSieve,
    LogicNot, LogicOr, Null, Number,
    Regex, SifterError, Symbol, SymbolGroup,

    parse_exprs, parse_index, parse_itempath, parse_quoted,
)


class ParserTest(TestCase):

    def parse(self, src):
        return list(parse_exprs(src))


    def check_empty(self, src):
        res = self.parse(src)
        self.assertEqual(res, [])


    def test_empty(self):
        sources = [
            "",

            """
            """,

            """
            ; comment
            """,

            """
            # comment
            """,
        ]

        for src in sources:
            self.check_empty(src)


    def test_empty_list(self):

        src = """
        ()
        """
        res = self.parse(src)
        self.assertEqual(res, [[]])


    def test_unterminated_list(self):

        src = """
        (
        """
        self.assertRaises(SifterError, self.parse, src)

        src = """
        (hello
        """
        self.assertRaises(SifterError, self.parse, src)

        src = "(hello"
        self.assertRaises(SifterError, self.parse, src)

        src = "hello)"
        self.assertRaises(SifterError, self.parse, src)

        src = "foo bar"
        res = self.parse(src)
        self.assertEqual(res, [Symbol("foo"), Symbol("bar")])


    def check_null(self, src):
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Null)
        self.assertEqual(str(res[0]), "null")
        self.assertEqual(repr(res[0]), "Null()")


    def test_null(self):
        sources = [
            """
            None
            """,

            """
            null
            """,

            """
            nil
            """,
        ]

        for src in sources:
            self.check_null(src)


    def test_quoted(self):

        src = """
        "Hello"
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), str)
        self.assertEqual(str(res[0]), "Hello")
        self.assertEqual(repr(res[0]), "'Hello'")

        src = r"""
        "\"Hello\""
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), str)
        self.assertEqual(str(res[0]), "\"Hello\"")
        self.assertEqual(repr(res[0]), "'\"Hello\"'")

        src = """
        /World/
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Regex)
        self.assertEqual(str(res[0]), "World")
        self.assertEqual(repr(res[0]), "Regex('World')")

        src = r"""
        /Wor\/ld/
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Regex)
        self.assertEqual(str(res[0]), "Wor/ld")
        self.assertEqual(repr(res[0]), "Regex('Wor/ld')")

        src = """
        |How|
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Glob)
        self.assertEqual(str(res[0]), "How")
        self.assertEqual(repr(res[0]), "Glob('How')")

        src = """
        |How|i
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Glob)
        self.assertEqual(str(res[0]), "How")
        self.assertEqual(repr(res[0]), "Glob('How', ignorecase=True)")

        src = r"""
        |H\|o\|w|
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Glob)
        self.assertEqual(str(res[0]), "H|o|w")
        self.assertEqual(repr(res[0]), "Glob('H|o|w')")

        src = """
        "Hello"/World/|How|Goes
        """
        res = self.parse(src)
        self.assertEqual(len(res), 4)
        self.assertEqual(type(res[0]), str)
        self.assertEqual(str(res[0]), "Hello")
        self.assertEqual(type(res[1]), Regex)
        self.assertEqual(str(res[1]), "World")
        self.assertEqual(type(res[2]), Glob)
        self.assertEqual(str(res[2]), "How")
        self.assertEqual(type(res[3]), Symbol)
        self.assertEqual(str(res[3]), "Goes")


    def test_symbol(self):

        src = """
        Goes
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Symbol)
        self.assertEqual(str(res[0]), "Goes")
        self.assertEqual(repr(res[0]), "Symbol('Goes')")

        src = r"""
        G\|o\/e\"s
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Symbol)
        self.assertEqual(str(res[0]), "G|o/e\"s")
        self.assertEqual(repr(res[0]), "Symbol('G|o/e\"s')")

        src = r"""
        \\wut
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Symbol)
        self.assertEqual(str(res[0]), r"\wut")
        self.assertEqual(repr(res[0]), r"Symbol('\\wut')")

        src = r"""
        \wut
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Symbol)
        self.assertEqual(str(res[0]), r"\wut")
        self.assertEqual(repr(res[0]), r"Symbol('\\wut')")


    def test_symbol_group(self):

        src = """
        foo{1..5}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), SymbolGroup)
        self.assertEqual(repr(res[0]), "SymbolGroup('foo{1..5}')")
        self.assertEqual(res[0], "foo1")
        self.assertEqual(res[0], "foo2")
        self.assertEqual(res[0], "foo3")
        self.assertEqual(res[0], "foo4")
        self.assertEqual(res[0], "foo5")
        self.assertNotEqual(res[0], "foo0")
        self.assertNotEqual(res[0], "foo6")
        self.assertNotEqual(res[0], "foo")

        src = """
        foo{01..05}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), SymbolGroup)
        self.assertEqual(repr(res[0]), "SymbolGroup('foo{01..05}')")
        self.assertEqual(res[0], "foo01")
        self.assertEqual(res[0], "foo02")
        self.assertEqual(res[0], "foo03")
        self.assertEqual(res[0], "foo04")
        self.assertEqual(res[0], "foo05")
        self.assertNotEqual(res[0], "foo")
        self.assertNotEqual(res[0], "foo0")
        self.assertNotEqual(res[0], "foo1")
        self.assertNotEqual(res[0], "foo00")
        self.assertNotEqual(res[0], "foo06")

        src = """
        foo{01..05..2}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), SymbolGroup)
        self.assertEqual(repr(res[0]), "SymbolGroup('foo{01..05..2}')")
        self.assertEqual(res[0], "foo01")
        self.assertNotEqual(res[0], "foo02")
        self.assertEqual(res[0], "foo03")
        self.assertNotEqual(res[0], "foo04")
        self.assertEqual(res[0], "foo05")
        self.assertNotEqual(res[0], "foo")
        self.assertNotEqual(res[0], "foo0")
        self.assertNotEqual(res[0], "foo1")
        self.assertNotEqual(res[0], "foo00")
        self.assertNotEqual(res[0], "foo06")

        src = """
        hi{foo,bar}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), SymbolGroup)
        self.assertEqual(repr(res[0]), "SymbolGroup('hi{foo,bar}')")
        self.assertEqual(res[0], "hifoo")
        self.assertEqual(res[0], "hibar")
        self.assertNotEqual(res[0], "hibaz")
        self.assertNotEqual(res[0], "hi")
        self.assertNotEqual(res[0], "foo")
        self.assertNotEqual(res[0], "bar")

        src = """
        hi{foo,null,None,nil}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), SymbolGroup)
        self.assertEqual(repr(res[0]), "SymbolGroup('hi{foo,null,None,nil}')")
        self.assertEqual(res[0], "hifoo")
        self.assertEqual(res[0], "hiNone")

        src = """
        {foo,bar}_{01..05}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), SymbolGroup)
        self.assertEqual(repr(res[0]), "SymbolGroup('{foo,bar}_{01..05}')")
        self.assertEqual(res[0], "foo_03")
        self.assertEqual(res[0], "bar_04")
        self.assertNotEqual(res[0], "foo01")
        self.assertNotEqual(res[0], "bar01")

        src = r"""
        {foo,bar}\ {01..05}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), SymbolGroup)
        self.assertEqual(repr(res[0]), "SymbolGroup('{foo,bar} {01..05}')")
        self.assertEqual(res[0], "foo 03")
        self.assertEqual(res[0], "bar 04")
        self.assertNotEqual(res[0], "foo01")
        self.assertNotEqual(res[0], "bar01")


    def test_symbol_ungroup(self):

        src = r"""
        \{foo,bar}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Symbol)
        self.assertEqual(repr(res[0]), "Symbol('{foo,bar}')")

        src = r"""
        lo\{foo,bar}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Symbol)
        self.assertEqual(res[0], "lo{foo,bar}")
        self.assertNotEqual(res[0], "lofoo")
        self.assertNotEqual(res[0], "lobar")
        self.assertNotEqual(res[0], "lo")
        self.assertNotEqual(res[0], "foo")
        self.assertNotEqual(res[0], "bar")

        src = r"""
        lo{foo\,bar}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Symbol)
        self.assertEqual(res[0], "lo{foo,bar}")
        self.assertNotEqual(res[0], "lofoo")
        self.assertNotEqual(res[0], "lobar")
        self.assertNotEqual(res[0], "lo")
        self.assertNotEqual(res[0], "foo")
        self.assertNotEqual(res[0], "bar")

        src = r"""
        lo{foo}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Symbol)
        self.assertEqual(res[0], "lo{foo}")
        self.assertNotEqual(res[0], "lofoo")
        self.assertNotEqual(res[0], "lobar")
        self.assertNotEqual(res[0], "lo")
        self.assertNotEqual(res[0], "foo")
        self.assertNotEqual(res[0], "bar")

        src = """
        foo{1..}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Symbol)
        self.assertEqual(repr(res[0]), "Symbol('foo{1..}')")

        src = """
        foo{1..a}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Symbol)
        self.assertEqual(repr(res[0]), "Symbol('foo{1..a}')")

        src = """
        foo{1..1..}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Symbol)
        self.assertEqual(repr(res[0]), "Symbol('foo{1..1..}')")

        src = """
        foo{1..1..a}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Symbol)
        self.assertEqual(repr(res[0]), "Symbol('foo{1..1..a}')")

        src = """
        foo{1..1..1..1}
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), Symbol)
        self.assertEqual(repr(res[0]), "Symbol('foo{1..1..1..1}')")


    def test_item_path_dotted(self):
        src = """
        .foo
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(pth.paths[0].key, "foo")

        src = ".foo"
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(pth.paths[0].key, "foo")

        src = """
        .foo.bar
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 2)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(type(pth.paths[1]), Item)
        self.assertEqual(pth.paths[0].key, "foo")
        self.assertEqual(pth.paths[1].key, "bar")


    def test_item_path_all(self):
        src = """
        []
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), AllItems)

        src = """
        foo[]
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 2)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(type(pth.paths[1]), AllItems)
        self.assertEqual(pth.paths[0].key, "foo")

        src = """
        foo[]bar
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 3)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(type(pth.paths[1]), AllItems)
        self.assertEqual(type(pth.paths[2]), Item)
        self.assertEqual(pth.paths[0].key, "foo")
        self.assertEqual(pth.paths[2].key, "bar")

        src = """
        .foo[].bar
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 3)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(type(pth.paths[1]), AllItems)
        self.assertEqual(type(pth.paths[2]), Item)
        self.assertEqual(pth.paths[0].key, "foo")
        self.assertEqual(pth.paths[2].key, "bar")


    def test_item_path_slice(self):

        src = """
        [:]
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(pth.paths[0].key, slice(None))

        src = """
        [::]
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(pth.paths[0].key, slice(None))

        src = """
        [:-1]
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(pth.paths[0].key, slice(None, -1))

        src = """
        [1:2:-1]
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(pth.paths[0].key, slice(1, 2, -1))


    def test_item_path_index(self):
        src = """
        [foo]
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(type(pth.paths[0].key), str)
        self.assertEqual(pth.paths[0].key, "foo")

        src = """
        [9]
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(type(pth.paths[0].key), int)
        self.assertEqual(pth.paths[0].key, 9)

        src = r"""
        [wut\]]
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(type(pth.paths[0].key), str)
        self.assertEqual(pth.paths[0].key, "wut]")

        src = r"""
        [\[wut\]]
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(type(pth.paths[0].key), str)
        self.assertEqual(pth.paths[0].key, "[wut]")

        src = r"""
        .\n
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(type(pth.paths[0].key), str)
        self.assertEqual(pth.paths[0].key, "\n")

        src = r"""
        \n[]
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 2)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(type(pth.paths[0].key), str)
        self.assertEqual(pth.paths[0].key, "\n")

        src = """
        ["foo"]
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), Item)
        self.assertEqual(type(pth.paths[0].key), str)
        self.assertEqual(pth.paths[0].key, "foo")


    def test_item_path_match(self):
        src = """
        [{foo,bar}]
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), ItemMatch)
        self.assertEqual(type(pth.paths[0].key), SymbolGroup)
        self.assertEqual(pth.paths[0].key, "foo")
        self.assertEqual(pth.paths[0].key, "bar")

        src = """
        [|f*|]
        """
        res = self.parse(src)
        self.assertEqual(len(res), 1)
        self.assertEqual(type(res[0]), ItemPath)

        pth = res[0]
        self.assertEqual(len(pth.paths), 1)
        self.assertEqual(type(pth.paths[0]), ItemMatch)
        self.assertEqual(type(pth.paths[0].key), Glob)
        self.assertEqual(pth.paths[0].key, "foo")


    def test_item_path_err(self):

        src = """
        .foo]
        """
        self.assertRaises(SifterError, self.parse, src)

        src = """
        []]
        """
        self.assertRaises(SifterError, self.parse, src)

        src = """
        .foo[]]
        """
        self.assertRaises(SifterError, self.parse, src)

        src = """
        .foo[bar baz]
        """
        self.assertRaises(SifterError, self.parse, src)


    def test_bad_regex(self):

        src = """
        /[/
        """
        self.assertRaises(SifterError, self.parse, src)


class TestParseQuoted(TestCase):


    def test_str(self):

        val = parse_quoted('""', quotec=None)
        self.assertEqual("", val)

        val = parse_quoted('"foo"', quotec=None)
        self.assertEqual("foo", val)

        val = parse_quoted('foo"', quotec='"')
        self.assertEqual("foo", val)

        val = parse_quoted(r'foo\""', quotec='"')
        self.assertEqual('foo"', val)


    def test_err_str(self):
        self.assertRaises(SifterError, parse_quoted, '')
        self.assertRaises(SifterError, parse_quoted, '"foo')
        self.assertRaises(SifterError, parse_quoted, 'foo', quotec='"')


class TestParseIndex(TestCase):

    def test_parse_index(self):

        ix = parse_index("[]")
        self.assertTrue(isinstance(ix, AllItems))

        ix = parse_index("[1:]")
        self.assertTrue(isinstance(ix, slice))

        self.assertRaises(SifterError, parse_index, '')
        self.assertRaises(SifterError, parse_index, "[")
        self.assertRaises(SifterError, parse_index, "[1:")
        self.assertRaises(SifterError, parse_index, "]")


class TestParseItemPath(TestCase):

    def test_repr(self):

        ip = parse_itempath("foo")
        self.assertEqual(repr(ip), "ItemPath([Item('foo')])")

        ip = parse_itempath("[]")
        self.assertEqual(repr(ip), "ItemPath([AllItems()])")

        ip = parse_itempath("[1:]")
        self.assertEqual(repr(ip),
                         "ItemPath([Item(slice(1, None, None))])")

        ip = parse_itempath("[{foo,bar}]")
        self.assertEqual(repr(ip),
                         "ItemPath([ItemMatch(SymbolGroup('{foo,bar}'))])")


    def test_parse_item(self):

        ip = parse_itempath("foo")
        self.assertTrue(isinstance(ip, ItemPath))
        self.assertEqual(len(ip.paths), 1)
        self.assertEqual(type(ip.paths[0]), Item)
        self.assertEqual(ip.paths[0].key, Symbol("foo"))

        ip = parse_itempath(".foo")
        self.assertTrue(isinstance(ip, ItemPath))
        self.assertEqual(len(ip.paths), 1)
        self.assertEqual(type(ip.paths[0]), Item)
        self.assertEqual(ip.paths[0].key, Symbol("foo"))

        ip = parse_itempath("[foo]")
        self.assertTrue(isinstance(ip, ItemPath))
        self.assertEqual(len(ip.paths), 1)
        self.assertEqual(type(ip.paths[0]), Item)
        self.assertEqual(ip.paths[0].key, Symbol("foo"))

        ip = parse_itempath("[1:]")
        self.assertTrue(isinstance(ip, ItemPath))
        self.assertEqual(len(ip.paths), 1)
        self.assertEqual(type(ip.paths[0]), Item)
        self.assertEqual(ip.paths[0].key, slice(1, None, None))

        ip = parse_itempath("[:-1]")
        self.assertTrue(isinstance(ip, ItemPath))
        self.assertEqual(len(ip.paths), 1)
        self.assertEqual(type(ip.paths[0]), Item)
        self.assertEqual(ip.paths[0].key, slice(None, -1, None))

        ip = parse_itempath("[1:3]")
        self.assertTrue(isinstance(ip, ItemPath))
        self.assertEqual(len(ip.paths), 1)
        self.assertEqual(type(ip.paths[0]), Item)
        self.assertEqual(ip.paths[0].key, slice(1, 3, None))

        ip = parse_itempath("[1:3:2]")
        self.assertTrue(isinstance(ip, ItemPath))
        self.assertEqual(len(ip.paths), 1)
        self.assertEqual(type(ip.paths[0]), Item)
        self.assertEqual(ip.paths[0].key, slice(1, 3, 2))


    def test_parse_item_match(self):

        ip = parse_itempath(".{foo,bar}")
        self.assertTrue(isinstance(ip, ItemPath))
        self.assertEqual(len(ip.paths), 1)
        self.assertEqual(type(ip.paths[0]), ItemMatch)
        self.assertEqual(type(ip.paths[0].key), SymbolGroup)


    def test_err(self):
        self.assertRaises(SifterError, parse_itempath, ".foo[")
        self.assertRaises(SifterError, parse_itempath, ".foo]")
        self.assertRaises(SifterError, ItemPath, [None])


#
# The end.
