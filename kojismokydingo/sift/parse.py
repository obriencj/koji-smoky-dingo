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
from io import StringIO
from itertools import chain, product
from typing import Iterable, Iterator, List, Sequence, Sized, Union, cast

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


class Matcher(metaclass=ABCMeta):
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
        return f"Symbol({str(self)!r})"


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
        return f"SymbolGroup({self.src!r})"


class FormattedSeries(Sequence[str]):
    """
    A portion of a `SymbolGroup` representing a repeatable formatted
    sequence.
    """

    def __init__(self, fmt: str, seq: Sequence):
        """
        :param fmt: formatting to apply

        :param seq: sequence which can safely have `iter` called on it
          multiple times
        """

        self._fmt = fmt
        self._seq = seq


    def __getitem__(self, index):
        return self._fmt.format(self._seq[index])


    def __iter__(self):
        return map(self._fmt.format, self._seq)


    def __len__(self):
        return len(self._seq)


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
        return f"Number({int(self)})"


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
            return f"Regex({self._src!r}, flags={self._flagstr!r})"
        else:
            return f"Regex({self._src!r})"


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
            return f"Glob({self._src!r}, ignorecase=True)"
        else:
            return f"Glob({self._src!r})"


class Item():
    """
    Seeks path members by an int or str key.
    """

    def __init__(self, key: Union[int, str, slice, Matcher]):
        if isinstance(key, int):
            key = int(key)
        elif isinstance(key, str):
            key = str(key)

        self.key = key


    def get(self, d: dict) -> Iterator:
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
        return f"{type(self).__name__}({self.key!r})"


class ItemMatch(Item):
    """
    Seeks path members by comparison of keys to a matcher (eg. a `Glob`
    or `Regex`)
    """

    def get(self, d: dict) -> Iterator:
        if isinstance(d, dict):
            data = d.items()
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


    def get(self, d: dict) -> Iterator:
        if isinstance(d, dict):
            return iter(d.values())
        else:
            return iter(d)


    def __repr__(self):
        return "AllItems()"


ItemPathSpec = Union[Item, Matcher, str, int, slice]


class ItemPath():
    """
    Represents a collection of elements inside a nested tree of lists
    and dicts
    """

    def __init__(self, *paths: ItemPathSpec):
        ipaths: List[Item] = []
        self.paths = ipaths

        for p in paths:
            if isinstance(p, Item):
                ipaths.append(p)
            elif isinstance(p, (str, int, slice)):
                ipaths.append(Item(p))
            elif isinstance(p, Matcher):
                ipaths.append(ItemMatch(p))
            else:
                msg = f"Unexpected path element in ItemPath: {p!r}"
                raise ParserError(msg)


    def get(self, data: dict) -> Iterator:
        work = iter([data])
        for element in self.paths:
            work = chain(*map(element.get, filter(None, work)))
        return work


    def __repr__(self):
        paths = ", ".join(map(str, self.paths))
        return f"ItemPath({paths})"


class Reader(StringIO):

    def __init__(self, source: str):
        # force it to be readonly
        super().__init__(source)


    def peek(self, count: int = 1) -> str:
        where = self.tell()
        val = self.read(count)
        self.seek(where)
        return val


def split_symbol_groups(
        source: str) -> Iterator[Sequence[str]]:
    """
    Invoked to by `convert_token` to split up a symbol into a series
    of groups which can then be combined to form a SymbolGroup.
    """

    reader = Reader(source)
    token: StringIO = None
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
            yield convert_group(cast(str, parse_quoted(reader, '}')))
            continue

        else:
            if not token:
                token = StringIO()
            token.write(c)
            continue

    if token:
        yield [token.getvalue()]
        token = None


def _trailing_esc(
        val: str) -> int:
    # a count of trailing escapes, just to figure out if there's an
    # odd or even amount (and hence whether there's an unterminated
    # escape at the end
    return len(val) - len(val.rstrip("\\"))


def convert_group(
        grp: str) -> Union[FormattedSeries, List[str]]:
    """
    A helper function for `split_symbol_groups`

    :param grp: group eg. ``"1,2,3"`` or range specifier eg. ``"1..3"``
    """

    if "," not in grp:
        if ".." in grp:
            return convert_range(grp)
        else:
            return [f"{{{grp}}}"]

    work: List[str] = []
    for brk in grp.split(","):
        if work and work[-1] and _trailing_esc(work[-1][-1]) & 1:
            work[-1] = ",".join((work[-1][:-1], brk))
        else:
            work.append(brk)

    if len(work) == 1:
        return [f"{{{work[0]}}}"]
    else:
        return work


