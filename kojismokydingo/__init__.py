

from __future__ import print_function

from functools import partial

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


def handle_cli(parser_factory, goptions, session, args):
    parser = parser_factory()
    options = parser.parse_args(args)

    options.session = session
    options.goptions = goptions

    try:
        activate_session(session, goptions)
        return options.cli(options) or 0

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


def produce_handler(parser_factory):
    handler = partial(handle_cli, parser_factory)
    update_wrapper(handler, parser_factory)
    return export_cli(handler)


#
# The end.
