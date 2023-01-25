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
Koji Smoky Dingo - CLI

This package contains mechanisms for more easily adding new
command-line features to the Koji client, in coordination with the
kojismokydingometa plugin.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import sys

from abc import ABCMeta, abstractmethod
from argparse import Action, ArgumentParser, Namespace
from collections import namedtuple
from contextlib import contextmanager
from functools import lru_cache, partial
from io import StringIO
from itertools import zip_longest
from json import dump
from koji import ClientSession, GenericError
from koji_cli.commands import _print_histline, _table_keys
from koji_cli.lib import activate_session, ensure_connection
from operator import itemgetter
from os import devnull
from os.path import basename
from typing import (
    Any, Callable, Dict, Iterable, List, Optional,
    Sequence, TextIO, Tuple, Union, )

from .. import BadDingo, NotPermitted
from ..common import load_plugin_config
from ..types import GOptions, HistoryEntry


__all__ = (
    "AdminSmokyDingo",
    "AnonSmokyDingo",
    "HostSmokyDingo",
    "SmokyDingo",
    "TagSmokyDingo",
    "TargetSmokyDingo",

    "clean_lines",
    "convert_history",
    "find_action",
    "remove_action",
    "int_or_str",
    "open_output",
    "pretty_json",
    "print_history",
    "print_history_results",
    "printerr",
    "read_clean_lines",
    "resplit",
    "space_normalize",
    "tabulate",
)


# these mimic the default format for jq output
JSON_PRETTY_OPTIONS = {
    "indent": 2,
    "separators": (",", ": "),
    "sort_keys": True,
}


def pretty_json(
        data: Any,
        output: Optional[TextIO] = None,
        **pretty):
    """
    Presents JSON in a pretty way.

    Keyword arguments are passed along to `json.dump` to alter the
    default output format defined by `JSON_PRETTY_OPTIONS`

    :param data: value to be printed

    :param output: stream to print to. Default, `sys.stdout`

    :param pretty: additional or overriding options to `json.dump`

    :since: 1.0
    """

    if output is None:
        output = sys.stdout

    if pretty:
        pretty_options = dict(JSON_PRETTY_OPTIONS, **pretty)
    else:
        pretty_options = JSON_PRETTY_OPTIONS

    dump(data, output, **pretty_options)
    print(file=output)


def find_action(
        parser: ArgumentParser,
        key: str) -> Optional[Action]:
    """
    Hunts through a parser to discover an action whose dest, metavar,
    or option strings matches the given key.

    :param parser: argument parser to search within

    :param key: the dest, metavar, or option string of the action

    :returns: the first matching Action, or None

    :since 1.0:
    """

    for act in parser._actions:
        if key == act.dest or key == act.metavar \
           or key in act.option_strings:
            return act
    return None


def remove_action(
        parser: ArgumentParser,
        key: str):
    """
    Hunts through a parser to remove an action based on the given key. The
    key can match either the dest, the metavar, or the option strings.

    :param parser: argument parser to remove the action from

    :param key: value to identify the action by

    :since 1.0:
    """

    found = find_action(parser, key)
    if found is None:
        return

    parser._actions.remove(found)

    if found in parser._optionals._actions:
        parser._optionals._actions.remove(found)

    for grp in parser._action_groups:
        if found in grp._group_actions:
            grp._group_actions.remove(found)


def resplit(
        arglist: Iterable[str],
        sep: str = ",") -> List[str]:
    """
    Collapses comma-separated and multi-specified items into a single
    list. Useful with ``action="append"`` in an argparse
    argument.

    this allows command-line arguments like

    ``-x 1 -x 2, -x 3,4,5 -x ,6,7, -x 8``

    to become

    ``x = [1, 2, 3, 4, 5, 6, 7, 8]``

    :param arglist: original series of arguments to be resplit

    :param sep: separator character

    :since 1.0:
    """

    work = map(str.strip, sep.join(arglist).split(sep))
    return list(filter(None, work))


