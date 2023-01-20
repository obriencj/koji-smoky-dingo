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
Koji Smoky Dingo - Common Utils

Some simple functions used by the other modules.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


# Note: features implemented in this module should not be specific to
# working with koji. ie: nothing should require a session object or
# work with the koji-specific types (build info, tag info, etc)


import re

from configparser import ConfigParser
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from functools import lru_cache
from glob import glob
from itertools import filterfalse
from operator import itemgetter
from os.path import expanduser, isdir, join
from typing import (
    Any, Callable, Dict, Iterable, Iterator, List,
    Optional, Sequence, Tuple, TypeVar, Union, )

from .types import KeySpec


try:
    import appdirs
except ImportError:  # pragma: no cover
    appdirs = None


__all__ = (
    "chunkseq",
    "escapable_replace",
    "fnmatches",
    "find_config_dirs",
    "find_config_files",
    "get_plugin_config",
    "globfilter",
    "load_full_config",
    "load_plugin_config",
    "merge_extend",
    "parse_datetime",
    "unique",
    "update_extend",
)


def chunkseq(
        seq: Iterable,
        chunksize: int) -> Iterator[Iterable]:
    """
    Chop up a sequence into sub-sequences, each up to chunksize in
    length.

    :param seq: a sequence to chunk up

    :param chunksize: max length for chunks

    :since: 1.0
    """

    if not isinstance(seq, (tuple, list)):
        seq = list(seq)
    seqlen = len(seq)

    return (seq[offset:offset + chunksize] for
            offset in range(0, seqlen, chunksize))


def escapable_replace(
        orig: str,
        character: str,
        replacement: str) -> str:
    """
    Single-character string substitutions. Doubled sentinel characters
    can be used to represent that exact character.

    Examples:

     * ``escapable_replace('Hello %', '%', 'World')`` returns ``"Hello
       World"``
     * ``escapable_replace('Hello %%', '%', 'World')`` returns
       ``"Hello %"``

    :param orig: Original text

    :param character: Single-character token.

    :param replacement: Replacement text

    :since: 1.0
    """

    assert len(character) == 1, "escapable_replace requires single characters"

    gather: List[str] = []
    collect = gather.append

    pieces = iter(orig)
    for p in pieces:
        if p == character:
            n = next(pieces, None)
            if n is None:
                collect(replacement)
            elif n == character:
                collect(character)
            else:
                collect(replacement)
                collect(n)
        else:
            collect(p)

    return "".join(gather)


def fnmatches(
        value: str,
        patterns: Iterable[str],
        ignore_case: bool = False) -> bool:
    """
    Checks value against multiple glob patterns. Returns True if any
    match.

    :param value: string to be matched

    :param patterns: list of glob-style pattern strings

    :param ignore_case: if True case is normalized, Default False

    :since: 1.0
    """

    if ignore_case:
        value = value.lower()
        patterns = [p.lower() for p in patterns]

    for pattern in patterns:
        if fnmatchcase(value, pattern):
            return True
    else:
        return False


KT = TypeVar('KT')


def update_extend(
        dict_orig: Dict[KT, List[Any]],
        *dict_additions: Dict[KT, List[Any]]) -> Dict[KT, List[Any]]:
    """
    Extend the list values of the original dict with the list values of
    the additions dict.

    eg.
    ::

        A = {'a': [1, 2], 'b': [7], 'c': [10]}
        B = {'a': [3], 'b': [8, 9], 'd': [11]}
        update_extend(A, B)

        A
        >> {'a': [1, 2, 3], 'b': [7, 8, 9], 'c': [10], 'd': [11]}

    The values of dict_orig must support an extend method.

    :param dict_orig: The original dict, which may be mutated and whose
      values may be extended

    :param dict_additions: The additions dict. Will not be altered.

    :returns: The original dict instance

    :since: 1.0
    """

    # oddity here, really *dict_additions should be Dict[Any,
    # Iterable] but for some bizarre reason MyPy doesn't consider
    # lists to be iterable when they're dict values. Really weird.

    for additions in dict_additions:
        for key, val in additions.items():
            orig = dict_orig.setdefault(key, [])
            orig.extend(val)

    return dict_orig


def merge_extend(
        *dict_additions: Dict[KT, List[Any]]) -> Dict[KT, List[Any]]:
    """
    Similar to `update_extend` but creates a new dict to hold results,
    and new initial lists to be extended, leaving all the arguments
    unaltered.

    :param dict_additions: The additions dict. Will not be altered.

    :returns: A new dict, whose values are new lists

    :since: 1.0
    """

    return update_extend({}, *dict_additions)