def convert_range(rng: str) -> Union[FormattedSeries, List[str]]:
    """
    A helper function for `convert_group` to work with the group range
    notation.

    range notation can be specified as ``START..STOP`` or as
    ``START..STOP..STEP``. note that any zero-prefix padding is honored,
    and padding will be applied to values that

    produces a `FormattedSeries` built on a range instance

    if the range specifier is invalid, then returns a list with the
    specifier as the only value

    :param rng: range specifier, eg ``"1..3"``
    """

    broken: List[str] = rng.split("..")
    blen = len(broken)

    if blen == 2:
        start, stop = broken
        step: Union[int, str] = 1
    elif blen == 3:
        start, stop, step = broken
    else:
        return [f"{{{rng}}}"]

    try:
        istart = int(start)
        istop = int(stop) + 1
        istep = int(step)
    except ValueError:
        return [f"{{{rng}}}"]

    sss = (start, stop)
    if any(map(lambda v: len(v) > 1 and v.startswith("0"), sss)):
        pad_to = max(map(len, sss))
        fmt = f"{{0:0{pad_to}d}}"
    else:
        fmt = "{0:d}"

    return FormattedSeries(fmt, range(istart, istop, istep))


def parse_exprs(
        reader: Reader,
        start: str = None,
        stop: str = None) -> Iterator:
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

    if not (start and stop):
        unterminated = True
        start = '('
        stop = ')'
    else:
        unterminated = False

    # bandit thinks this is a password, haha
    token_breaks = f"{start}{stop} [;#|/\"\'\n\r\t"  # nosec

    token: StringIO = None
    esc: str = None

    srciter = iter(partial(reader.read, 1), '')
    for c in srciter:
        if esc:
            if not token:
                token = StringIO()
            if c not in token_breaks:
                token.write(esc)
            token.write(c)
            esc = None
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

        # if we get this far, then c is in token_breaks

        if c in ';#':
            # comments run to end of line
            reader.readline()

        elif c == start:
            yield list(parse_exprs(reader, start, stop))

        elif c == stop:
            if unterminated:
                raise ParserError(f"Unexpected closing {c!r}")
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
        raise ParserError(f"Unexpected EOF, missing closing {stop!r}")


ESCAPE_SEQUENCE_RE = re.compile(r'''
(\\U........
| \\u....
| \\x..
| \\[0-7]{1,3}
| \\N\{[^}]+\}
| \\[\\'"abfnrtv]
)''', re.UNICODE | re.VERBOSE)


def convert_escapes(val: str) -> str:
    """
    Decodes common escape sequences embedded in a str

    :param val: source str to decode
    """

    def descape(m):
        return decode(m.group(0), 'unicode-escape')
    return ESCAPE_SEQUENCE_RE.sub(descape, val)


NUMBER_RE = Regex(r"^-?\d+$")


def convert_token(val: str) -> Union[Matcher, str, bool]:
    """
    Converts unquoted values to a `Matcher` instance.

    * An all-digit value will become `Number`
    * None, null, nil become a `Null`
    * True becomes the boolean `True`
    * False becomes the boolean `False`
    * Use of ``{}`` may become a `SymbolGroup` or `Symbol`
    * Everything else becomes a `Symbol`

    :param val: token value to be converted
    """

    if val in (None, "None", "null", "nil"):
        return Null()

    elif val is True or val == "True":
        # note, we do not use 'in' because 1 would match as True
        return True

    elif val is False or val == "False":
        # note, we do not use 'in' because 0 would match as False
        return False

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


