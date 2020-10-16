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
from collections import OrderedDict
from functools import partial
from operator import itemgetter
from six import add_metaclass, iteritems, itervalues
from six.moves import StringIO

from .. import BadDingo
from ..common import fnmatches


__all__ = (
    "DEFAULT_SIEVES",

    "Flagged",
    "Flagger",
    "Glob",
    "Logic",
    "LogicAnd",
    "LogicNot",
    "LogicOr",
    "Regex",
    "Sifter",
    "SifterError",
    "Symbol",

    "ensure_int_or_str",
    "ensure_matcher",
    "ensure_matchers",
    "ensure_sieve",
    "ensure_sieves",
    "ensure_str",
    "ensure_symbol",

    "parse_exprs",
    "parse_quoted",
)


class SifterError(BadDingo):
    complaint = "Error compiling Sifter"


class Null(object):
    def __repr__(self):
        return "null"

    def __eq__(self, val):
        return val is None


class Symbol(str):
    def __repr__(self):
        return "Symbol(%r)" % str(self)


class Regex(object):
    def __init__(self, src):
        self._src = src
        self._re = re.compile(src)

    def __eq__(self, val):
        return bool(self._re.findall(val))

    def __repr__(self):
        return "Regex(%r)" % self._src


class Glob(object):
    def __init__(self, src):
        self._glob = src

    def __eq__(self, val):
        return fnmatches(val, (self._glob,))

    def __repr__(self):
        return "Glob(%r)" % self._glob


def parse_exprs(srciter):
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

    if isinstance(srciter, str):
        srciter = iter(srciter)

    token = None

    for c in srciter:

        if c in ' ();#|/\"\'\n\r\t':
            if token:
                yield parse_token(token.getvalue())
                token = None
        else:
            if not token:
                token = StringIO()
            token.write(c)
            continue

        if c in ';#':
            # comments run to end of line
            for c in srciter:
                if c in "\n\r":
                    break

        elif c == '(':
            yield list(parse_exprs(srciter))

        elif c == ')':
            return

        elif c in '\'\"/|':
            yield parse_quoted(srciter, c)

    if token:
        # we could make this raise an exception instead, but currently
        # let's just be permissive and implicitly close unterminated
        # lists
        yield parse_token(token.getvalue())


def parse_token(val):
    """
    Converts unquoted values.
    All digit value become unsigned int. None, null, nil become a Null.
    Everything else becomes a Symbol
    """

    if val in (None, "None", "null", "nil"):
        return Null()

    elif val.isdigit():
        return int(val)

    else:
        return Symbol(val)


def parse_quoted(srciter, quotec='\"'):
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
            token.write(c)
            esc = False
        elif c == quotec:
            break
        elif c == '\\':
            esc = True
        else:
            token.write(c)
    else:
        msg = "Unterminated matcher: missing closing %r" % quotec
        raise SifterError(msg)

    val = token.getvalue()

    if quotec == "/":
        return Regex(val)
    elif quotec == "|":
        return Glob(val)
    else:
        return val


def ensure_symbol(value, msg=None):
    """
    Checks that the value is a Symbol. If not, raises a SifterError.
    """

    if isinstance(value, Symbol):
        return value
    else:
        if not msg:
            msg = "Value must be a symbol"
        raise SifterError("%s: %r (type %s)" %
                          (msg, value, type(value).__name__))


def ensure_str(value, msg=None):
    """
    Checks that value is either a str or Symbol. If not, raises a
    SifterError.
    """

    if isinstance(value, (str, Symbol)):
        return str(value)
    else:
        if not msg:
            msg = "Value must be a string"
        raise SifterError("%s: %r (type %s)" %
                          (msg, value, type(value).__name__))


def ensure_int_or_str(value, msg=None):
    """
    Checks that value is either a str or Symbol. If it is a Symbol,
    attempts to parse it as an unsigned integer. If not a str or
    Symbol, raises a SifterError.
    """

    if isinstance(value, (int, str)):
        return value

    elif isinstance(value, Symbol):
        if value.isdigit():
            return int(value)
        else:
            return value
    else:
        if not msg:
            msg = "Value must be an int, string, or symbol"
        raise SifterError("%s: %r (type %s)" %
                          (msg, value, type(value).__name__))


def ensure_matcher(value, msg=None):
    """
    Checks that value is either a str, Symbol, Regex, or Glob
    instance.  If not, raises a SifterError.
    """

    if isinstance(value, (str, Symbol, Regex, Glob, Null)):
        return value
    else:
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
    else:
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

        elif sym.startswith("!"):
            # treat !foo as an alias for not-foo
            sym = Symbol("not-" + sym[1:])

        return sym


    def _convert_sieve_aliases(self, sym, args):
        if sym.startswith("not-"):
            # converts (not-foo 1) into (not (foo 1))
            subexpr = [Symbol(sym[4:])]
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


    def __call__(self, session, info_dicts):

        data = dict((self.key(b), b) for b in info_dicts if b)

        for expr in self._exprs:
            autoflag = not isinstance(expr, Flagger)
            for binfo in expr(session, itervalues(data)):
                if autoflag:
                    self.set_flag("default", binfo)

        results = {}
        for flag, bids in iteritems(self._flags):
            results[flag] = [data[bid] for bid in bids]

        return results


    def reset_flags(self):
        self._flags = {}


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


