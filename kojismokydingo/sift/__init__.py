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
Koji Smoky Dingo - Sifter filtering

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import re

from abc import ABCMeta, abstractmethod, abstractproperty
from functools import partial
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


def parse_quoted(srciter, quotec='\"'):
    token = StringIO()
    esc = False

    for c in srciter:
        if not esc and c == quotec:
            break
        else:
            token.write(c)
            esc = (c == '\\') and (not esc)

    val = token.getvalue()

    if quotec == "/":
        return Regex(val)
    elif quotec == "|":
        return Glob(val)
    else:
        return val


def parse_exprs(srciter):
    if isinstance(srciter, str):
        srciter = iter(srciter)

    token = None

    for c in srciter:

        if c in ';#|/\"\'() \n\r\t':
            if token:
                yield Symbol(token.getvalue())
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
        yield Symbol(token.getvalue())


def ensure_symbol(value, msg=None):
    if isinstance(value, Symbol):
        return value
    else:
        if not msg:
            msg = "Value must be a symbol"
        raise SifterError("%s: %r (type %s)" %
                          (msg, value, type(value).__name__))


def ensure_str(value, msg=None):
    if isinstance(value, (str, Symbol)):
        return str(value)
    else:
        if not msg:
            msg = "Value must be a string"
        raise SifterError("%s: %r (type %s)" %
                          (msg, value, type(value).__name__))


def ensure_int_or_str(value, msg=None):
    if isinstance(value, (str, Symbol)):
        if value.isdigit():
            return int(value)
        else:
            return value
    else:
        if not msg:
            msg = "Value must be an int or string"
        raise SifterError("%s: %r (type %s)" %
                          (msg, value, type(value).__name__))


def ensure_matcher(value, msg=None):
    if isinstance(value, (str, Symbol, Regex, Glob)):
        return value
    else:
        if not msg:
            msg = "Value must be a string, regex, or glob"
        raise SifterError("%s: %r (type %s)" %
                          (msg, value, type(value).__name__))


def ensure_matchers(values, msg=None):
    return [ensure_matcher(v, msg) for v in values]


def ensure_sieve(value, msg=None):
    if isinstance(value, Sieve):
        return value
    else:
        if not msg:
            msg = "Value must be a sieve expression"
        raise SifterError("%s: %r (type %s)" %
                          (msg, value, type(value).__name__))


def ensure_sieves(values, msg=None):
    return [ensure_sieve(v, msg) for v in values]


class Sifter(object):

    def __init__(self, sieves, source_str, id_key="id"):
        """
        :type predicates: list[type[SiftPredicate]]
        """

        self.key = id_key

        # {flagname: set(data_id)}
        self._flags = {}

        # {data_id: set(flagname)}
        self._data_flags = {}


        if not isinstance(sieves, dict):
            sieves = dict((sieve.name, sieve) for sieve in sieves)

        self._sieve_classes = sieves
        self._exprs = self._compile(source_str) if source_str else []


    def sieve_exprs(self):
        return self._exprs


    def _compile(self, source_str):
        return [self._convert(p) for p in parse_exprs(source_str)]


    def _convert(self, parsed):
        if isinstance(parsed, list):
            name = ensure_symbol(parsed[0], "Sieve names must be symbols")

            cls = self._sieve_classes.get(name)
            if cls is None:
                raise SifterError("No such sieve: %s" % name)

            return cls(self, *map(self._convert, parsed[1:]))

        else:
            return parsed


    def __call__(self, session, info_dicts):

        id_key = self.key
        data = dict((b[id_key], b) for b in info_dicts)

        for expr in self._exprs:
            if isinstance(expr, Flagger):
                flagname = expr.flag
            else:
                flagname = "default"

            flgd = self.flagged(flagname)

            for binfo in expr(session, itervalues(data)):
                bid = binfo[id_key]

                flgd.add(bid)
                self.data_flags(bid).add(flagname)

        results = {}
        for flag, bids in iteritems(self._flags):
            results[flag] = [data[bid] for bid in bids]

        return results


    def flagged(self, flagname):
        """
        The set of data IDs associated with the given flag name

        :rtype: set(int)
        """

        bfl = self._flags.get(flagname)
        if bfl is None:
            bfl = self._flags[flagname] = set()
        return bfl


    def data_flags(self, data_id):
        """
        The set of flag names associated with the given data ID

        :rtype: set(str)
        """

        bfl = self._data_flags.get(data_id)
        if bfl is None:
            bfl = self._data_flags[data_id] = set()
        return bfl


@add_metaclass(ABCMeta)
class Sieve(object):

    @abstractproperty
    def name(self):
        pass


    def __init__(self, sifter):
        self.sifter = sifter


    @abstractmethod
    def check(self, session, binfo):
        """
        Override to return True if the predicate matches the given
        info dict.
        """
        pass


    def prep(self, session, info_dicts):
        """
        Override if some decoration of info_dicts is necessary. This
        allows bulk operations to be performed over the entire set of
        info dicts to be filtered, rather than one at a time in the
        `check` method
        """
        pass


    def __call__(self, session, info_dicts):
        """
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

    name = "and"

    def __call__(self, session, info_dicts):
        work = info_dicts
        for expr in self._exprs:
            work = expr(session, work)
        return work


class LogicOr(Logic):

    name = "or"

    def __call__(self, session, info_dicts):
        id_key = self.sifter.key
        work = dict((b[id_key], b) for b in info_dicts)
        results = {}

        for expr in self._exprs:
            if not work:
                break

            for b in expr(session, list(itervalues(work))):
                bid = b[id_key]
                del work[bid]
                results[bid] = b

        return list(itervalues(results))


class LogicNot(Logic):

    name = "not"

    def __call__(self, session, info_dicts):
        id_key = self.sifter.key
        work = dict((b[id_key], b) for b in info_dicts)

        for expr in self._exprs:
            if not work:
                break
            for b in expr(session, list(itervalues(work))):
                del work[b[id_key]]

        return list(itervalues(work))


class Flagger(LogicAnd):

    name = "flag"

    def __init__(self, sifter, flag, expr, *exprs):
        super(Flagger, self).__init__(sifter, expr, *exprs)
        self.flag = ensure_str(flag)


class Flagged(Sieve):

    name = "flagged"

    def __init__(self, sifter, *names):
        super(Flagged, self).__init__(sifter)
        self._flags = set(ensure_str(n) for n in names)


    def check(self, session, binfo):
        id_key = self.sifter.key
        bflgs = self.sifter.data_flags(binfo[id_key])
        return not self._flags.isdisjoint(bflgs)


    def __repr__(self):
        return "".join(("(", self.name, " ".join(self._flags), ")"))


@add_metaclass(ABCMeta)
class VariadicSieve(Sieve):

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


@add_metaclass(ABCMeta)
class PropertySieve(VariadicSieve):

    @abstractproperty
    def field(self):
        pass


    def __init__(self, sifter, pattern):
        pattern = ensure_matcher(pattern)
        super(PropertySieve, self).__init__(sifter, pattern)


    def check(self, session, binfo):
        return self.token == binfo[self.field]


DEFAULT_SIEVES = [
    Flagged, Flagger,
    LogicAnd, LogicOr, LogicNot,
]


#
# The end.
