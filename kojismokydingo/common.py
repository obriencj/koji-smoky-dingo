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
# work with the koji-specific dict types (build info, tag info, etc)


import re

from collections import OrderedDict
from datetime import datetime
from fnmatch import fnmatchcase
from glob import glob
from operator import itemgetter
from os.path import expanduser, isdir, join
from six import iteritems, itervalues
from six.moves import filter, filterfalse, range, zip_longest
from six.moves.configparser import ConfigParser


try:
    from datetime import timezone
except ImportError:  # pragma: no cover
    timezone = None

try:
    import appdirs
except ImportError:  # pragma: no cover
    appdirs = None


__all__ = (
    "chunkseq",
    "fnmatches",
    "find_config_dirs",
    "find_config_files",
    "get_plugin_config",
    "globfilter",
    "load_full_config",
    "load_plugin_config",
    "merge_extend",
    "parse_datetime",
    "rpm_evr_compare",
    "unique",
    "update_extend",
)


def chunkseq(seq, chunksize):
    """
    Chop up a sequence into sub-sequences, each up to chunksize in
    length.

    :param seq: a sequence to chunk up
    :type seq: list

    :param chunksize: max length for chunks
    :type chunksize: int

    :rtype: Generator[list]
    """

    if not isinstance(seq, (tuple, list)):
        seq = list(seq)
    seqlen = len(seq)

    return (seq[offset:offset + chunksize] for
            offset in range(0, seqlen, chunksize))


def escapable_replace(orig, character, replacement):
    """
    Single-character string substitutions. Doubled sentinel characters
    can be used to represent that exact character.

    Examples:

     * ``escapable_replace('Hello %', '%', 'World')`` returns ``"Hello
       World"``
     * ``escapable_replace('Hello %%', '%', 'World')`` returns
       ``"Hello %"``

    :param orig: Original text
    :type orig: str

    :param character: Single-character token.
    :type character: str

    :param replacement: Replacement text
    :type replacement: str
    """

    assert len(character) == 1, "escapable_replace requires single characters"

    gather = []
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


def fnmatches(value, patterns, ignore_case=False):
    """
    Checks value against multiple glob patterns. Returns True if any
    match.

    :param value: string to be matched
    :type value: str

    :param patterns: list of glob-style pattern strings
    :type patterns: list[str]

    :param ignore_case: if True case is normalized, Default False
    :type ignore_case: bool, optional

    :rtype: bool
    """

    if ignore_case:
        value = value.lower()
        patterns = [p.lower() for p in patterns]

    for pattern in patterns:
        if fnmatchcase(value, pattern):
            return True
    else:
        return False


