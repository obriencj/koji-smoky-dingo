# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.


from __future__ import print_function

import sys

from functools import partial
from koji import GenericError
from koji.plugin import export_cli
from koji_cli.lib import activate_session


class NoSuchTag(Exception):
    pass


class NoSuchBuild(Exception):
    pass


class NoSuchUser(Exception):
    pass


class PermissionException(Exception):
    pass


printerr = partial(print, file=sys.stderr)


def int_range(start, stop=None):
    """
    For use as a type in an ArgumentParser argument, raises a
    TypeError if the given integer argument is not within the start
    and stop values provided
    """

    errname = "int (out of range start=%i, stop=%i)" % (start, stop)

    def rint(val):
        rint.__name__ = "int"
        val = int(val)

        if start < val <= stop:
            return val
        else:
            rint.__name__ = errname
            raise TypeError(val)

    return rint


def handle_cli(name, parser_factory, handler_fn, goptions, session, args):
    """
    Helper function which is used by koji_cli_plugin and
    koji_anon_cli_plugin to combine a command name, an option parser
    factory, and a handler function with the parameters passed by koji
    to command handlers.

    This function will create the parser using the given name, parse the
    arguments from the koji cli invocation, activate the session using
    the global options, and then invoke the handler_fn.

    A number of basic exception types are caught by default, providing
    polite output and a return code, but without a traceback.
    """

    parser = parser_factory(name)
    options = parser.parse_args(args)

    options.session = session
    options.goptions = goptions

    try:
        activate_session(session, goptions)
        return handler_fn(options) or 0

    except KeyboardInterrupt:
        print(file=sys.stderr)
        return 130

    except GenericError as kge:
        printerr(kge)
        return -1

    except PermissionException as perms:
        printerr("Insufficient permissions:", perms)
        return -2

    except NoSuchTag as nst:
        printerr("No such tag:", nst)
        return -3

    except NoSuchBuild as nsb:
        printerr("No such build:", nsb)
        return -4

    except NoSuchUser as nsu:
        printerr("No such user:", nsu)
        return -5


def koji_cli_plugin(parser_factory, cli_fn):
    """
    Helper to combine a function that creates an ArgumentParser with a
    function to handle the parsed args, and produce a unary function
    that takes its invocation name to produce a koji cli handler
    function.

    :parser_factory: unary function accepting the name of the command as
    invoked. Should return an ArgumentParser instance

    :cli_fn: unary function accepting an options object as produced by
    the parser_factor's parser.

    :return: partial combining the handler_cli function, the name, the
    parser_factory, and the cli_fn. Will be marked as a cli command
    handler for koji, and will present a name appropriate for the koji
    cli.
    """

    def cli_plugin(name):
        wonkyname = "handle_%s" % name.replace("-", "_")

        handler = partial(handle_cli, name, parser_factory, cli_fn)
        handler.__doc__ = parser_factory.__doc__.strip()
        handler.__name__ = wonkyname
        handler.export_alias = wonkyname

        return export_cli(handler)

    return cli_plugin


def koji_anon_cli_plugin(parser_factory, cli_fn):
    """
    Helper to combine a function that creates an ArgumentParser with a
    function to handle the parsed args, and produce a unary function
    that takes its invocation name to produce a koji cli handler
    function.

    Identical to koji_cli_plugin but the session will not be
    authenticated.

    :parser_factory: unary function accepting the name of the command as
    invoked. Should return an ArgumentParser instance

    :cli_fn: unary function accepting an options object as produced by
    the parser_factor's parser.

    :return: partial combining the handler_cli function, the name, the
    parser_factory, and the cli_fn. Will be marked as a cli command
    handler for koji, and will present a name appropriate for the koji
    cli.
    """

    def anon_cli_plugin(name):
        wonkyname = "anon_handle_%s" % name.replace("-", "_")

        handler = partial(handle_cli, name, parser_factory, cli_fn)
        handler.__doc__ = parser_factory.__doc__.strip()
        handler.__name__ = wonkyname
        handler.export_alias = wonkyname

        return export_cli(handler)

    return anon_cli_plugin


#
# The end.
