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
Koji Smoky Dingo - Filtering Language Sifty Dingo

This is a mini-language based on S-Expressions used for filtering
sequences of dict data. The core language only supports some simple
logical constructs and a facility for setting and checking flags. The
language must be extended to add more predicates specific to the
schema of the data being filtered to become useful.

The Sifty Dingo mini-language has nothing to do with the Sifty
project, nor the Sieve email filtering language. I just thought that
Sifter and Sieve were good names for something that filters stuff.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import re

from abc import ABCMeta, abstractmethod, abstractproperty
from codecs import decode
from collections import OrderedDict
from fnmatch import translate
from functools import partial
from itertools import chain, product
from operator import itemgetter
from six import add_metaclass, iteritems, itervalues, text_type
from six.moves import StringIO, map

from .. import BadDingo


__all__ = (
    "DEFAULT_SIEVES",

    "AllItems",
    "Flagged",
    "Flagger",
    "Glob",
    "Item",
    "ItemMatch",
    "ItemPath",
    "ItemPathSieve",
    "ItemSieve",
    "Logic",
    "LogicAnd",
    "LogicNot",
    "LogicOr",
    "Null",
    "Reader",
    "Regex",
    "RegexError",
    "Sifter",
    "SifterError",
    "Symbol",
    "SymbolGroup",
    "VariadicSieve",

    "ensure_all_int_or_str",
    "ensure_all_matcher",
    "ensure_all_sieve",
    "ensure_all_symbol",
    "ensure_int",
    "ensure_int_or_str",
    "ensure_matcher",
    "ensure_sieve",
    "ensure_str",
    "ensure_symbol",

    "parse_exprs",
)


class SifterError(BadDingo):
    complaint = "Error compiling Sifter"


class RegexError(SifterError):
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
                raise SifterError(msg)


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
                raise SifterError("Unexpected closing %r" % c)
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
        raise SifterError("Unexpected EOF, missing closing %r" % stop)


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
                val = "".join(g[0] for g in grps)
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
                raise SifterError("Unexpected closer: %r" % reader.read(1))
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
        raise SifterError(msg)
    elif start != '[':
        msg = "Unknown item index start: %r" % start
        raise SifterError(msg)

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
        raise SifterError(msg)


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
            raise SifterError(msg)

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
        raise SifterError(msg)

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


def ensure_symbol(value, msg=None):
    """
    Checks that the value is a Symbol, and returns it. If value was
    not a Symbol, raises a SifterError.

    :rtype: Symbol
    """

    if isinstance(value, Symbol):
        return value

    if not msg:
        msg = "Value must be a symbol"

    raise SifterError("%s: %r (type %s)" %
                      (msg, value, type(value).__name__))


def ensure_all_symbol(values, msg=None):
    """
    Checks that all of the elements in values are Symbols, and returns
    them as a new list.  If not, raises a SifterError.

    :type values: list

    :rtype: list[Symbol]
    """

    return [ensure_symbol(val, msg) for val in values]


def ensure_str(value, msg=None):
    """
    Checks that value is either an int, str, or Symbol, and returns a
    str version of it. If value is not an int, str, or Symbol, raises
    a SifterError.

    :rtype: str
    """

    if isinstance(value, (int, str)):
        return str(value)

    if not msg:
        msg = "Value must be a string"

    raise SifterError("%s: %r (type %s)" %
                      (msg, value, type(value).__name__))


def ensure_int(value, msg=None):
    """
    Checks that valie is an int or Number, and returns it as an
    int. If value is not an int or Number, raises a SifterError.
    """

    if isinstance(value, int):
        return int(value)

    if not msg:
        msg = "Value must be an int"

    raise SifterError("%s: %r (type %s)" %
                      (msg, value, type(value).__name__))