def update_extend(dict_orig, *dict_additions):
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

    :type dict_orig: dict[object, list]

    :param dict_additions: The additions dict. Will not be altered.

    :type dict_additions: dict[object, list]

    :returns: The original dict instance

    :rtype: dict[object, list]
    """

    for additions in dict_additions:
        for key, val in iteritems(additions):
            orig = dict_orig.setdefault(key, [])
            orig.extend(val)

    return dict_orig


def merge_extend(*dict_additions):
    """
    Similar to `update_extend` but creates a new dict to hold results,
    and new initial lists to be extended, leaving all the arguments
    unaltered.

    :param dict_additions: The additions dict. Will not be altered.

    :type dict_additions: dict[object, list]

    :returns: A new dict, whose values are new lists

    :rtype: dict[object, list]
    """

    return update_extend({}, *dict_additions)


def globfilter(seq, patterns,
               key=None, invert=False, ignore_case=False):
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

    :type seq: list

    :param patterns: list of glob-style pattern strings. Members of
      seq which match any of these patterns are yielded.

    :type patterns: list[str]

    :param key: A unary callable which translates individual items on
      seq into the value to be matched against the patterns. Default,
      match against values in seq directly.

    :type key: Callable[[object], str], optional

    :param invert: Invert the logic, yielding the non-matches rather
      than the matches. Default, yields matches

    :type invert: bool, optional

    :param ignore_case: pattern comparison is case normalized if
      True. Default, False

    :type ignore_case: bool, optional

    :rtype: Iterable[object]
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


def _rpm_str_split(s, _split=re.compile(r"(~?(?:\d+|[a-zA-Z]+))").split):
    """
    Split an E, V, or R string for comparison by its segments
    """

    return tuple(i for i in _split(s) if (i.isalnum() or i.startswith("~")))


def _rpm_str_compare(left, right):
    """
    Comparison of left and right by RPM version comparison rules.

    Either string should be *one* element of the EVR tuple (ie. either the
    epoch, version, or release). Comparison will split the element on RPM's
    special delimeters.
    """

    left = _rpm_str_split(left)
    right = _rpm_str_split(right)

    for lp, rp in zip_longest(left, right, fillvalue=""):

        # Special comparison for tilde segments
        if lp.startswith("~"):
            # left is tilde

            if rp.startswith("~"):
                # right also is tilde, let's just chop off the tilde
                # and fall through to non-tilde comparisons below

                lp = lp[1:]
                rp = rp[1:]

            else:
                # right is not tilde, therefore right is greater
                return -1

        elif rp.startswith("~"):
            # left is not tilde, but right is, therefore left is greater
            return 1

        # Special comparison for digits vs. alphabetical
        if lp.isdigit():
            # left is numeric

            if rp.isdigit():
                # left and right are both numeric, convert and fall
                # through
                lp = int(lp)
                rp = int(rp)

            else:
                # right is alphabetical or absent, left is greater
                return 1

        elif rp.isdigit():
            # left is alphabetical but right is not, right is greater
            return -1

        # Final comparison for segment
        if lp == rp:
            # left and right are equivalent, check next segment
            continue
        else:
            # left and right are not equivalent
            return 1 if lp > rp else -1

    else:
        # ran out of segments to check, must be equivalent
        return 0


def rpm_evr_compare(left_evr, right_evr):
    """
    Compare two (Epoch, Version, Release) tuples.

    This is an alternative implementation of the rpm lib's
    labelCompare function.

    Return values:

    * 1 if left_evr is greater-than right_evr
    * 0 if left_evr is equal-to right_evr
    * -1 if left_evr is less-than right_evr

    :param left_evr: The left Epoch, Version, Release for comparison
    :type left_evr: (str, str, str)

    :param right_evr: The right Epoch, Version, Release for comparison
    :type right_evr: (str, str, str)

    :rtype: int
    """

    for lp, rp in zip_longest(left_evr, right_evr, fillvalue="0"):
        if lp == rp:
            # fast check to potentially skip all the matching
            continue

        compared = _rpm_str_compare(lp, rp)
        if compared:
            # non zero comparison for segment, done checking
            return compared

    else:
        # ran out of segments to check, must be equivalent
        return 0


def unique(sequence, key=None):
    """
    Given a sequence, de-duplicate it into a new list, preserving
    order.

    In the event that the sequence contains non-hashable objects,
    `key` must be specified as a unary callable which produces a
    hashable unique identifier for the individual items in the
    sequence. This identifier is then used to perform the
    de-duplication.

    :param sequence: series of hashable objects
    :type sequence: list

    :param key: unary callable that produces a hashable identifying
      value. Default, use each object in sequence as its own
      identifier.

    :type key: Callable[[object],object], optional

    :rtype: list
    """

    # in python 3.6+ OrderedDict is not necessary here, but we're
    # supporting 2.6, 2.7 as well. At some point Python will likely do
    # something bad and deprecate OrderedDict, at that point we'll
    # have to begin detecting the version and using just plain dict

    if key:
        if not callable(key):
            # undocumented behavior! woo!!
            key = itemgetter(key)
        work = ((key(v), v) for v in sequence)
        return list(itervalues(OrderedDict(work)))
    else:
        return list(OrderedDict.fromkeys(sequence))


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


def parse_datetime(src, strict=True):
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

    :type src: str

    :param strict: Raise an exception if no matching format is known
      and the date-time text cannot be parsed. If False, simply return
      `None`

    :type strict: bool, optional

    :raises Exception: if strict and no src matches none of the
      pre-defined formats

    :rtype: `datetime` or `None`
    """

    if timezone is None:
        # This is gross, but if we are on an older Python with no
        # timezone support baked in, we need to remove the %z portion
        # and replace it with a hardcoded UTC for %Z instead.
        src = re.compile(r"([+-]\d{2}:?\d{2}$)").sub(" UTC", src)

    for pattern, parser in DATETIME_FORMATS:
        mtch = pattern.match(src)
        if mtch:
            return parser(mtch.string)
    else:
        if strict:
            raise Exception("Invalid date-time format, %r" % src)
        else:
            return None


def find_config_dirs():
    """
    The site and user configuration dirs, as a tuple. Attempts to use
    the ``appdirs`` package if it is available.

    :rtype: tuple[str]
    """

    if appdirs is None:
        site_conf_dir = "/etc/xdg/ksd/"
        user_conf_dir = expanduser("~/.config/ksd/")
    else:
        site_conf_dir = appdirs.site_config_dir("ksd")
        user_conf_dir = appdirs.user_config_dir("ksd")

    return (site_conf_dir, user_conf_dir)


def find_config_files(dirs=None):
    """
    The ordered list of configuration files to be loaded.

    If `dirs` is specified, it must be a sequence of directory names,
    from which conf files will be loaded in order. If unspecified,
    defaults to the result of `find_config_dirs`

    :param dirs: list of directories to look for config files within
    :type dirs: list[str], optional

    :rtype: list[str]
    """

    if dirs is None:
        dirs = find_config_dirs()

    found = []

    for confdir in dirs:
        if isdir(confdir):
            wanted = join(confdir, "*.conf")
            found.extend(sorted(glob(wanted)))

    return found


def load_full_config(config_files=None):
    """
    Configuration object representing the full merged view of config
    files.

    If `config_files` is None, use the results of `find_config_files`.
    Otherwise, `config_files` must be a sequence of filenames.

    :rtype: ConfigParser
    """

    if config_files is None:
        config_files = find_config_files()

    conf = ConfigParser()
    conf.read(config_files)

    return conf


def get_plugin_config(conf, plugin, profile=None):
    """
    Given a loaded configuration, return the section specific to the
    given plugin, and optionally profile

    :param conf: Full configuration
    :type conf: ConfigParser

    :param plugin: Plugin name
    :type plugin: str

    :param profile: Profile name
    :type profile: str, optional

    :rtype: dict[str,object]
    """

    plugin_conf = {}

    if conf.has_section(plugin):
        plugin_conf.update(conf.items(plugin))

    if profile is not None:
        profile = ":".join((plugin, profile))
        if conf.has_section(profile):
            plugin_conf.update(conf.items(profile))

    return plugin_conf


def load_plugin_config(plugin, profile=None):
    """
    Configuration specific to a given plugin, and optionally profile

    :param plugin: Plugin name
    :type plugin: str

    :param profile: Profile name
    :type profile: str, optional

    :rtype: dict[str,object]
    """

    conf = load_full_config()
    return get_plugin_config(conf, plugin, profile)


#
# The end.