GFT = TypeVar('GFT')


def globfilter(
        seq: Iterable[GFT],
        patterns: Iterable[str],
        key: Optional[KeySpec] = None,
        invert: bool = False,
        ignore_case: bool = False) -> Iterable[GFT]:
    """
    Generator yielding members of sequence seq which match any of the
    glob patterns specified.

    Patterns must be a list of glob-style pattern strings.

    If key is specified, it must be a unary callable which translates a
    given sequence item into a string for comparison with the patterns.

    If invert is True, yields the non-matches rather than the matches.

    If ignore_case is True, the pattern comparison is case normalized.

    :param seq: series of objects to be filtered. Normally strings,
      but may be any type provided the key parameter is specified to
      provide a string for matching based on the given object.

    :param patterns: list of glob-style pattern strings. Members of
      seq which match any of these patterns are yielded.

    :param key: A unary callable which translates individual items on
      seq into the value to be matched against the patterns. Default,
      match against values in seq directly.

    :param invert: Invert the logic, yielding the non-matches rather
      than the matches. Default, yields matches

    :param ignore_case: pattern comparison is case normalized if
      True. Default, False

    :since: 1.0
    """

    if ignore_case:
        # rather than passing ignore_case directly on to fnmatches,
        # we'll do the case normalization ourselves. This way it only
        # needs to happen one time for the patterns
        patterns = [p.lower() for p in patterns]

    if not (key is None or callable(key)):
        key = itemgetter(key)

    def test(val):
        if key:
            val = key(val)
        if ignore_case:
            val = val.lower()
        return fnmatches(val, patterns)

    return filterfalse(test, seq) if invert else filter(test, seq)


UT = TypeVar('UT')


def unique(
        sequence: Iterable[UT],
        key: Optional[KeySpec] = None) -> List[UT]:
    """
    Given a sequence, de-duplicate it into a new list, preserving
    order.

    In the event that the sequence contains non-hashable objects,
    `key` must be specified as a unary callable which produces a
    hashable unique identifier for the individual items in the
    sequence. This identifier is then used to perform the
    de-duplication.

    :param sequence: series of hashable objects

    :param key: unary callable that produces a hashable identifying
      value. Default, use each object in sequence as its own
      identifier.

    :since: 1.0
    """

    if key:
        if not callable(key):
            # undocumented behavior! woo!!
            key = itemgetter(key)
        work = {key(v): v for v in sequence}
        return list(work.values())
    else:
        return list(dict.fromkeys(sequence))


DATETIME_FORMATS = (
    (re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} .{3}$"),
     lambda d: datetime.strptime(d, "%Y-%m-%d %H:%M:%S.%f %Z")),

    (re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}[+-]\d{4}$"),
     lambda d: datetime.strptime(d, "%Y-%m-%d %H:%M:%S.%f%z")),

    (re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}[+-]\d{2}:\d{2}$"),
     lambda d: datetime.strptime("".join(d.rsplit(":", 1)),
                                 "%Y-%m-%d %H:%M:%S.%f%z")),

    (re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} .{3}$"),
     lambda d: datetime.strptime(d, "%Y-%m-%d %H:%M:%S %Z")),

    (re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{4}$"),
     lambda d: datetime.strptime(d, "%Y-%m-%d %H:%M:%S%z")),

    (re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$"),
     lambda d: datetime.strptime("".join(d.rsplit(":", 1)),
                                 "%Y-%m-%d %H:%M:%S%z")),

    (re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"),
     lambda d: datetime.strptime(d, "%Y-%m-%d %H:%M:%S")),

    (re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}$"),
     lambda d: datetime.strptime(d, "%Y-%m-%d %H:%M")),

    (re.compile(r"\d{4}-\d{2}-\d{2}$"),
     lambda d: datetime.strptime(d, "%Y-%m-%d")),

    (re.compile(r"\d{4}-\d{2}$"),
     lambda d: datetime.strptime(d, "%Y-%m")),

    (re.compile(r"\d+$"),
     lambda d: datetime.utcfromtimestamp(int(d))),

    (re.compile("now$"),
     lambda d: datetime.utcnow()),
)


