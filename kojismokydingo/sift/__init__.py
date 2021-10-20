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


from abc import ABCMeta, abstractproperty
from collections import OrderedDict
from functools import partial
from io import TextIOBase
from koji import ClientSession
from operator import itemgetter
from typing import (
    Any, Iterable, Callable, Dict, List, Sequence, Set,
    Tuple, Type, TypeVar, Union, )

from .. import BadDingo
from ..types import KeySpec
from .parse import (
    Glob, ItemPath, Matcher, Number, Reader, Regex, Symbol, SymbolGroup,
    convert_token, parse_exprs, )


__all__ = (
    "DEFAULT_SIEVES",

    "Flagged",
    "Flagger",
    "IntStrSieve",
    "ItemPathSieve",
    "ItemSieve",
    "Logic",
    "LogicAnd",
    "LogicNot",
    "LogicOr",
    "MatcherSieve",
    "Sieve",
    "Sifter",
    "SifterError",
    "SymbolSieve",
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
)


class SifterError(BadDingo):
    # Indicates an problem during the compilation of a Sifter, either
    # due to a syntactic problem or in the initialization of a Sieve
    # instance with incompatible parameter types.

    complaint = "Error compiling Sifter"


def ensure_symbol(
        value: Any,
        msg: str = None) -> Symbol:
    """
    Checks that the value is a Symbol, and returns it. If value was
    not a Symbol, raises a SifterError.
    """

    if isinstance(value, Symbol):
        return value

    if not msg:
        msg = "Value must be a symbol"

    raise SifterError(f"{msg}: {value!r}"
                      f" (type {type(value).__name__})")


def ensure_all_symbol(
        values: List[Any],
        expand: bool = True,
        msg: str = None) -> List[Symbol]:
    """
    Checks that all of the elements in values are Symbols, and returns
    them as a new list.  If not, raises a SifterError.

    If expand is True then any SymbolGroup instances will be expanded
    to their full combination of Symbols and inlined. Otherwise, the
    inclusion of a SymbolGroup is an error.

    :param expand: convert any SymbolGroups into their combinant
      Symbols
    """

    result: List[Symbol] = []

    for val in values:
        if isinstance(val, Symbol):
            result.append(val)

        elif expand and isinstance(val, SymbolGroup):
            result.extend(val)

        else:
            if not msg:
                msg = "Value must be a symbol"
            raise SifterError(f"{msg}: {val!r}"
                              f" (type {type(val).__name__})")

    return result


def ensure_str(
        value: Any,
        msg: str = None) -> str:
    """
    Checks that value is either an int, str, or Symbol, and returns a
    str version of it. If value is not an int, str, or Symbol, raises
    a SifterError.
    """

    if isinstance(value, (int, str)):
        return str(value)

    if not msg:
        msg = "Value must be a string"

    raise SifterError(f"{msg}: {value!r}"
                      f" (type {type(value).__name__})")


def ensure_int(
        value: Any,
        msg: str = None) -> int:
    """
    Checks that valie is an int or Number, and returns it as an
    int. If value is not an int or Number, raises a SifterError.
    """

    if isinstance(value, int):
        return int(value)

    if not msg:
        msg = "Value must be an int"

    raise SifterError(f"{msg}: {value!r}"
                      f" (type {type(value).__name__})")


def ensure_int_or_str(
        value: Any,
        msg: str = None) -> Union[int, str]:
    """
    Checks that value is either a int, Number, str, or Symbol. Returns
    an int or str as appropriate. If value is not an int, Number, str,
    nor Symbol, raises a SifterError.

    :param value: the value to coerce into an int or str

    :param msg: optional error message if value cannot be coerced
    """

    if isinstance(value, int):
        return int(value)
    elif isinstance(value, str):
        # Symbol is a subclass of str, so convert it back
        return str(value)

    if not msg:
        msg = "Value must be an int, Number, str, or Symbol"

    raise SifterError(f"{msg}: {value!r}"
                      f" (type {type(value).__name__})")


def ensure_all_int_or_str(
        values: Iterable[Any],
        msg: str = None) -> List[Union[int, str]]:
    """
    Checks that all values are either a int, Number, str, or Symbol.
    Returns each as an int or str as appropriate in a new list. If any
    value is not an int, Number, str, nor Symbol, raises a
    SifterError.

    :param values: sequence of values to ensure or convert

    :param msg: optional error message for exception raised if a portion
      of values could not be coerced to an int or str
    """

    return [ensure_int_or_str(v, msg) for v in values]


def ensure_matcher(
        value: Any,
        msg: str = None) -> Union[str, Matcher]:
    """
    Checks that value is either a str, or a Matcher instance, and
    returns it. If not, raises a SifterError.
    """

    if isinstance(value, (str, Matcher)):
        return value

    if not msg:
        msg = "Value must be a string, regex, or glob"

    raise SifterError(f"{msg}: {value!r}"
                      f" (type {type(value).__name__})")


