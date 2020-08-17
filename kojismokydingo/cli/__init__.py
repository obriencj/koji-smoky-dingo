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


def pretty_json(data, output=sys.stdout, pretty=JSON_PRETTY_OPTIONS):
    """
    Presents JSON in a pretty way.
    """

    dump(data, output, **pretty)
    print(file=output)


def resplit(arglist, sep=","):
    """
    Collapses comma-separated and multi-specified items into a single
    list. Useful with action="append" in an argparse argument.

    this allows arguments like:
    -x 1 -x 2, -x 3,4,5 -x ,6,7, -x 8

    to become
    x = [1, 2, 3, 4, 5, 6, 7, 8]
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

    :rtype: list[str]
    """

    if skip_comments:
        lines = (l.split('#', 1)[0].strip() for l in lines)
    else:
        lines = (l.strip() for l in lines)
    return [l for l in lines if l]


def read_clean_lines(filename="-", skip_comments=True):
    """
    Reads clean lines from a named file. If filename is '-' then read
    from sys.stdin instead.

    Each line will be stripped of leading and trailing whitespace.

    If skip_comments is True (the default), then any line with a
    leading hash ('#') will be considered a comment and omitted from
    the output.

    Content will be fully collected into a list and the file (if not
    sys.stdin) will be closed before returning.

    :param filename: File name to read lines from, or - to indicate
    stdin. Default, -
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


def columns(data):
    if data:
        for c in range(0, len(data[0])):
            yield (row[c] for row in data)


def tabulate(headings, data, quiet=None, key=None, out=sys.stdout):
    if quiet is None:
        quiet = not out.isatty()

    if key:
        data = [key(row) for row in data]
    else:
        data = list(data)

    if data:
        widths = [max(len(str(v)) for v in col)
                  for col in columns(data)]
    else:
        widths = []

    if headings and not quiet:
        widths = [max(w or 0, len(h or "")) for w, h in
                  zip_longest(widths, headings)]

    fmt = "  ".join("{:<%i}" % w for w in widths)

    if headings and not quiet:
        headings = [(h or "") for w, h in
                    zip_longest(widths, headings)]

        print(fmt.format(*headings), file=out)
        print("  ".join(("-" * h) for h in widths), file=out)

    for row in data:
        print(fmt.format(*row), file=out)


@add_metaclass(ABCMeta)
class SmokyDingo(object):
    """
    Base class for new sub-commands in Koji. Subclasses may be
    referenced via an entry point under the koji_smoky_dingo group to
    be loaded at runtime by the kojismokydingometa Koji client plugin.

    Summary:
    * kojismokydingometa installed in koji_cli_plugins loads when koji
      client launches
    * the meta plugin loads all koji_smoky_dingo entry points
    * each entry point name is a command name, and the reference should
      resolve to a subclass of SmokyDingo
    * each entry point is instantiated, and provided to the koji cli as
      a new sub-command
    * if the sub-command is invoked, then the SmokyDingo instance is
      called, this triggers the following:
    ** the SmokyDingo.parser method provides additional argument
       parsing
    ** the SmokyDingo.validate method provides a chance to validate
       and/or manipulate the parsed arguments
    ** the SmokyDingo.activate method authenticates with the hub
    ** the SmokyDingo.handle method invokes the actual work of the
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

        # this is necessary for koji to recognize us as a cli command
        self.exported_cli = True

        # allow a docstr to be specified on subclasses, but if absent
        # let's set it based on the group and description.
        if getattr(self, "__doc__", None) is None:
            self.__doc__ = "[%s] %s" % (self.group, self.description)

        # these will be populated once the command instance is
        # actually called
        self.goptions = None
        self.session = None


    def parser(self):
        """
        Override to provide an ArgumentParser instance with all the
        relevant positional arguments and options added.
        """

        invoke = " ".join((basename(sys.argv[0]), self.name))
        return ArgumentParser(prog=invoke, description=self.description)


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
        Activate the session
        """

        return activate_session(self.session, self.goptions)


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