@add_metaclass(ABCMeta)
class Sieve(object):
    """
    The abstract base type for all Sieve expressions.

    A Sieve is a callable instance which is passed a session and a
    sequence of info dicts, and returns a filtered subset of those
    info dicts.

    The default ``__call__`` implementation will trigger the `prep`
    method first, and then use the `check` method on each info dict to
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


    def __init__(self, sifter):
        self.sifter = sifter
        self.key = sifter.key


    @abstractmethod
    def check(self, session, info):
        """
        Override to return True if the predicate matches the given
        info dict.

        This is used by the default `__call__` implementation in a
        filter. Only the info dicts which return True from this method
        will be included in the results.

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


    def __call__(self, session, info_dicts):
        """
        Use this Sieve instance to select and return a subset of the
        info_dicts sequence.

        :type info_dicts: list[dict]
        :rtype: list[dict]
        """

        self.prep(session, info_dicts)
        return filter(partial(self.check, session), info_dicts)


    def __repr__(self):
        return "".join(("(", self.name, ")"))


@add_metaclass(ABCMeta)
class Logic(Sieve):

    check = None

    def __init__(self, sifter, *exprs):
        super(Logic, self).__init__(sifter)
        self._exprs = ensure_sieves(exprs)

    def __repr__(self):
        e = " ".join(map(repr, self._exprs))
        return "".join(("(", self.name, " " if e else "", e, ")"))


class LogicAnd(Logic):
    """
    Usage:  ``(and EXPR [EXPR...])``

    filters for info dicts which match all sub expressions.
    """

    name = "and"

    def __call__(self, session, info_dicts):
        work = info_dicts
        for expr in self._exprs:
            work = expr(session, work)
        return work


class LogicOr(Logic):
    """
    Usage: ``(or EXPR [EXPR...])``

    filters for info dicts which match any of the sub expressions.
    """

    name = "or"

    def __call__(self, session, info_dicts):
        work = dict((self.key(b), b) for b in info_dicts)
        results = {}

        for expr in self._exprs:
            if not work:
                break

            for b in expr(session, list(itervalues(work))):
                bid = self.key(b)
                del work[bid]
                results[bid] = b

        return list(itervalues(results))


class LogicNot(Logic):
    """
    Usage: ``(not EXPR [EXPR...])``

    filters for info dicts which match none of the sub expressions.
    """

    name = "not"

    def __call__(self, session, info_dicts):
        work = dict((self.key(b), b) for b in info_dicts)

        for expr in self._exprs:
            if not work:
                break

            for b in expr(session, list(itervalues(work))):
                del work[self.key(b)]

        return list(itervalues(work))


class Flagger(LogicAnd):
    """
    Usage: ``(flag NAME EXPR [EXPR...])``

    filters for info dicts which match all of the sub expressions, and
    marks them with the given named flag.
    """

    name = "flag"

    def __init__(self, sifter, flag, expr, *exprs):
        super(Flagger, self).__init__(sifter, expr, *exprs)
        self.flag = ensure_symbol(flag)


    def __call__(self, session, info_dicts):
        results = super(Flagger, self).__call__(session, info_dicts)

        for info in results:
            self.sifter.set_flag(self.flag, info)

        return results


    def __repr__(self):
        e = " ".join(map(repr, self._exprs))
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

    def __new__(cls, sifter, expr, *exprs):
        if exprs:
            wrapped = [cls(sifter, expr)]
            wrapped.extend(cls(sifter, expr) for expr in exprs)
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
class PropertySieve(VariadicSieve):
    """
    A VariadicSieve which performs a comparison by fetching a named
    key from the info dict.

    Subclasses must provide a `field` attribute which will be used as
    a key to fetch a comparison value from any checked info dicts.
    """

    @abstractproperty
    def field(self):
        pass


    def __init__(self, sifter, pattern=None):
        pattern = ensure_matcher(pattern)
        super(PropertySieve, self).__init__(sifter, pattern)


    def check(self, session, info):
        if self.token is None:
            return bool(info.get(self.field))
        else:
            return self.token == info.get(self.field)


    def __repr__(self):
        if self.token is None:
            return "".join(("(", self.name, ")"))
        else:
            return "".join(("(", self.name, " ", repr(self.token), ")"))


DEFAULT_SIEVES = [
    Flagged, Flagger,
    LogicAnd, LogicOr, LogicNot,
]


#
# The end.