def ensure_all_matcher(
        values: Iterable[Any],
        msg: str = None) -> List[Union[str, Matcher]]:
    """
    Checks that all of the elements in values are either a str,
    Symbol, Regex, or Glob instance, and returns them as a new list.
    If not, raises a SifterError.
    """

    return [ensure_matcher(v, msg) for v in values]


def ensure_sieve(
        value: Any,
        msg: str = None) -> 'Sieve':
    """
    Checks that value is a Sieve instance, and returns it.  If not,
    raises a SifterError.
    """

    if isinstance(value, Sieve):
        return value

    if not msg:
        msg = "Value must be a sieve expression"

    raise SifterError(f"{msg}: {value!r}"
                      f" (type {type(value).__name__})")


def ensure_all_sieve(
        values: Iterable[Any],
        msg: str = None) -> List['Sieve']:
    """
    Checks that all of the elements in values are Sieve instances, and
    returns them in a new list. If not, raises a SifterError.
    """

    return [ensure_sieve(v, msg) for v in values]


def gather_args(
        values: Iterable[str]) -> Tuple[list, dict]:
    """
    Converts list of values into an *args and **kwds pair for use in
    creating a Sieve instance.
    """

    missing = object()
    args = []
    kwds = {}

    ivals = iter(values)
    for val in ivals:
        if isinstance(val, Symbol) and val.endswith(":"):
            key = val.rstrip(":")
            val = next(ivals, missing)  # type: ignore
            if val is missing:
                msg = f"Missing value for keyword argument {key}"
                raise SifterError(msg)
            else:
                kwds[key] = val
        else:
            args.append(val)

    return args, kwds


ST = TypeVar('ST')