def ensure_int_or_str(value, msg=None):
    """
    Checks that value is either a int, Number, str, or Symbol. Returns
    an int or str as appropriate. If value is not an int, Number, str,
    nor Symbol, raises a SifterError.

    :rtype: int or str
    """

    if isinstance(value, int):
        return int(value)
    elif isinstance(value, (str, text_type)):
        # Symbol is a subclass of str, so convert it back
        return str(value)

    if not msg:
        msg = "Value must be an int, Number, str, or Symbol"

    raise SifterError("%s: %r (type %s)" %
                      (msg, value, type(value).__name__))


def ensure_all_int_or_str(values, msg=None):
    """
    Checks that all values are either a int, Number, str, or Symbol.
    Returns each as an int or str as appropriate in a new list. If any
    value is not an int, Number, str, nor Symbol, raises a
    SifterError.

    :type values: list

    :rtype: list[int or str]
    """

    return [ensure_int_or_str(v, msg) for v in values]


def ensure_matcher(value, msg=None):
    """
    Checks that value is either a str, or a Matcher instance, and
    returns it. If not, raises a SifterError.

    :rtype: Matcher
    """

    if isinstance(value, (str, Matcher, text_type)):
        return value

    if not msg:
        msg = "Value must be a string, regex, or glob"

    raise SifterError("%s: %r (type %s)" %
                      (msg, value, type(value).__name__))


def ensure_all_matcher(values, msg=None):
    """
    Checks that all of the elements in values are either a str,
    Symbol, Regex, or Glob instance, and returns them as a new list.
    If not, raises a SifterError.

    :type values: list

    :rtype: list[Matcher]
    """

    return [ensure_matcher(v, msg) for v in values]


def ensure_sieve(value, msg=None):
    """
    Checks that value is a Sieve instance, and returns it.  If not,
    raises a SifterError.

    :rtype: Sieve
    """

    if isinstance(value, Sieve):
        return value

    if not msg:
        msg = "Value must be a sieve expression"

    raise SifterError("%s: %r (type %s)" %
                      (msg, value, type(value).__name__))


def ensure_all_sieve(values, msg=None):
    """
    Checks that all of the elements in values are Sieve instances, and
    returns them in a new list. If not, raises a SifterError.

    :type values: list

    :rtype: list[Sieve]
    """

    return [ensure_sieve(v, msg) for v in values]


