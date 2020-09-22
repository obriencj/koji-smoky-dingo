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


from __future__ import print_function

import sys

from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser
from functools import partial
from json import dump
from koji import GenericError
from koji_cli.lib import activate_session, ensure_connection
from os.path import basename
from six import add_metaclass
from six.moves import zip_longest

from kojismokydingo import BadDingo, NotPermitted


# these mimic the default format for jq output
JSON_PRETTY_OPTIONS = {
    "indent": 2,
    "separators": (",", ": "),
    "sort_keys": True,
}


def pretty_json(data, output=None, **pretty):
    """
    Presents JSON in a pretty way.

    Keyword arguments are passed along to `json.dump` to alter the
    default output format defined by `JSON_PRETTY_OPTIONS`

    :param data: value to be printed

    :type data: int or str or dict or list or None

    :param output: stream to print to. Default, `sys.stdout`

    :type output: io.TextIOBase, optional

    :rtype: None
    """

    if output is None:
        output = sys.stdout

    if pretty:
        pretty_options = dict(JSON_PRETTY_OPTIONS, **pretty)
    else:
        pretty_options = JSON_PRETTY_OPTIONS

    dump(data, output, **pretty_options)
    print(file=output)


def resplit(arglist, sep=","):
    """
    Collapses comma-separated and multi-specified items into a single
    list. Useful with ``action="append"`` in an argparse
    argument.

    this allows command-line arguments like

    ``-x 1 -x 2, -x 3,4,5 -x ,6,7, -x 8``

    to become

    ``x = [1, 2, 3, 4, 5, 6, 7, 8]``
    """

    work = (a.strip() for a in sep.join(arglist).split(sep))
    return [a for a in work if a]


def clean_lines(lines, skip_comments=True):
    """
    Filters clean lines from a sequence.

    Each line will be stripped of leading and trailing whitespace.

    If skip_comments is True (the default), then any line with a
    leading hash ('#') will be considered a comment and omitted from
    the output.

    :param lines: Sequence of lines to process

    :type lines: Iterator[str]

    :param skip_comments: Skip over lines with leading # characters.
      Default, True

    :type skip_comments: bool, optional

    :rtype: List[str]
    """

    if skip_comments:
        lines = (l.split('#', 1)[0].strip() for l in lines)
    else:
        lines = (l.strip() for l in lines)
    return [l for l in lines if l]