class Sifter():
    """
    A flagging data filter, compiled from an s-expression syntax.

    Sifter instances are callable, and when invoked with a session and
    a list of info dicts will perform filtering tests on the data to
    determine which items match the predicates from the source syntax.
    """

    def __init__(self,
                 sieves: Union[Dict[str, Type['Sieve']],
                               Iterable[Type['Sieve']]],
                 source: Union[str, Reader],
                 key: KeySpec = "id",
                 params: Dict[str, str] = None):
        """
        :param sieves: list of classes to use in compiling the source
          str. Each class should be a subclass of Sieve. The name
          attribute of each class is used as the lookup value when
          compiling a sieve expression

        :param source: Source from which to parse Sieve expressions

        :param key: Unique hashable identifier key for the info
          dicts. This is used to deduplicate or otherwise correlate
          the incoming information. Default, use the "id" value.

        :param params: Map of text substitutions for quoted strings
        """

        if not callable(key):
            key = itemgetter(key)
        self.key: Callable = key

        self.params: Dict[str, str] = params or {}

        # {flagname: {data_id: bool}}
        self._flags: Dict[str, Dict[Any, bool]] = {}

        # {(cachename, data_id): {}}
        self._cache: Dict[Tuple[str, Any], Any] = {}

        sievedict: Dict[str, Type[Sieve]]

        if not isinstance(sieves, dict):
            # convert a list of sieves into a dict mapping the sieve
            # names and their aliases to the classes
            sieves = tuple(sieves)
            sievedict = {sieve.name: sieve  # type: ignore
                         for sieve in sieves}
            for sieve in sieves:
                for alias in sieve.aliases:
                    sievedict[alias] = sieve
            sieves = sievedict

        self._sieve_classes: Dict[str, Type[Sieve]] = sieves

        exprs = self._compile(source) if source else []
        self._exprs = ensure_all_sieve(exprs)


    def sieve_exprs(self) -> List['Sieve']:
        """
        The list of Sieve expressions in this Sifter
        """

        return self._exprs


    def _compile(self, source: Union[Reader, str]):
        """
        Turns a source string into a list of Sieve instances
        """

        if isinstance(source, Reader):
            reader = source
        else:
            reader = Reader(str(source))

        return [self._convert(p) for p in parse_exprs(reader)]


    def _convert_sieve_aliases(
            self,
            sym: Symbol,
            args: Tuple) -> Tuple[Symbol, Tuple]:
        """
        When there is no sieve with a matchin name for sym, we check if it
        could be a convenience alias for some other forms.

        * (not-FOO ARGS...)  becomes  (not (FOO ARGS...))
        * (!FOO ARGS...)  becomes  (not (FOO ARGS...))
        * (BAR?)  becomes  (flagged BAR)
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
                # a shortcut to the built-in 'item' sieve is to start the
                # sieve with an ItemPath
                name = Symbol("item")
                args = parsed

            else:
                name = ensure_symbol(parsed[0], "Sieve names must be symbols")
                args = parsed[1:]

            cls = self._sieve_classes.get(name)

            if cls is None:
                # no direct matches, so we'll look up syntactic
                # aliases.  This is where conversion of the ! prefix
                # and the ?  suffix would happen.
                newname, args = self._convert_sieve_aliases(name, args)
                cls = self._sieve_classes.get(newname)

            if cls is None:
                # even after converting for aliases we have no match, so
                # we cannot compile the sieve.
                raise SifterError(f"No such sieve: {name}")

            # looks for positional and option parameters from the tail
            # of the list.
            args, kwds = gather_args(map(self._convert, args))

            try:
                result = cls(self, *args, **kwds)

            except TypeError as te:
                raise SifterError(f"Error creating Sieve {name}: {te}")

        elif isinstance(parsed, Symbol):
            if parsed.startswith("$") and parsed[1:] in self.params:
                # this is a parameter reference, and should be
                # converted to the value of the parameter.
                result = convert_token(self.params[parsed[1:]])
                result = self._convert(result)
            else:
                result = parsed

        elif isinstance(parsed, str):
            if "{" in parsed:
                # strings can have {param_name} entries in them which
                # will allow for substitutions with parameters
                result = parsed.format(**self.params)
            else:
                result = parsed

        else:
            result = parsed

        return result


    def run(self,
            session: ClientSession,
            info_dicts: Iterable[ST]) -> Dict[str, List[ST]]:
        """
        Clears existing flags and runs contained sieves on the given
        info_dicts.
        """

        self._flags.clear()

        key = self.key
        data = {key(b): b for b in info_dicts if b}
        work = tuple(data.values())

        for expr in self._exprs:
            autoflag = not isinstance(expr, Flagger)
            for binfo in expr(session, work):
                if autoflag:
                    self.set_flag("default", binfo)

        results = {}
        for flag, bids in self._flags.items():
            results[flag] = [data[bid] for bid in bids]

        return results


    def __call__(self,
                 session: ClientSession,
                 info_dicts: Iterable[ST]) -> Dict[str, List[ST]]:
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


    def is_flagged(
            self,
            flagname: str,
            data: ST) -> bool:
        """
        True if the data has been flagged with the given flagname, either
        via a ``(flag ...)`` sieve expression, or via `set_flag`
        """

        return ((flagname in self._flags) and
                (self._flags[flagname].get(self.key(data), False)))


    def set_flag(
            self,
            flagname: str,
            data: ST):
        """
        Records the given data as having been flagged with the given
        flagname.
        """

        bfl: Dict[Any, bool] = self._flags.get(flagname)
        if bfl is None:
            # we want to preserve the order
            self._flags[flagname] = bfl = {}

        bfl[self.key(data)] = True


    def get_cache(self, cachename, key) -> dict:
        """
        Flexible storage for caching data in a sifter. Sieves can use this
        to record data about individual info dicts, or to cache results
        from arbitrary koji session calls.

        This data is cleared when the `reset` method is invoked.
        """

        cachekey = (cachename, key)
        cch = self._cache.get(cachekey)
        if cch is None:
            cch = self._cache[cachekey] = {}
        return cch


    def get_info_cache(self, cachename, data) -> dict:
        """
        Cache associated with a particular info dict.

        This data is cleared when the `reset` method is invoked
        """

        return self.get_cache(cachename, self.key(data))


class Sieve(metaclass=ABCMeta):
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
    def name(self) -> str:
        pass


    aliases: Sequence[str] = ()


    def __init__(self,
                 sifter: Sifter,
                 *tokens, **options):
        self.sifter = sifter
        self.key = sifter.key
        self.tokens = tokens
        self.options = options


    def __call__(
            self,
            session: ClientSession,
            info_dicts: Iterable[ST]) -> Iterable[ST]:

        work = tuple(info_dicts)
        return tuple(self.run(session, work)) if work else work


    def __repr__(self):
        params = list(map(repr, self.tokens))
        for key, val in self.options.items():
            params.append(key + ":")
            params.append(repr(val))

        if params:
            e = " ".join(params)
            return f"({self.name} {e})"
        else:
            return f"({self.name})"


    def check(self,
              session: ClientSession,
              info: ST) -> bool:
        """
        Override to return True if the predicate matches the given
        info dict.

        This is used by the default `run` implementation in a filter.
        Only the info dicts which return True from this method will be
        included in the results.

        :param info: The info dict to be checked.
        """

        pass


    def prep(self,
             session: ClientSession,
             info_dicts: Iterable[ST]):
        """
        Override if some bulk pre-loading operations are necessary.

        This is used by the default `run` implementation to allow bulk
        operations to be performed over the entire set of info dicts
        to be filtered, rather than one at a time in the `check`
        method
        """

        return


    def run(self,
            session: ClientSession,
            info_dicts: Iterable[ST]) -> Iterable[ST]:
        """
        Use this Sieve instance to select and return a subset of the
        info_dicts sequence.
        """

        self.prep(session, info_dicts)
        return filter(partial(self.check, session), info_dicts)


    def get_cache(self, key: str) -> dict:
        """
        Gets a cache dict from the sifter using the name of this sieve
        and the given key (which must be hashable)

        The same cache dict will be returned for this key until the
        sifter has its `reset` method invoked.
        """

        return self.sifter.get_cache(self.name, key)


    def get_info_cache(self, info: ST) -> dict:
        """
        Gets a cache dict from the sifter using the name of this sieve and
        the sifter's designated key for the given info dict. The default
        sifter key will get the "id" value from the info dict.

        The same cache dict will be returned for this info dict until
        the sifter has its `reset` method invoked.
        """

        return self.sifter.get_info_cache(self.name, info)


class MatcherSieve(Sieve):
    """
    A Sieve that requires all of its arguments to be matchers. Calls
    `ensure_all_matcher` on `tokens`
    """

    def __init__(self, sifter, *tokens):
        tokens = ensure_all_matcher(tokens)
        super().__init__(sifter, *tokens)


class SymbolSieve(Sieve):
    """
    A Sieve that requires all of its arguments to be matchers. Calls
    `ensure_all_symbol` on `tokens`
    """

    def __init__(self, sifter, *tokens):
        tokens = ensure_all_symbol(tokens)
        super().__init__(sifter, *tokens)


class IntStrSieve(Sieve):
    """
    A Sieve that requires all of its arguments to be matchers. Calls
    `ensure_all_int_or_str` on `tokens`
    """

    def __init__(self, sifter, *tokens):
        tokens = ensure_all_int_or_str(tokens)
        super().__init__(sifter, *tokens)


class Logic(Sieve, metaclass=ABCMeta):

    check = None


    def __init__(self, sifter, *exprs):
        exprs = ensure_all_sieve(exprs)
        super().__init__(sifter, *exprs)


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
        work = {self.key(b): b for b in info_dicts}
        results = {}

        for expr in self.tokens:
            if not work:
                break

            for b in expr(session, work.values()):
                bid = self.key(b)
                del work[bid]
                results[bid] = b

        return results.values()


class LogicNot(Logic):
    """
    Usage: ``(not EXPR [EXPR...])``

    filters for info dicts which match none of the sub expressions.
    """

    name = "not"
    aliases = ("!", )


    def run(self, session, info_dicts):
        work = {self.key(b): b for b in info_dicts}

        for expr in self.tokens:
            if not work:
                break

            for b in expr(session, work.values()):
                del work[self.key(b)]

        return work.values()


class Flagger(LogicAnd):
    """
    Usage: ``(flag NAME EXPR [EXPR...])``

    filters for info dicts which match all of the sub expressions, and
    marks them with the given named flag.
    """

    name = "flag"


    def __init__(self, sifter, flag, *exprs):
        super().__init__(sifter, *exprs)
        self.flag = ensure_symbol(flag)


    def run(self, session, info_dicts):
        results = super().run(session, info_dicts)

        for info in results:
            self.sifter.set_flag(self.flag, info)

        return results


    def __repr__(self):
        e = " ".join(map(repr, self.tokens))
        return f"({self.name} {self.flag!r} {e})"


class VariadicSieve(Sieve, metaclass=ABCMeta):
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
        super().__init__(sifter, token)
        self.token = token


class Flagged(VariadicSieve):
    """
    Usage: ``(flagged NAME [NAME...])``

    filters for info dicts which have been marked with any of the
    given named flags
    """

    name = "flagged"
    aliases = ("?", )


    def __init__(self, sifter, name):
        super().__init__(sifter, ensure_symbol(name))


    def check(self, session, info):
        return self.sifter.is_flagged(self.token, info)


class ItemSieve(VariadicSieve, metaclass=ABCMeta):
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
        super().__init__(sifter, pattern)


    def check(self, session, info):
        if self.token is None:
            return info.get(self.field) is not None
        else:
            return ((self.field in info) and
                    (self.token == info[self.field]))


    def __repr__(self):
        if self.token is None:
            return f"({self.name})"
        else:
            return f"({self.name} {self.token!r})"


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
        super().__init__(sifter, *values)

        self.path = path


    def check(self, session, data):
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
        if self.tokens:
            e = " ".join(map(str, self.tokens))
            return f"({self.name} {self.path!s} {e})"
        else:
            return f"({self.name} {self.path!s})"


DEFAULT_SIEVES: List[Type[Sieve]] = [
    Flagged, Flagger,
    ItemPathSieve,
    LogicAnd, LogicOr, LogicNot,
]


#
# The end.