class Sifter(object):

    def __init__(self, sieves, source, key="id", params=None):
        """
        A flagging data filter, compiled from an s-expression syntax.

        Sifter instances are callable, and when invoked with a session
        and a list of info dicts will perform filtering tests on the
        data to determine which items match the predicates from the
        source syntax.

        :param sieves: list of classes to use in compiling the source
          str. Each class should be a subclass of Sieve. The name
          attribute of each class is used as the lookup value when
          compiling a sieve expression

        :type sieves: list[type[Sieve]]

        :param source: Source from which to parse Sieve expressions

        :type source: stream or str

        :param key: Unique hashable identifier key for the info
          dicts. This is used to deduplicate or otherwise correlate
          the incoming information. Default, use the "id" value.

        :type key: str, optional

        :param params: Map of text substitutions for quoted strings

        :type params: dict[str, str], optional
        """

        if not callable(key):
            key = itemgetter(key)
        self.key = key

        self.params = params or {}

        # {flagname: set(data_id)}
        self._flags = {}

        # {(cachename, data_id): {}}
        self._cache = {}

        if not isinstance(sieves, dict):
            sieves = dict((sieve.name, sieve) for sieve in sieves)

        self._sieve_classes = sieves

        exprs = self._compile(source) if source else []
        self._exprs = ensure_all_sieve(exprs)


    def sieve_exprs(self):
        """
        The list of Sieve expressions in this Sifter
        """

        return self._exprs


    def _compile(self, source):
        """
        Turns a source string into a list of Sieve instances
        """

        return [self._convert(p) for p in parse_exprs(source)]


    def _convert_sym_aliases(self, sym):
        if sym == "!":
            # treat ! as an alias for not
            sym = Symbol("not")

        elif sym == "?":
            # tread ? as an alias for flagged
            sym = Symbol("flagged")

        return sym


    def _convert_sieve_aliases(self, sym, args):
        """
        When there is no sieve with a matchin name for sym, we check if it
        could be a convenience alias for some other forms.

        * (not-FOO ARGS...)  becomes  (not (FOO ARGS...))
        * (!FOO ARGS...)  becomes  (not (FOO ARGS...))
        * (BAR?)  becomes  (flagged BAR)

        :rtype: Symbol, tuple
        """

        if sym.startswith("not-"):
            # converts (not-foo 1) into (not (foo 1))
            subexpr = [Symbol(sym[4:])]
            subexpr.extend(args)
            return Symbol("not"), (subexpr,)

        elif sym.startswith("!"):
            # converts (!foo 1) into (not (foo 1))
            subexpr = [Symbol(sym[1:])]
            subexpr.extend(args)
            return Symbol("not"), (subexpr,)

        elif sym.endswith("?") and not args:
            # converts (bar?) into (flagged bar)
            return Symbol("flagged"), (Symbol(sym[:-1]),)

        else:
            return sym, args


    def _convert(self, parsed):
        """
        Takes the simple parse tree and turns it into a series of nested
        Sieve instances
        """

        if isinstance(parsed, list):
            if not parsed:
                raise SifterError("Empty expression: ()")

            if isinstance(parsed[0], ItemPath):
                name = Symbol("item")
                args = parsed

            else:
                name = ensure_symbol(parsed[0], "Sieve names must be symbols")
                name = self._convert_sym_aliases(name)
                args = parsed[1:]

            cls = self._sieve_classes.get(name)

            if cls is None:
                newname, args = self._convert_sieve_aliases(name, args)
                cls = self._sieve_classes.get(newname)

            if cls is None:
                raise SifterError("No such sieve: %s" % name)

            try:
                result = cls(self, *map(self._convert, args))
            except TypeError as te:
                msg = "Error creating Sieve %s: %s" % (name, te)
                raise SifterError(msg)

        elif isinstance(parsed, Symbol):
            if parsed.startswith("$") and parsed[1:] in self.params:
                result = convert_token(self.params[parsed[1:]])
                result = self._convert(result)
            else:
                result = parsed

        elif isinstance(parsed, str):
            if "{" in parsed:
                result = parsed.format(**self.params)
            else:
                result = parsed

        else:
            result = parsed

        return result


    def run(self, session, info_dicts):
        """
        Clears existing flags and runs contained sieves on the given
        info_dicts.

        :rtype: dict[str,list[dict]]
        """

        self._flags.clear()

        key = self.key
        data = OrderedDict((key(b), b) for b in info_dicts if b)
        work = tuple(itervalues(data))

        for expr in self._exprs:
            autoflag = not isinstance(expr, Flagger)
            for binfo in expr(session, work):
                if autoflag:
                    self.set_flag("default", binfo)

        results = {}
        for flag, bids in iteritems(self._flags):
            results[flag] = [data[bid] for bid in bids]

        return results


    def __call__(self, session, info_dicts):
        """
        Invokes run if there are any elements in info_dicts sequence. If
        there are not any elements, returns an empty dict.

        This bypassing of `run` would prevent the prep methods being
        invoked on any of the sieves.
        """

        work = tuple(info_dicts)
        return self.run(session, work) if work else {}


    def reset(self):
        """
        Clears flags and data caches
        """

        self._cache.clear()
        self._flags.clear()


    def is_flagged(self, flagname, data):
        """
        True if the data has been flagged with the given flagname, either
        via a ``(flag ...)`` sieve expression, or via `set_flag`
        """

        return ((flagname in self._flags) and
                (self.key(data) in self._flags[flagname]))


    def set_flag(self, flagname, data):
        """
        Records the given data as having been flagged with the given
        flagname.
        """

        bfl = self._flags.get(flagname)
        if bfl is None:
            # we want to preserve the order
            bfl = self._flags[flagname] = OrderedDict()

        bfl[self.key(data)] = True


    def get_cache(self, cachename, data):
        cachekey = (cachename, self.key(data))
        cch = self._cache.get(cachekey)
        if cch is None:
            cch = self._cache[cachekey] = OrderedDict()
        return cch