@contextmanager
def open_output(
        filename: str = "-",
        append: Optional[bool] = None):
    """
    Context manager for a CLI output file.

    Files will be opened for text-mode output, and closed when the
    context exits.

    If the filename is ``"-"`` then stdout will be used as the output file
    stream, but it will not be closed.

    If the filename is ``""`` or ``None`` then `os.devnull` will be used.

    If append is True, the file will be appended to. If append is
    False, the file will be overwritten. If append is None, then the
    file will be overwriten unless it specified with a prefix of
    ``"@"``. This prefix will be stripped from the filename in this
    case only.

    :since: 1.0
    """

    if filename:
        if append is None:
            if filename.startswith("@"):
                filename = filename[1:]
                append = True
            else:
                append = False
    else:
        filename = devnull

    if filename == "-":
        stream = sys.stdout
    else:
        stream = open(filename, "at" if append else "wt")

    yield stream

    if filename != "-":
        stream.close()


def clean_lines(
        lines: Iterable[str],
        skip_comments: bool = True) -> List[str]:
    """
    Filters clean lines from a sequence.

    Each line will be stripped of leading and trailing whitespace.

    If skip_comments is True (the default), then any line with a
    leading hash ('#') will be considered a comment and omitted from
    the output.

    :param lines: Sequence of lines to process

    :param skip_comments: Skip over lines with leading # characters.
      Default, True

    :since: 1.0
    """

    if skip_comments:
        lines = (l.split('#', 1)[0].strip() for l in lines)
    else:
        lines = map(str.strip, lines)

    return list(filter(None, lines))


def read_clean_lines(
        filename: str = "-",
        skip_comments: bool = True) -> List[str]:
    """
    Reads clean lines from a named file. If filename is ``-`` then
    read from `sys.stdin` instead.

    Each line will be stripped of leading and trailing whitespace.

    If skip_comments is True (the default), then any line with a
    leading hash ('#') will be considered a comment and omitted from
    the output.

    Content will be fully collected into a list and the file (if not
    stdin) will be closed before returning.

    :param filename: File name to read lines from, or ``-`` to indicate
      stdin. Default, read from `sys.stdin`

    :param skip_comments: Skip over lines with leading # characters.
      Default, True

    :since: 1.0
    """

    if not filename:
        return []

    elif filename == "-":
        return clean_lines(sys.stdin)

    else:
        with open(filename, "rt") as fin:
            return clean_lines(fin)


def printerr(
        *values: Any,
        sep: str = ' ',
        end: str = '\n',
        flush: bool = False):
    """
    Prints values to stderr by default

    :param values: values to be printed

    :param sep: text inserted between values, defaults to a space

    :param end: text appended after the last value, defaults to a newline

    :param flush: forcibly flush the stream

    :since: 1.0
    """

    # we don't use a partial because docs can't figure out a signature
    # for print
    return print(*values, sep=sep, end=end, file=sys.stderr, flush=flush)


def tabulate(
        headings: Sequence[str],
        data: Any,
        key: Callable = None,
        sorting: int = 0,
        quiet: Optional[bool] = None,
        out: TextIO = None):
    """
    Prints tabulated data, with the given headings.

    This function is not resilient -- the headings and data must have
    the same count of rows, nothing will inject empty values.

    Output will be configured to set the columns to their maximum
    width necessary for the longest value from all the rows or the
    heading.

    :param headings: The column titles

    :param data: Rows of data

    :param key: Transformation to apply to each row of data to get the
      actual individual columns. Should be a unary function. Default,
      data is iterated as-is.

    :param sorting: Whether data rows should be sorted and in what
      direction. 0 for no sorting, 1 for ascending, -1 for
      descending. If key is specified, then sorting will be based on
      those transformations. Default, no sorting.

    :param quiet: Whether to print headings or not. Default, only print
      headings if out is a TTY device.

    :param out: Stream to write output to. Default, `sys.stdout`

    :since: 1.0
    """

    if out is None:
        out = sys.stdout

    # The quiet setting has three values. True meaning no header,
    # False meaning header, and None meaning no header if out is not a
    # TTY.
    if quiet is None:
        quiet = not out.isatty()

    if key is not None:
        if not callable(key):
            key = itemgetter(key)

        # convert data to a list, and apply the key if necessary to find
        # the real columns
        data = map(key, data)

    if sorting:
        data = sorted(data, reverse=(sorting < 0))
    else:
        data = list(data)

    # now we need to compute the maximum width of each columns
    if data:
        widths = [max(len(str(v)) for v in col)
                  for col in zip_longest(*data, fillvalue="")]
    else:
        widths = []

    if headings and not quiet:
        widths = [max(w or 0, len(h or "")) for w, h in
                  zip_longest(widths, headings)]

    # now we create the format string based on the max width of each
    # column plus some spacing.
    fmt = "  ".join(f"{{!s:<{w}}}" for w in widths)

    if headings and not quiet:
        print(fmt.format(*headings), file=out)
        print("  ".join(("-" * h) for h in widths), file=out)

    for row in data:
        print(fmt.format(*row), file=out)


