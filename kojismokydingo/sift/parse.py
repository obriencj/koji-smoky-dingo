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


"""
Koji Smoky Dingo - Sifty Dingo Parser

This is the parser for the Sift Dingo filtering language.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import re

from abc import ABCMeta
from codecs import decode
from fnmatch import translate
from functools import partial
from itertools import chain, product
from six import add_metaclass, iteritems, itervalues
from six.moves import StringIO, map

from .. import BadDingo


__all__ = (
    "AllItems",
    "Glob",
    "Item",
    "ItemMatch",
    "ItemPath",
    "Matcher",
    "Null",
    "Number",
    "Reader",
    "Regex",
    "RegexError",
    "Symbol",
    "SymbolGroup",

    "convert_escapes",
    "convert_token",
    "parse_exprs",
)


class ParserError(BadDingo):
    complaint = "Error parsing Sifter"


class RegexError(ParserError):
    complaint = "Error compiling Regex"


@add_metaclass(ABCMeta)
class Matcher(object):
    """
    Base class for special comparison types
    """

    pass


class Null(Matcher):
    """
    An empty literal, represented by the symbols ``null`` or
    ``None``. Matches only with the python None value.
    """

    def __eq__(self, val):
        return val is None


    def __str__(self):
        return "null"


    def __repr__(self):
        return "Null()"


class Symbol(str, Matcher):
    """
    An unquoted literal series of characters. A symbol can compare
    with python str instances.
    """

    def __repr__(self):
        return "Symbol(%r)" % str(self)


class SymbolGroup(Matcher):
    """
    A symbol group is a literal symbol with multiple permutations. It is
    represented as a symbol containing groups within curly-braces

    Examples:

    * ``{foo,bar}-candidate`` is equal to foo-candidate and bar-candidate
    * ``foo-{1..3}`` is equal to any of foo-1, foo-2, foo-3
    """

    def __init__(self, src, groups):
        self.src = src
        self.groups = groups


    def __iter__(self):
        for k in map("".join, product(*self.groups)):
            if NUMBER_RE == k:
                yield Number(k)
            else:
                yield Symbol(k)


    def __eq__(self, val):
        return any(map(lambda s: s == val, self))


    def __repr__(self):
        return "SymbolGroup(%r)" % self.src


class Number(int, Matcher):
    """
    A number is a literal made entirely of digits. It can compare with
    both the python int and str types.
    """

    def __eq__(self, val):
        if isinstance(val, str):
            if NUMBER_RE == val:
                val = int(val)

        return int(self) == val


    def __repr__(self):
        return "Number(%i)" % self


class Regex(Matcher):
    """
    A regex is a quoted literal using forward-slashes as quotes

    Examples:

    * ``/.*foo$/`` is a case-sensitive match for text ending in foo
    * ``/.*foo$/i`` is a case-insensitive match for text ending in foo
    """

    def __init__(self, src, flags=None):
        self._src = src
        self._flagstr = flags

        fint = sum(getattr(re, c.upper(), 0) for c in flags) if flags else 0

        try:
            self._re = re.compile(src, fint)
        except re.error as exc:
            raise RegexError(str(exc))


    def __eq__(self, val):
        try:
            return bool(self._re.findall(val))
        except TypeError:
            return False


    def __str__(self):
        return self._src


    def __repr__(self):
        if self._flagstr:
            return "Regex(%r, flags=%r)" % (self._src, self._flagstr)
        else:
            return "Regex(%r)" % self._src


class Glob(Matcher):
    """
    A glob is a quoted literal using pipes as quotes

    Examples:

    * ``|*foo|`` is a case-sensitive match for text ending in foo
    * ``|*foo|i`` is a case-insensitive match for text ending in foo
    """

    def __init__(self, src, ignorecase=False):
        self._src = src
        self._ignorecase = ignorecase
        self._re = re.compile(translate(src), re.I if ignorecase else 0)


    def __eq__(self, val):
        try:
            return self._re.match(val) is not None
        except TypeError:
            return False


    def __str__(self):
        return self._src


    def __repr__(self):
        if self._ignorecase:
            return "Glob(%r, ignorecase=True)" % self._src
        else:
            return "Glob(%r)" % self._src


class Item(object):
    """
    Seeks path members by an int or str key.
    """

    def __init__(self, key):
        if isinstance(key, int):
            key = int(key)
        elif isinstance(key, str):
            key = str(key)

        self.key = key


    def get(self, d):
        key = self.key
        try:
            if isinstance(key, slice):
                for v in d[key]:
                    yield v
            else:
                yield d[key]

        except (IndexError, KeyError):
            # do not catch TypeError
            pass


    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.key)


class ItemMatch(Item):
    """
    Seeks path members by comparison of keys to a matcher (eg. a Glob
    or Regex)
    """

    def get(self, d):
        if isinstance(d, dict):
            data = iteritems(d)
        else:
            data = enumerate(d)

        key = self.key
        for k, v in data:
            if key == k:
                yield v


class AllItems(Item):
    """
    Seeks all path members
    """

    def __init__(self):
        pass


    def get(self, d):
        if isinstance(d, dict):
            return itervalues(d)
        else:
            return iter(d)


    def __repr__(self):
        return "AllItems()"


class ItemPath(object):
    """
    Represents a collection of elements inside a nested tree of lists
    and dicts
    """

    def __init__(self, *paths):
        self.paths = list(paths)

        for i, p in enumerate(paths):
            if isinstance(p, Item):
                continue
            elif isinstance(p, (str, int, slice)):
                self.paths[i] = Item(p)
            elif isinstance(p, Matcher):
                self.paths[i] = ItemMatch(p)
            else:
                msg = "Unexpected path element in ItemPath: %r" % p
                raise ParserError(msg)


    def get(self, data):
        work = [data]
        for element in self.paths:
            work = chain(*map(element.get, filter(None, work)))
        return work


    def __repr__(self):
        return "ItemPath(%s)" % ", ".join(map(str, self.paths))


class Reader(StringIO):

    def __init__(self, source):
        # overridden to mandate a source for read-mode. But we cannot
        # use super due to our py2 support, where StringIO is an
        # old-style class.
        StringIO.__init__(self, source)


    def peek(self, count=1):
        where = self.tell()
        val = self.read(count)
        self.seek(where)
        return val


def split_symbol_groups(reader):
    """
    Invoked to by convert_token to split up a symbol into a series of
    groups which can then be combined to form a SymbolGroup.
    """

    if isinstance(reader, str):
        reader = Reader(reader)

    token = None
    esc = False

    srciter = iter(partial(reader.read, 1), '')
    for c in srciter:
        if esc:
            esc = False
            if not token:
                token = StringIO()
            token.write(c)
            continue

        elif c == '\\':
            esc = True
            continue

        elif c == '{':
            if token:
                yield [token.getvalue()]
                token = None
            yield convert_group(parse_quoted(reader, '}'))
            continue

        else:
            if not token:
                token = StringIO()
            token.write(c)
            continue

    if token:
        yield [token.getvalue()]
        token = None


def _trailing_esc(val):
    # a count of trailing escapes, just to figure out if there's an
    # odd or even amount (and hence whether there's an unterminated
    # escape at the end
    return len(val) - len(val.rstrip("\\"))


def convert_group(grp):
    if "," not in grp:
        if ".." in grp:
            return list(convert_range(grp))
        else:
            return ["".join(("{", grp, "}"))]

    work = []
    for brk in grp.split(","):
        if work and _trailing_esc(work[-1][-1]) & 1:
            work[-1] = ",".join((work[-1][:-1], brk))
        else:
            work.append(brk)

    if len(work) == 1:
        return ["".join(("{", work[0], "}"))]
    else:
        return work


def convert_range(rng):
    broken = rng.split("..")
    blen = len(broken)

    if blen == 2:
        start, stop = broken
        step = 1
    elif blen == 3:
        start, stop, step = broken
    else:
        return ["".join(("{", rng, "}"))]

    try:
        istart = int(start)
        istop = int(stop) + 1
        istep = int(step)
    except ValueError:
        return ["".join(("{", rng, "}"))]

    sss = (start, stop)
    if any(map(lambda v: len(v) > 1 and v.startswith("0"), sss)):
        pad_to = max(map(len, sss))
        fmt = "{0:0%id}" % pad_to
    else:
        fmt = "{0:d}"

    return map(fmt.format, range(istart, istop, istep))


def parse_exprs(reader, start=None, stop=None):
    """
    Simple s-expr parser. Reads from a string or character iterator,
    emits expressions as nested lists.
    """

    # I've been re-using this code for over a decade. It was
    # originally in a command-line tool I wrote named 'deli' which
    # worked with del.icio.us for finding and filtering through my
    # bookmarks. Then I used it in Spexy and a form of it is the basis
    # for Sibilant's parser as well. And now it lives here, in Koji
    # Smoky Dingo.

    if isinstance(reader, str):
        reader = Reader(reader)

    if not (start and stop):
        unterminated = True
        start, stop = '()'
    else:
        unterminated = False

    token_breaks = "".join((start, stop, ' [;#|/\"\'\n\r\t'))

    token = None
    esc = False

    srciter = iter(partial(reader.read, 1), '')
    for c in srciter:
        if esc:
            if not token:
                token = StringIO()
            if c not in token_breaks:
                token.write(esc)
            token.write(c)
            esc = False
            continue

        if c == '\\':
            esc = c
            continue

        elif c == '.' and token is None:
            yield parse_itempath(reader, None, c)
            continue

        elif c == '[':
            prefix = None
            if token:
                prefix = token.getvalue()
                token = None
            yield parse_itempath(reader, prefix, c)
            continue

        elif c in token_breaks:
            if token:
                yield convert_token(token.getvalue())
                token = None

        else:
            if not token:
                token = StringIO()
            token.write(c)
            continue

        # c is in token_breaks
        if c in ';#':
            # comments run to end of line
            reader.readline()

        elif c == start:
            yield list(parse_exprs(reader, start, stop))

        elif c == stop:
            if unterminated:
                raise ParserError("Unexpected closing %r" % c)
            else:
                return

        elif c in '\'\"/|':
            yield parse_quoted(reader, c)

    if unterminated:
        # leftovers are therefore allowed
        if token:
            yield convert_token(token.getvalue())
    else:
        # we shouldn't have reached this
        raise ParserError("Unexpected EOF, missing closing %r" % stop)


ESCAPE_SEQUENCE_RE = re.compile(r'''
(\\U........
| \\u....
| \\x..
| \\[0-7]{1,3}
| \\N\{[^}]+\}
| \\[\\'"abfnrtv]
)''', re.UNICODE | re.VERBOSE)


def convert_escapes(val):
    """
    Decodes common escape sequences embedded in a str

    :rtype: str
    """

    def descape(m):
        return decode(m.group(0), 'unicode-escape')
    return ESCAPE_SEQUENCE_RE.sub(descape, val)


NUMBER_RE = Regex(r"^-?\d+$")


def convert_token(val):
    """
    Converts unquoted values to a Matcher instance.

    * An all-digit value will become Number
    * None, null, nil become a Null
    * Use of {} may become a SymbolGroup or Symbol
    * Everything else becomes a Symbol.

    :param val: token value to be converted
    :type val: str

    :rtype: Matcher
    """

    if val in (None, "None", "null", "nil"):
        return Null()

    elif NUMBER_RE == val:
        return Number(val)

    else:
        val = convert_escapes(val)

        if "{" in val:
            grps = list(split_symbol_groups(val))
            if all(map(lambda v: len(v) == 1, grps)):
                # in cases where there's only one choice in all the
                # groups, then we can simply create a single Symbol
                # from those merged choices.
                val = "".join(str(g[0]) for g in grps)
                return Symbol(val)
            else:
                return SymbolGroup(val, grps)

        else:
            return Symbol(val)


def parse_itempath(reader, prefix=None, char=None):
    """
    Parses an ItemPath definition from the given reader.

    :rtype: ItemPath
    """

    if isinstance(reader, str):
        reader = Reader(reader)

    paths = []

    if prefix:
        paths.append(convert_token(prefix))

    if char == '[':
        paths.append(parse_index(reader, char))

    token_breaks = ' .[]();#|/\"\'\n\r\t'

    token = None
    esc = False

    srciter = iter(partial(reader.peek, 1), '')
    for c in srciter:
        if esc:
            if token is None:
                token = StringIO()
            if c not in token_breaks:
                token.write(esc)
            token.write(c)
            esc = False

        elif c == '\\':
            esc = c

        elif c in token_breaks:
            if token:
                paths.append(convert_token(token.getvalue()))
                token = None

            if c == "[":
                paths.append(parse_index(reader, reader.read(1)))
                continue
            elif c == "]":
                raise ParserError("Unexpected closer: %r" % reader.read(1))
            elif c == ".":
                pass
            else:
                break

        else:
            if token is None:
                token = StringIO()
            token.write(c)

        # actually consume the character from the reader
        reader.read(1)

    if token:
        paths.append(convert_token(token.getvalue()))
        token = None

    return ItemPath(*paths)


_slice_like = Regex(r"^("
                    r":|::|"
                    r"[+-]?\d*:|"
                    r":[+-]?\d*|"
                    r"[+-]?\d*:[+-]?\d*|"
                    r"[+-]?\d*:[+-]?\d*:[+-]?\d*"
                    r")$")


def convert_slice(val):
    """
    Converted a colon-separated string into a slice. Raises a TypeError
    if the elements do not convert cleanly to integers

    Examples:
    * val of ``1:`` results in ``slice(1, None, None)``
    * val of ``:1`` results in ``slice(None, 1, None)``
    * val of ``"1:2:3"`` results in ``slice(1, 2, 3)``

    :rtype: slice
    """

    vals = ((int(v) if v else None) for v in val.split(":"))
    return slice(*vals)


def parse_index(reader, start=None):
    """
    Parse an index portion of an ItemPath from the reader

    :rtype: AllItems or slice or Matcher
    """

    if isinstance(reader, str):
        reader = Reader(reader)

    if not start:
        start = reader.read(1)

    if not start:
        msg = "Unterminated item index, missing closing ']'"
        raise ParserError(msg)
    elif start != '[':
        msg = "Unknown item index start: %r" % start
        raise ParserError(msg)

    val = list(parse_exprs(reader, '[', ']'))
    lval = len(val)

    if lval == 0:
        return AllItems()

    elif lval == 1:
        val = val[0]
        if _slice_like == val:
            val = convert_slice(val)
        return val

    else:
        msg = "Too many arguments in item index: %r" % val
        raise ParserError(msg)


def parse_quoted(reader, quotec=None, advanced_escapes=True):
    """
    Helper function for parse_exprs, will parse quoted values and
    return the appropriate wrapper type depending on the quoting
    character.

    * ``"foo"`` is a str
    * ``/foo/`` is a Regex
    * ``|foo|`` is a Glob

    Symbols are generated in the parse_exprs function directly, as
    they are not quoted.

    It is expected that the first quoting character will have been
    read already from src prior to this function being invoked. If
    that is not the case, and the first quoting character is still in
    the src iterable, then a quotec of None can be used to indicate
    that it should be taken from the first character of the src.
    """

    if isinstance(reader, str):
        reader = Reader(reader)

    if not quotec:
        quotec = reader.read(1)
        if not quotec:
            msg = "Unterminated matcher: missing closing %r" % quotec
            raise ParserError(msg)

    token = StringIO()
    esc = False

    srciter = iter(partial(reader.read, 1), '')
    for c in srciter:
        if esc:
            if advanced_escapes and c != quotec:
                token.write(esc)
            token.write(c)
            esc = False
        elif c == quotec:
            break
        elif c == '\\':
            esc = c
        else:
            token.write(c)

    else:
        msg = "Unterminated matcher: missing closing %r" % quotec
        raise ParserError(msg)

    val = token.getvalue()
    if advanced_escapes:
        val = convert_escapes(val)

    if quotec == "/":
        flags = []
        while reader.peek(1) in "aiLmsux":
            flags.append(reader.read(1))

        val = Regex(val, "".join(flags))

    elif quotec == "|":
        flags = False
        if reader.peek(1) == 'i':
            reader.read(1)
            flags = True
        val = Glob(val, ignorecase=flags)

    return val


#
# The end.
