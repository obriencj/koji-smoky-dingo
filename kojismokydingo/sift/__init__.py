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

This mini-language has nothing to do with Sifty, nor the Sieve email
filtering language. I just thought that Sifter and Sieve were good
names for something that filters stuff.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import re

from abc import ABCMeta, abstractmethod, abstractproperty
from codecs import decode
from collections import OrderedDict
from fnmatch import fnmatchcase
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
    "Regex",
    "RegexError",
    "Sifter",
    "SifterError",
    "Symbol",
    "VariadicSieve",

    "ensure_int",
    "ensure_int_or_str",
    "ensure_matcher",
    "ensure_matchers",
    "ensure_sieve",
    "ensure_sieves",
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
    pass


class Null(Matcher):

    def __eq__(self, val):
        return val is None


    def __str__(self):
        return "null"


    def __repr__(self):
        return "Null()"


class Symbol(str, Matcher):

    def __repr__(self):
        return "Symbol(%r)" % str(self)


class SymbolGroup(Matcher):

    def __init__(self, src, groups):
        self.src = src
        self.groups = groups


    def __iter__(self):
        for k in map("".join, product(*self.groups)):
            if k.isdigit():
                yield Number(k)
            else:
                yield Symbol(k)


    def __eq__(self, val):
        return any(map(lambda s: s == val, self))


    def __repr__(self):
        return "SymbolGroup(%r)" % self.src


class Number(int, Matcher):

    def __eq__(self, val):
        if isinstance(val, str):
            if val.isdigit():
                val = int(val)

        return int(self) == val


    def __repr__(self):
        return "Number(%i)" % self


class Regex(Matcher):

    def __init__(self, src):
        self._src = src
        self._re = re.compile(src)


    def __eq__(self, val):
        try:
            return bool(self._re.findall(val))
        except TypeError:
            return False


    def __str__(self):
        return self._src


    def __repr__(self):
        return "Regex(%r)" % self._src


class Glob(Matcher):

    def __init__(self, src):
        self._src = src


    def __eq__(self, val):
        try:
            return fnmatchcase(val, self._src,)
        except TypeError:
            return False


    def __str__(self):
        return self._src


    def __repr__(self):
        return "Glob(%r)" % self._src


class Item(object):

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


class ItemMatch(Item):

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

    def __init__(self):
        pass


    def get(self, d):
        if isinstance(d, dict):
            return itervalues(d)
        else:
            return iter(d)


class ItemPath(object):

    def __init__(self, paths):
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


def parse_symbol_groups(srciter):

    if isinstance(srciter, str):
        srciter = iter(srciter)

    token = None
    esc = False

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
            yield convert_group(parse_quoted(srciter, '}'))
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


def parse_exprs(srciter, start="(", stop=")"):
    """
    Simple s-expr parser. Reads from a string or character iterator,
    emits expressions as nested lists. Lenient about closing
    expressions.
    """

    # I've been re-using this code for over a decade. It was
    # originally in a command-line tool I wrote named 'deli' which
    # worked with del.icio.us for finding and filtering through my
    # bookmarks. Then I used it in Spexy and a form of it is the basis
    # for Sibilant's parser as well. And now it lives here, in Koji
    # Smoky Dingo.

    assert len(start) == 1
    assert len(stop) == 1

    if isinstance(srciter, str):
        srciter = iter(srciter)

    token_breaks = "".join((start, stop, ' [;#|/\"\'\n\r\t'))

    token = None
    esc = False

    for c in srciter:
        if esc:
            if not token:
                token = StringIO()
            if c not in token_breaks:
                token.write(esc)
            token.write(c)
            esc = False
            continue

        elif c == '\\':
            esc = c
            continue

        elif c == '.' and token is None:
            yield parse_itempath(srciter, '', c)

        elif c == '[':
            prefix = ""
            if token:
                prefix = token.getvalue()
                token = None
            yield parse_itempath(srciter, prefix, c)

        elif c in token_breaks:
            if token:
                yield convert_token(token.getvalue())
                token = None

        else:
            if not token:
                token = StringIO()
            token.write(c)

        if c in ';#':
            # comments run to end of line
            for c in srciter:
                if c in "\n\r":
                    break

        elif c == start:
            yield list(parse_exprs(srciter, start, stop))

        elif c == stop:
            return

        elif c in '\'\"/|':
            yield parse_quoted(srciter, c)

    if token:
        # we could make this raise an exception instead, but currently
        # let's just be permissive and implicitly close unterminated
        # lists
        yield convert_token(token.getvalue())