def space_normalize(txt: str) -> str:
    """
    Normalizes the whitespace in txt to single spaces.

    :param txt: Original text

    :since: 1.0
    """

    return " ".join(txt.split())


def int_or_str(value: Any) -> Union[int, str]:
    """
    For use as an argument type where the value may be either an int
    (if it is entirely numeric) or a str.

    :since: 1.0
    """

    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            pass

    elif not isinstance(value, int):
        value = str(value)

    return value


def convert_history(
        history: Dict[str, List[Dict[str, Any]]]) -> List[HistoryEntry]:
    """
    Converts the history dicts as returned from the
    `ClientSession.queryHistory` API into the format `print_history`
    expects.

    Note that the results are a single list, containing the history
    from all tables. By default these will be in the order of the
    table name, then in the order given.

    :param history: mapping of table name to list of history events

    :since: 2.0
    """

    results: List[HistoryEntry] = []
    timeline: List[HistoryEntry] = []

    for table, events in history.items():
        for event in events:
            event_id: int
            event_id = event.get('revoke_event')
            if event_id:
                timeline.append((event_id, table, False, dict(event)))
            event_id = event.get('create_event')
            if event_id:
                timeline.append((event_id, table, True, event))

    timeline.sort(key=itemgetter(0, 1, 2))

    # group edits together
    last_event = None
    edit_index: Dict[Tuple[str, int], Dict[Tuple, Dict[str, Any]]] = {}
    for entry in timeline:
        event_id, table, create, x = entry
        if event_id != last_event:
            edit_index = {}
            last_event = event_id
        key = tuple([x[k] for k in _table_keys[table]])
        prev = edit_index.setdefault((table, event_id), {})
        if key in prev:
            prev_x = prev[key]
            prev_x.setdefault('.related', []).append(entry)
        else:
            prev[key] = x
            results.append(entry)

    return results


def print_history(
        timeline: Sequence[HistoryEntry],
        utc: bool = False,
        show_events: bool = False,
        verbose: bool = False):

    """
    Print history lines using koji's own history formatting. The
    history timeline needs to be in the format koji is expecting. The
    results from `ClientSession.queryHistory` can be converted via the
    `convert_history` function.

    :param timeline: A sequence of history events to display

    :param utc: output timestamps in UTC instead of local time

    :param show_events: print the individual event IDs

    :param verbose: enables show_events and some additional output

    :since: 2.0
    """

    Opts = namedtuple('Opts', ['utc', 'events', 'verbose'])
    options = Opts(utc, show_events, verbose)

    for event in timeline:
        _print_histline(event, options=options)


def print_history_results(
        timeline: Dict[str, List[Dict[str, Any]]],
        utc: bool = False,
        show_events: bool = False,
        verbose: bool = False):

    """
    Prints history lines using koji's own history formatting. The
    history timeline should be in the format as returned by the
    `ClientSession.queryHistory` API.

    This is a convenience function that combines the `convert_history`
    and `print_history` functions.

    :param timeline: A sequence of history events to display

    :param utc: output timestamps in UTC instead of local time

    :param show_events: print the individual event IDs

    :param verbose: enables show_events and some additional output

    :since: 2.0
    """

    history = convert_history(timeline)
    return print_history(history, utc, show_events, verbose)