def parse_itempath(
        reader: Reader,
        prefix: str = None,
        char: str = None) -> ItemPath:
    """
    Parses an `ItemPath` definition from the given reader.

    :param reader: source reader to parse from

    :param prefix: an initial path token to convert as the start of the
      path

    :param char: the initiating character that has already been read from
      the reader, if any
    """

    paths: List[ItemPathSpec] = []

    if prefix:
        paths.append(convert_token(prefix))

    if char == '[':
        paths.append(parse_index(reader, char))

    # bandit thinks this is a password, haha
    token_breaks = ' .[]();#|/\"\'\n\r\t'  # nosec

    token: StringIO = None
    esc: str = None

    srciter = iter(partial(reader.peek, 1), '')
    for c in srciter:
        if esc:
            if token is None:
                token = StringIO()
            if c not in token_breaks:
                token.write(esc)
            token.write(c)
            esc = None

        elif c == '\\':
            esc = c

        elif c in token_breaks:
            if token:
                paths.append(convert_token(token.getvalue()))
                token = None

            if c == "[":
                c = reader.read(1)
                paths.append(parse_index(reader, c))
                continue
            elif c == "]":
                c = reader.read(1)
                raise ParserError(f"Unexpected closer: {c!r}")
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


def convert_slice(val: str) -> slice:
    """
    Converted a colon-separated string into a slice. Raises a TypeError
    if the elements do not convert cleanly to integers

    Examples:
    * val of ``1:`` results in ``slice(1, None, None)``
    * val of ``:1`` results in ``slice(None, 1, None)``
    * val of ``"1:2:3"`` results in ``slice(1, 2, 3)``
    """

    vals = [(int(v) if v else None) for v in val.split(":")]
    return slice(*vals)


def parse_index(
        reader: Reader,
        start: str = None) -> ItemPathSpec:
    """
    Parse an index portion of an `ItemPath` from the reader
    """

    if not start:
        start = reader.read(1)

    if not start:
        msg = "Unterminated item index, missing closing ']'"
        raise ParserError(msg)
    elif start != '[':
        msg = f"Unknown item index start: {start!r}"
        raise ParserError(msg)

    val = list(parse_exprs(reader, '[', ']'))
    lval = len(val)

    if lval == 0:
        return AllItems()

    elif lval == 1:
        sval: str = val[0]
        if _slice_like == sval:
            return convert_slice(sval)
        else:
            return sval

    else:
        msg = f"Too many arguments in item index: {val!r}"
        raise ParserError(msg)


QuotedSpec = Union[Glob, Regex, str]


def parse_quoted(
        reader: Reader,
        quotec: str = None,
        advanced_escapes: bool = True) -> QuotedSpec:
    """
    Helper function for `parse_exprs`, will parse quoted values and
    return the appropriate wrapper type depending on the quoting
    character.

    * ``"foo"`` is a `str`
    * ``/foo/`` is a `Regex`
    * ``|foo|`` is a `Glob`

    Symbols are generated in the parse_exprs function directly, as
    they are not quoted.

    It is expected that the first quoting character will have been
    read already from src prior to this function being invoked. If
    that is not the case, and the first quoting character is still in
    the src iterable, then a quotec of None can be used to indicate
    that it should be taken from the first character of the src.

    :param reader: source to read from

    :param quotec: initiating quote character, or None if the first
      character should be read from the reader

    :param advanced_escapes: if True then the escaped character will
      be parsed for character escape sequences which will be replaced
      with their relevant unicode value. if False then escaped
      character will simply be inlined into the value
    """

    if not quotec:
        quotec = reader.read(1)
        if not quotec:
            msg = f"Unterminated matcher: missing closing {quotec!r}"
            raise ParserError(msg)

    token = StringIO()
    esc: str = None

    srciter = iter(partial(reader.read, 1), '')
    for c in srciter:
        if esc:
            if advanced_escapes and c != quotec:
                token.write(esc)
            token.write(c)
            esc = None
        elif c == quotec:
            break
        elif c == '\\':
            esc = c
        else:
            token.write(c)

    else:
        msg = f"Unterminated matcher: missing closing {quotec!r}"
        raise ParserError(msg)

    val = token.getvalue()
    if advanced_escapes:
        val = convert_escapes(val)

    if quotec == "/":
        flags = []
        # hard-coding the flags we support for regex
        while reader.peek(1) in "aiLmsux":
            flags.append(reader.read(1))

        return Regex(val, "".join(flags))

    elif quotec == "|":
        iflag = False
        # hard-coding that we only support a single flag for glob
        if reader.peek(1) == 'i':
            reader.read(1)
            iflag = True
        return Glob(val, ignorecase=iflag)

    else:
        # plain ol' string
        return val


#
# The end.
