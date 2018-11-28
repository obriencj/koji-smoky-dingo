

from __future__ import print_function

from functools import partial
from koji import GenericError
from koji.plugin import export_cli
from koji_cli.lib import activate_session

import sys


class NoSuchTag(Exception):
    pass


class NoSuchBuild(Exception):
    pass


class NoSuchUser(Exception):
    pass


class PermissionException(Exception):
    pass


printerr = partial(print, file=sys.stderr)


def handle_cli(parser_factory, handler_fn, goptions, session, args):
    parser = parser_factory()
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
    def cli_plugin(name):
        wonkyname = "handle_%s" % name

        handler = partial(handle_cli, parser_factory, cli_fn)
        handler.__doc__ = parser_factory.__doc__.strip()
        handler.__name__ = wonkyname
        handler.export_alias = wonkyname

        return export_cli(handler)

    return cli_plugin


def koji_anon_cli_plugin(parser_factory, cli_fn):
    def anon_cli_plugin(name):
        wonkyname = "anon_handle_%s" % name

        handler = partial(handle_cli, parser_factory, cli_fn)
        handler.__doc__ = parser_factory.__doc__.strip()
        handler.__name__ = wonkyname
        handler.export_alias = wonkyname

        return export_cli(handler)

    return anon_cli_plugin


#
# The end.