class SmokyDingo(metaclass=ABCMeta):
    """
    Base class for new sub-commands in Koji. Subclasses may be
    referenced via an entry point under the koji_smoky_dingo group to
    be loaded at runtime by the kojismokydingometa Koji client plugin.

    Summary of behavior is as follows

    * kojismokydingometa plugin loads when koji client launches

    * the meta plugin loads all `koji_smoky_dingo` entry points

    * each entry point name is a command name, and the reference should
      resolve to a subclass of `SmokyDingo`

    * each entry point is instantiated, and presented to the koji cli
      as a new sub-command

    * if the sub-command is invoked, then the `SmokyDingo` instance is
      called, this triggers the following:

      * the `SmokyDingo.parser` method provides an ArgumentParser
        instance which it then decorates with arguments by passing it
        to `SmokyDingo.arguments`

      * the `SmokyDingo.validate` method provides a chance to validate
        and/or manipulate the parsed arguments

      * the `SmokyDingo.activate` method authenticates with the hub

      * the `SmokyDingo.pre_handle` method verifies that any required
        permissions are present for the user

      * the `SmokyDingo.handle` method invokes the actual work of the
        sub-command
    """

    group: str = "misc"
    """
    The koji CLI group that this command will be displayed under in
    the help output
    """

    description: str = "A CLI Plugin"
    """
    Short description of this command, for use in the help output
    """

    # permission name required for use of this command. A value of
    # None indicates anonymous access. Checked in the pre_handle
    # method.
    permission: str = None
    """
    permission name required for use of this command. A value of None
    indicates anonymous access.
    """

    def __init__(self, name: str = None):
        """
        :param name: The name that this command is being represented as
        """

        if name is not None:
            self.name: str = name

        elif getattr(self, "name", None) is None:
            # check that the class doesn't already define a name as a
            # default. Failing that, use a squished version of the
            # classname
            self.name = type(self).__name__.lower()

        # this is used to register the command with koji in a manner
        # that it expects to deal with
        self.__name__: str = "handle_" + self.name.replace("-", "_")

        # this is necessary for koji to recognize us as a cli command.
        # We only set this on instances, not on the class itself,
        # because it is only the instances which should be used that
        # way.
        self.exported_cli: bool = True

        # allow a docstr to be specified on subclasses, but if absent
        # let's set it based on the group and description.
        if getattr(self, "__doc__", None) is None:
            desc = space_normalize(self.description)
            self.__doc__ = f"[{self.group}] {desc}"
        else:
            desc = space_normalize(self.__doc__)
            if not desc.startswith("["):
                desc = f"[{self.group}] {desc}"
            self.__doc__ = desc

        # populated by the get_plugin_config method
        self.config: Dict[str, Any] = None

        # these will be populated once the command instance is
        # actually called
        self.goptions: GOptions = None
        self.session: ClientSession = None


    def get_plugin_config(self, key: str, default: Any = None) -> Any:
        """
        fetch a configuration value for this command under the given key. If
        no configuration is found, returns the default.

        :param key: the configuration key name
        :param default: value to return if no configuration is found
        """

        if self.config is None:
            profile = self.goptions.profile if self.goptions else None
            self.config = load_plugin_config(self.name, profile)

        return self.config.get(key, default)


    @property
    @lru_cache(1)
    def enabled(self):
        val = self.get_plugin_config("enabled", "1")
        return val and val.lower() in ("1", "yes", "true")


    def parser(self) -> ArgumentParser:
        """
        Creates a new ArgumentParser instance and decorates it with
        arguments from the `arguments` method.
        """

        invoke = f"{basename(sys.argv[0])} {self.name}"
        argp = ArgumentParser(prog=invoke, description=self.description)
        return self.arguments(argp) or argp


    def arguments(
            self,
            parser: ArgumentParser) -> Optional[ArgumentParser]:
        """
        Override to add relevant arguments to the given parser instance.
        May return an alternative parser instance or None.

        :param parser: the parser to decorate with additional arguments
        """

        pass


    def validate(
            self,
            parser: ArgumentParser,
            options: Namespace) -> None:
        """
        Override to perform validation on options values. Return value is
        ignored, use `parser.error` if needed.
        """

        pass


    def pre_handle(
            self,
            options: Namespace) -> None:
        """
        Verify necessary permissions are in place before attempting any
        further calls.
        """

        if self.permission and self.session:
            session = self.session
            userinfo = session.getLoggedInUser()
            userperms = session.getUserPerms(userinfo["id"]) or ()

            if not (self.permission in userperms or "admin" in userperms):
                msg = f"Insufficient permissions for command {self.name}"
                raise NotPermitted(msg)


    @abstractmethod
    def handle(self,
               options: Namespace) -> Optional[int]:
        """
        Perform the full set of actions for this command.
        """

        pass


    def activate(self) -> None:
        """
        Activate our session. This is triggered after validate, before
        pre_handle and handle

        The session and goptions attributes will have been set just
        prior.
        """

        if self.session:
            return activate_session(self.session, self.goptions)


    def deactivate(self) -> None:
        """
        Deactivate our session. This is triggered after handle has
        completed, either normally or by raising an exception.

        The session and goptions attributes will be cleared just
        after.
        """

        if self.session:
            try:
                self.session.logout()
            except BaseException:
                pass


    def __call__(
            self,
            goptions: GOptions,
            session: ClientSession,
            args: List[str] = None) -> int:
        """
        This is the koji CLI handler interface. The global options, the
        session, and the unparsed command arguments are provided.
        """

        self.goptions = goptions
        self.session = session

        parser = self.parser()
        options = parser.parse_args(args)

        self.validate(parser, options)

        try:
            self.activate()
            self.pre_handle(options)
            return self.handle(options) or 0

        except KeyboardInterrupt:
            printerr()
            return 130

        except GenericError as kge:
            printerr(kge)
            return -1

        except BadDingo as bad:
            printerr(bad)
            return -2

        except Exception:
            # koji CLI hides tracebacks from us. If something goes
            # wrong, we want to see it
            import traceback
            traceback.print_exc()
            raise

        finally:
            self.deactivate()
            self.goptions = None
            self.session = None