@add_metaclass(ABCMeta)
class Sieve(object):
    """
    The abstract base type for all Sieve expressions.

    A Sieve is a callable instance which is passed a session and a
    sequence of info dicts, and returns a filtered subset of those
    info dicts.

    The default ``run`` implementation will trigger the `prep` method
    first, and then use the `check` method on each info dict to
    determine whether it should be included in the results or not.
    Subclasses can therefore easily write just the check method.

    The prep method is there in the event that additional queries
    should be called on the whole set of incoming data (enabling
    multicall optimizations).

    Sieves are typically instanciated by a Sifter when it compiles the
    sieve expression string.

    Sieve subclasses must provide a ``name`` class property or
    attribute. This property is the key used to define how the Sieve
    is invoked by the source. For example, a source of
    ``(check-enabled X)`` is going to expect that the Sifter has a
    Sieve class available with a name of `"check-enabled"`
    """

    @abstractproperty
    def name(self):
        pass


    def __init__(self, sifter, *tokens):
        self.sifter = sifter
        self.key = sifter.key
        self.tokens = tokens


    def __call__(self, session, info_dicts):
        work = tuple(info_dicts)
        return tuple(self.run(session, work)) if work else work


    def __repr__(self):
        if self.tokens:
            e = " ".join(map(repr, self.tokens))
            return "".join(("(", self.name, " ", e, ")"))
        else:
            return "".join(("(", self.name, ")"))


    @abstractmethod
    def check(self, session, info):
        """
        Override to return True if the predicate matches the given
        info dict.

        This is used by the default `run` implementation in a filter.
        Only the info dicts which return True from this method will be
        included in the results.

        :param info: The info dict to be checked.
        :type info: dict

        :rtype: bool
        """

        pass


    def prep(self, session, info_dicts):
        """
        Override if some decoration of info_dicts is necessary. This
        allows bulk operations to be performed over the entire set of
        info dicts to be filtered, rather than one at a time in the
        `check` method

        :type info_dicts: list[dict]
        :rtype: None
        """

        pass


    def run(self, session, info_dicts):
        """
        Use this Sieve instance to select and return a subset of the
        info_dicts sequence.

        :type info_dicts: list[dict]
        :rtype: list[dict]
        """

        self.prep(session, info_dicts)
        return filter(partial(self.check, session), info_dicts)


    def get_cache(self, info):
        return self.sifter.get_cache(self.name, info)


@add_metaclass(ABCMeta)
class Logic(Sieve):

    check = None


    def __init__(self, sifter, *exprs):
        exprs = ensure_all_sieve(exprs)
        super(Logic, self).__init__(sifter, *exprs)


class LogicAnd(Logic):
    """
    Usage:  ``(and EXPR [EXPR...])``

    filters for info dicts which match all sub expressions.
    """

    name = "and"


    def run(self, session, info_dicts):
        work = info_dicts

        for expr in self.tokens:
            if not work:
                break
            work = expr(session, work)

        return work


class LogicOr(Logic):
    """
    Usage: ``(or EXPR [EXPR...])``

    filters for info dicts which match any of the sub expressions.
    """

    name = "or"


    def run(self, session, info_dicts):
        work = OrderedDict((self.key(b), b) for b in info_dicts)
        results = OrderedDict()

        for expr in self.tokens:
            if not work:
                break

            for b in expr(session, itervalues(work)):
                bid = self.key(b)
                del work[bid]
                results[bid] = b

        return itervalues(results)


class LogicNot(Logic):
    """
    Usage: ``(not EXPR [EXPR...])``

    filters for info dicts which match none of the sub expressions.
    """

    name = "not"


    def run(self, session, info_dicts):
        work = OrderedDict((self.key(b), b) for b in info_dicts)

        for expr in self.tokens:
            if not work:
                break

            for b in expr(session, itervalues(work)):
                del work[self.key(b)]

        return itervalues(work)