def read_clean_lines(filename="-", skip_comments=True):
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

    :type filename: str, optional

    :param skip_comments: Skip over lines with leading # characters.
      Default, True

    :type skip_comments: bool, optional

    :rtype: list[str]
    """

    if not filename:
        return []

    elif filename == "-":
        return clean_lines(sys.stdin)

    else:
        with open(filename, "rt") as fin:
            return clean_lines(fin)


printerr = partial(print, file=sys.stderr)


def tabulate(headings, data, key=None, sorting=0,
             quiet=None, out=None):
    """
    Prints tabulated data, with the given headings.

    This function is not resilient -- the headings and data must have
    the same count of rows, nothing will inject empty values.

    Output will be configured to set the columns to their maximum
    width necessary for the longest value from all the rows or the
    heading.

    :param headings: The column titles

    :type headings: list[str]

    :param data: Rows of data

    :type data: list

    :param key: Transformation to apply to each row of data to get the
      actual individual columns. Should be a unary function. Default,
      data is iterated as-is.

    :type key: Callable[[object], object]

    :param sorting: Whether data rows should be sorted and in what
      direction. 0 for no sorting, 1 for ascending, -1 for
      descending. If key is specified, then sorting will be based on
      those transformations. Default, no sorting.

    :type sorting: int, optional

    :param quiet: Whether to print headings or not. Default, only print
      headings if out is a TTY device.

    :type quiet: bool, optional

    :param out: Stream to write output to. Default, `sys.stdout`

    :type out: io.TextIOBase, optional

    :rtype: None
    """

    if out is None:
        out = sys.stdout

    # The quiet setting has three values. True meaning no header,
    # False meaning header, and None meaning no header if out is not a
    # TTY.
    if quiet is None:
        quiet = not out.isatty()

    # convert data to a list, and apply the key if necessary to find
    # the real columns
    if key:
        data = (key(row) for row in data)

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
    # column plus some spacing. Note that python 2.6 mandates the
    # field index be specified, so we MUST use enumerate here.
    fmt = "  ".join("{%i:<%i}" % iw for iw in enumerate(widths))

    if headings and not quiet:
        print(fmt.format(*headings), file=out)
        print("  ".join(("-" * h) for h in widths), file=out)

    for row in data:
        print(fmt.format(*row), file=out)


def space_normalize(txt):
    lines = (t.strip() for t in txt.split())
    return " ".join(t for t in lines if t)


@add_metaclass(ABCMeta)
class SmokyDingo(object):
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

      * the `SmokyDingo.handle` method invokes the actual work of the
        sub-command
    """

    group = "misc"
    description = "A CLI Plugin"

    # set of permission names that can grant use of this command. None
    # or empty for anonymous access. Checked in pre_handle
    permission = None


    def __init__(self, name):
        self.name = name

        # this is used to register the command with koji in a manner
        # that it expects to deal with
        self.__name__ = "handle_" + name.replace("-", "_")

        # this is necessary for koji to recognize us as a cli command.
        # We only set this on instances, not on the class itself,
        # because it is only the instances which should be used that
        # way.
        self.exported_cli = True

        # allow a docstr to be specified on subclasses, but if absent
        # let's set it based on the group and description.
        if getattr(self, "__doc__", None) is None:
            desc = space_normalize(self.description)
            self.__doc__ = "[%s] %s" % (self.group, desc)
        else:
            desc = space_normalize(self.__doc__)
            if not desc.startswith("["):
                desc = "[%s] %s" % (self.group, desc)
            self.__doc__ = desc

        # these will be populated once the command instance is
        # actually called
        self.goptions = None
        self.session = None


    def parser(self):
        invoke = " ".join((basename(sys.argv[0]), self.name))
        argp = ArgumentParser(prog=invoke, description=self.description)
        return self.arguments(argp) or argp


    def arguments(self, parser):
        """
        Override to add relevant arguments to the given parser instance.
        May return an alternative parser instance or None.
        """

        pass


    def validate(self, parser, options):
        """
        Override to perform validation on options values. Return value is
        ignored, use parser.error if needed.
        """

        pass


    def pre_handle(self, options):
        """
        Verify necessary permissions are in place before attempting any
        further calls.
        """

        if self.permission:
            session = self.session
            userinfo = session.getLoggedInUser()
            userperms = session.getUserPerms(userinfo["id"]) or ()

            if not (self.permission in userperms or "admin" in userperms):
                msg = "Insufficient permissions for command %s" % self.name
                raise NotPermitted(msg)


    @abstractmethod
    def handle(self, options):
        """
        Perform the full set of actions for this command.
        """

        pass


    def activate(self):
        """
        Activate our session. This is triggered after validate, before
        pre_handle and handle

        The session and goptions attributes will have been set just
        prior.
        """

        return activate_session(self.session, self.goptions)


    def deactivate(self):
        """
        Deactivate our session. This is triggered after handle has
        completed, either normally or by raising an exception.

        The session and goptions attributes will be cleared just
        after.
        """

        try:
            self.session.logout()
        finally:
            pass


    def __call__(self, goptions, session, args):
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


class AnonSmokyDingo(SmokyDingo):
    """
    A SmokyDingo which upon activation will connect to koji hub, but
    will not authenticate. This means only hub RPC endpoints which do
    not enforce require some permission will work. This is normal for
    many information-only endpoints.
    """

    group = "info"
    permission = None


    def __init__(self, name):
        super(AnonSmokyDingo, self).__init__(name)

        # koji won't even bother fully authenticating our session for
        # this command if we tweak the name like this. Since
        # subclasses of this are meant to be anonymous commands
        # anyway, we may as well omit the session init
        self.__name__ = "anon_handle_" + self.name.replace("-", "_")


    def activate(self):
        # rather than logging on, we only open a connection
        ensure_connection(self.session)


    def pre_handle(self, options):
        # do not check permissions at all, we won't be logged in
        pass


class AdminSmokyDingo(SmokyDingo):
    """
    A SmokyDingo which checks for the 'admin' permission after
    activation.
    """

    group = "admin"
    permission = "admin"


class TagSmokyDingo(SmokyDingo):
    """
    A SmokyDingo which checks for the 'tag' or 'admin' permission after
    activation.
    """

    group = "admin"
    permission = "tag"


class TargetSmokyDingo(SmokyDingo):
    """
    A SmokyDingo which checks for the 'target' or 'admin' permission
    after activation.
    """

    group = "admin"
    permission = "target"


class HostSmokyDingo(SmokyDingo):
    """
    A SmokyDingo which checks for the 'host' or 'admin' permisson
    after activation.
    """

    group = "admin"
    permission = "host"


#
# The end.