class AnonSmokyDingo(SmokyDingo, metaclass=ABCMeta):
    """
    A SmokyDingo which upon activation will connect to koji hub, but
    will not authenticate. This means only hub RPC endpoints which do
    not require some permission will work. This is normal for most
    read-only informational endpoints.
    """

    group = "info"
    permission = None


    def __init__(self, name=None):
        super().__init__(name)

        # koji won't even bother fully authenticating our session for
        # this command if we tweak the name like this. Since
        # subclasses of this are meant to be anonymous commands
        # anyway, we may as well omit the session init
        self.__name__ = "anon_handle_" + self.name.replace("-", "_")


    def activate(self):
        # rather than logging on, we only open a connection
        if self.session:
            ensure_connection(self.session)


    def pre_handle(self, options):
        # do not check permissions at all, we won't be logged in
        pass


class AdminSmokyDingo(SmokyDingo, metaclass=ABCMeta):
    """
    A SmokyDingo which checks for the 'admin' permission after
    activation.
    """

    group = "admin"
    permission = "admin"


class TagSmokyDingo(SmokyDingo, metaclass=ABCMeta):
    """
    A SmokyDingo which checks for the 'tag' or 'admin' permission after
    activation.
    """

    group = "admin"
    permission = "tag"


class TargetSmokyDingo(SmokyDingo, metaclass=ABCMeta):
    """
    A SmokyDingo which checks for the 'target' or 'admin' permission
    after activation.
    """

    group = "admin"
    permission = "target"


class HostSmokyDingo(SmokyDingo, metaclass=ABCMeta):
    """
    A SmokyDingo which checks for the 'host' or 'admin' permisson
    after activation.
    """

    group = "admin"
    permission = "host"


#
# The end.