class Flagger(LogicAnd):
    """
    Usage: ``(flag NAME EXPR [EXPR...])``

    filters for info dicts which match all of the sub expressions, and
    marks them with the given named flag.
    """

    name = "flag"


    def __init__(self, sifter, flag, *exprs):
        super(Flagger, self).__init__(sifter, *exprs)
        self.flag = ensure_symbol(flag)


    def run(self, session, info_dicts):
        results = super(Flagger, self).run(session, info_dicts)

        for info in results:
            self.sifter.set_flag(self.flag, info)

        return results


    def __repr__(self):
        e = " ".join(map(repr, self.tokens))
        return "".join(("(", self.name, " ", repr(self.flag),
                        " " if e else "", e, ")"))


@add_metaclass(ABCMeta)
class VariadicSieve(Sieve):
    """
    Utility class which automatically applies an outer ``(or ...)`` when
    presented with more than one argument.

    This allows for example ``(name foo bar baz)`` to automatically
    become ``(or (name foo) (name bar) (name baz))`` while the
    ``name`` sieve only needs to be written to check for a single
    value.
    """

    def __new__(cls, sifter, *exprs):
        if len(exprs) > 1:
            wrapped = [cls(sifter, expr) for expr in exprs]
            return LogicOr(sifter, *wrapped)
        else:
            return object.__new__(cls)


    def __init__(self, sifter, token):
        super(VariadicSieve, self).__init__(sifter, token)
        self.token = token


class Flagged(VariadicSieve):
    """
    Usage: ``(flagged NAME [NAME...])``

    filters for info dicts which have been marked with any of the
    given named flags
    """

    name = "flagged"


    def __init__(self, sifter, name):
        super(Flagged, self).__init__(sifter, ensure_symbol(name))


    def check(self, _session, info):
        return self.sifter.is_flagged(self.token, info)


@add_metaclass(ABCMeta)
class ItemSieve(VariadicSieve):
    """
    A VariadicSieve which performs a comparison by fetching a named
    key from the info dict.

    Subclasses must provide a `field` attribute which will be used as
    a key to fetch a comparison value from any checked info dicts.

    If a pattern is specified, then the predicate matches if the info
    dict has an item by the given field key, and the value of that
    item matches the pattern.

    If a pattern is absent then this predicate will only check that
    given field key exists and is not None.
    """

    @abstractproperty
    def field(self):
        pass


    def __init__(self, sifter, pattern=None):
        if pattern is not None:
            pattern = ensure_matcher(pattern)
        super(ItemSieve, self).__init__(sifter, pattern)


    def check(self, session, info):
        if self.token is None:
            return info.get(self.field) is not None
        else:
            return ((self.field in info) and
                    (self.token == info[self.field]))


    def __repr__(self):
        if self.token is None:
            return "".join(("(", self.name, ")"))
        else:
            return "".join(("(", self.name, " ", repr(self.token), ")"))


class ItemPathSieve(Sieve):
    """
    usage: ``(item PATH [VALUE...])``

    Resolves the given PATH on each element and checks that any of the given
    values match. If any do, the element passes.
    """

    name = "item"


    def __init__(self, sifter, path, *values):
        if not isinstance(path, ItemPath):
            path = ItemPath(path)

        values = ensure_all_matcher(values)
        super(ItemPathSieve, self).__init__(sifter, *values)

        self.path = path


    def check(self, _session, data):
        work = self.path.get(data)

        if self.tokens:
            for pathv in work:
                for val in self.tokens:
                    if val == pathv:
                        return True
        else:
            for pathv in work:
                if pathv is not None:
                    return True

        return False


    def __repr__(self):
        toks = [self.name, str(self.path)]
        toks.extend(map(str, self.tokens))
        return "".join(("(", " ".join(toks), ")"))


DEFAULT_SIEVES = [
    Flagged, Flagger,
    ItemPathSieve,
    LogicAnd, LogicOr, LogicNot,
]


#
# The end.