ESCAPE_SEQUENCE_RE = re.compile(r'''
(\\U........
| \\u....
| \\x..
| \\[0-7]{1,3}
| \\N\{[^}]+\}
| \\[\\'"abfnrtv]
)''', re.UNICODE | re.VERBOSE)


def convert_escapes(s):
    def descape(m):
        return decode(m.group(0), 'unicode-escape')
    return ESCAPE_SEQUENCE_RE.sub(descape, s)


def convert_token(val):
    """
    Converts unquoted values.
    All digit value become unsigned int. None, null, nil become a Null.
    Everything else becomes a Symbol
    """

    if val in (None, "None", "null", "nil"):
        return Null()

    elif val.isdigit():
        return Number(val)

    else:
        val = convert_escapes(val)

        if "{" in val:
            grps = list(parse_symbol_groups(val))
            if all(map(lambda v: len(v) == 1, grps)):
                val = "".join(g[0] for g in grps)
                return Symbol(val)
            else:
                return SymbolGroup(val, grps)

        else:
            return Symbol(val)


def parse_itempath(srciter, prefix=None, char=None):
    paths = []

    if prefix:
        paths.append(convert_token(prefix))

    if char == "[":
        paths.append(parse_index(srciter))

    token_breaks = ' .[]();#|/\"\'\n\r\t'

    token = None
    esc = False
    for c in srciter:
        if esc:
            if token is None:
                token = StringIO()
            if c not in token_breaks:
                token.write(esc)
            token.write(c)
            esc = False
            continue

        elif c == '\\':
            esc = c
            continue

        elif c in token_breaks:
            if token:
                paths.append(convert_token(token.getvalue()))
                token = None

            if c == "[":
                paths.append(parse_index(srciter))
            elif c == "]":
                msg = "Unexpected closer: %r" % c
                raise SifterError(msg)
            elif c == ".":
                pass
            else:
                break

        else:
            if token is None:
                token = StringIO()
            token.write(c)

    if token:
        paths.append(convert_token(token.getvalue()))
        token = None

    return ItemPath(paths)


_slice_like = Regex(r"^("
                    r":|::|"
                    r"[+-]?\d*:|"
                    r":[+-]?\d*|"
                    r"[+-]?\d*:[+-]?\d*|"
                    r"[+-]?\d*:[+-]?\d*:[+-]?\d*"
                    r")$")


def convert_slice(val):
    vals = ((int(v) if v else None) for v in val.split(":"))
    return slice(*vals)


def parse_index(srciter):
    val = list(parse_exprs(srciter, '[', ']'))
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


def parse_quoted(srciter, quotec='\"', advanced_escapes=True):
    """
    Helper function for parse_exprs, will parse quoted values and
    return the appropriate wrapper type depending on the quoting
    character.

    * ``"foo"`` is a str
    * ``/foo/`` is a Regex
    * ``|foo|`` is a Glob

    Symbols are generated in the parse_exprs function directly, as
    they are not quoted.
    """

    token = StringIO()
    esc = False

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
        try:
            val = Regex(val)
        except re.error as exc:
            raise RegexError(str(exc))

    elif quotec == "|":
        val = Glob(val)

    return val


def ensure_symbol(value, msg=None):
    """
    Checks that the value is a Symbol. If not, raises a SifterError.
    """

    if isinstance(value, Symbol):
        return value

    if not msg:
        msg = "Value must be a symbol"
    raise SifterError("%s: %r (type %s)" %
                      (msg, value, type(value).__name__))