def parse_datetime(
        src: str,
        strict: bool = True) -> datetime:
    """
    Attempts to parse a datetime string in numerous ways based on
    pre-defined regex mappings

    Supported formats:
     - %Y-%m-%d %H:%M:%S.%f %Z
     - %Y-%m-%d %H:%M:%S.%f%z
     - %Y-%m-%d %H:%M:%S %Z
     - %Y-%m-%d %H:%M:%S%z
     - %Y-%m-%d %H:%M:%S
     - %Y-%m-%d %H:%M
     - %Y-%m-%d
     - %Y-%m

    Plus integer timestamps and the string ``"now"``

    Timezone offset formats (%z) may also be specified as either +HHMM
    or +HH:MM (the : will be removed)

    :param src: Date-time text to be parsed

    :param strict: Raise an exception if no matching format is known
      and the date-time text cannot be parsed. If False, simply return
      `None` when the value cannot be parsed.

    :raises ValueError: if strict and no src matches none of the
      pre-defined formats

    :since: 1.0
    """

    for pattern, parser in DATETIME_FORMATS:
        mtch = pattern.match(src)
        if mtch:
            return parser(mtch.string)
    else:
        if strict:
            raise ValueError(f"Invalid date-time format, {src!r}")
        else:
            return None


def find_config_dirs() -> Tuple[str, str]:
    """
    The site and user configuration dirs for koji-smoky-dingo, as a
    tuple. Attempts to use the ``appdirs`` package if it is available.

    :since: 1.0
    """

    if appdirs is None:
        site_conf_dir = "/etc/xdg/ksd/"
        user_conf_dir = expanduser("~/.config/ksd/")
    else:
        site_conf_dir = appdirs.site_config_dir("ksd")
        user_conf_dir = appdirs.user_config_dir("ksd")

    return (site_conf_dir, user_conf_dir)


def find_config_files(
        dirs: Optional[Iterable[str]] = None) -> List[str]:
    """
    The ordered list of configuration files to be loaded.

    If `dirs` is specified, it must be a sequence of directory names,
    from which conf files will be loaded in order. If unspecified,
    defaults to the result of `find_config_dirs`

    Configuration files must have the extension ``.conf`` to be
    considered. The files will be listed in directory order, and then
    in alphabetical order from within each directory.

    :param dirs: list of directories to look for config files within

    :since: 1.0
    """

    if dirs is None:
        dirs = find_config_dirs()

    found: List[str] = []

    for confdir in dirs:
        if isdir(confdir):
            wanted = join(confdir, "*.conf")
            found.extend(sorted(glob(wanted)))

    return found


@lru_cache(maxsize=1)
def _load_full_config(
        config_files: Optional[Tuple[str]] = None) -> ConfigParser:

    if config_files is None:
        config_files = find_config_files()  # type: ignore

    conf = ConfigParser()
    conf.read(config_files)

    return conf


def load_full_config(
        config_files: Optional[Iterable[str]] = None) -> ConfigParser:
    """
    Configuration object representing the full merged view of config
    files.

    If `config_files` is None, use the results of `find_config_files`.
    Otherwise, `config_files` must be a sequence of filenames.

    :param config_files: configuration files to be loaded, in order.
      If not specified, the results of `find_config_files` will be
      used.

    :returns: a configuration representing a merged view of all config
      files

    :since: 1.0
    """

    # this is actually just a wrapper to a cached call, but we need to
    # convert to a hashable argument type first.

    if config_files is not None:
        config_files = tuple(config_files)

    return _load_full_config(config_files)


def get_plugin_config(
        conf: ConfigParser,
        plugin: str,
        profile: Optional[str] = None) -> Dict[str, Any]:
    """
    Given a loaded configuration, return the section specific to the
    given plugin, and optionally profile-specific as well.

    :param conf: loaded configuration data

    :param plugin: plugin name

    :param profile: profile name, optional

    :since: 1.0
    """

    plugin_conf: Dict[str, Any] = {}

    if conf.has_section(plugin):
        plugin_conf.update(conf.items(plugin))

    if profile is not None:
        profile = ":".join((plugin, profile))
        if conf.has_section(profile):
            plugin_conf.update(conf.items(profile))

    return plugin_conf


def load_plugin_config(
        plugin: str,
        profile: Optional[str] = None) -> Dict[str, Any]:
    """
    Configuration specific to a given plugin, and optionally specific
    to a given profile as well.

    Profile-specific sections are denoted by a suffix on the section
    name, eg.

    ::

      [my_plugin]
      # this setting is for my_plugin on all profiles
      setting = foo

      [my_plugin:testing]
      # this setting is for my_plugin on the testing profile
      setting = bar

    :param plugin: plugin name

    :param profile: profile name

    :since: 1.0
    """

    conf = load_full_config()
    return get_plugin_config(conf, plugin, profile)


#
# The end.