def ensure_str(value, msg=None):
    """
    Checks that value is either a str or Symbol. If not, raises a
    SifterError.
    """

    if isinstance(value, (int, str)):
        return str(value)

    if not msg:
        msg = "Value must be a string"
    raise SifterError("%s: %r (type %s)" %
                      (msg, value, type(value).__name__))


def ensure_int(value, msg=None):
    if isinstance(value, int):
        return int(value)

    if not msg:
        msg = "Value must be an int"
    raise SifterError("%s: %r (type %s)" %
                      (msg, value, type(value).__name__))


def ensure_int_or_str(value, msg=None):
    """
    Checks that value is either a int, Number, str, or Symbol. If not,
    raises a SifterError.

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


def ensure_matcher(value, msg=None):
    """
    Checks that value is either a str, or a Matcher instance. If not,
    raises a SifterError.
    """

    if isinstance(value, (str, Matcher, text_type)):
        return value

    if not msg:
        msg = "Value must be a string, regex, or glob"
    raise SifterError("%s: %r (type %s)" %
                      (msg, value, type(value).__name__))


def ensure_matchers(values, msg=None):
    """
    Checks that all of the elements in values are either a str,
    Symbol, Regex, or Glob instance.  If not, raises a SifterError.
    """

    return [ensure_matcher(v, msg) for v in values]


def ensure_sieve(value, msg=None):
    """
    Checks that value is a Sieve instance.  If not, raises a
    SifterError.
    """

    if isinstance(value, Sieve):
        return value

    if not msg:
        msg = "Value must be a sieve expression"
    raise SifterError("%s: %r (type %s)" %
                      (msg, value, type(value).__name__))


def ensure_sieves(values, msg=None):
    """
    Checks that all of the elements in values are Sieve instance.  If
    not, raises a SifterError.
    """

    return [ensure_sieve(v, msg) for v in values]


class Sifter(object):

    def __init__(self, sieves, source_str, key="id"):
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

        :param source_str: Sieve expressions

        :type source_str: str

        :param key: Unique hashable identifier key for the info
          dicts. This is used to deduplicate or otherwise correlate
          the incoming information. Default, use the "id" value.

        :type key: str, optional
        """

        if not callable(key):
            key = itemgetter(key)
        self.key = key

        # {flagname: set(data_id)}
        self._flags = {}

        # {(cachename, data_id): {}}
        self._cache = {}

        if not isinstance(sieves, dict):
            sieves = dict((sieve.name, sieve) for sieve in sieves)

        self._sieve_classes = sieves

        exprs = self._compile(source_str) if source_str else []
        self._exprs = ensure_sieves(exprs)


    def sieve_exprs(self):
        """
        The list of Sieve expressions in this Sifter
        """

        return self._exprs


    def _compile(self, source_str):
        """
        Turns a source string into a list of Sieve instances
        """

        return [self._convert(p) for p in parse_exprs(source_str)]


    def _convert_sym_aliases(self, sym):
        if sym == "!":
            # treat ! as an alias for not
            sym = Symbol("not")

        elif sym == "?":
            # tread ? as an alias for flagged
            sym = Symbol("flagged")

        return sym


    def _convert_sieve_aliases(self, sym, args):
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

            result = cls(self, *map(self._convert, args))

        else:
            result = parsed

        return result


    def run(self, session, info_dicts):
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
        work = tuple(info_dicts)
        return self.run(session, work) if work else {}


    def reset(self):
        """
        Clears data caches
        """

        self._cache.clear()


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


    def __init__(self, sifter, tokens=None):
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
        exprs = ensure_sieves(exprs)
        super(Logic, self).__init__(sifter, exprs)


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
        super(VariadicSieve, self).__init__(sifter)
        self.token = token


    def __repr__(self):
        return "".join(("(", self.name, " ", repr(self.token), ")"))


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

    name = "item"


    def __init__(self, sifter, path, *values):
        if not isinstance(path, ItemPath):
            path = ItemPath([path])

        values = ensure_matchers(values)
        super(ItemPathSieve, self).__init__(sifter, values)

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


DEFAULT_SIEVES = [
    Flagged, Flagger,
    ItemPathSieve,
    LogicAnd, LogicOr, LogicNot,
]


#
# The end.