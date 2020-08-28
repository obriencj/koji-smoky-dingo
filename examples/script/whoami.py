#! /usr/bin/env python


from __future__ import print_function

from argparse import ArgumentParser
from koji import GenericError
from kojismokydingo import BadDingo, ManagedClientSession
from kojismokydingo.cli import pretty_json, printerr
from kojismokydingo.cli.users import get_usertype_str, get_userstatus_str
from kojismokydingo.users import collect_userinfo
from os.path import basename

import sys


DESCRIPTION = """
Print information about the currently logged-in Koji user.
"""


def cli_argparser(progname):
    parser = ArgumentParser(prog=basename(progname),
                            description=DESCRIPTION.strip())

    parser.add_argument("--profile", action="store", default="koji",
                        help="Koji profile to use. Default: koji")

    parser.add_argument("--json", action="store_true", default=False,
                        help="Output as JSON")

    return parser


def cli_whoami(options):
    with ManagedClientSession(options.profile) as session:
        myinfo = session.getLoggedInUser()
        collect_userinfo(session, myinfo)

    if options.json:
        pretty_json(myinfo)
        return

    print("User: {name} [{id}]".format(**myinfo))

    krb_princs = myinfo.get("krb_principals", None)
    if krb_princs:
        print("Kerberos principals:")
        for kp in sorted(krb_princs):
            print(" ", kp)

    print("Type:", get_usertype_str(myinfo))
    print("Status:", get_userstatus_str(myinfo))

    perms = myinfo.get("permissions", None)
    if perms:
        print("Permissions:")
        for perm in sorted(perms):
            print(" ", perm)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = cli_argparser(argv[0])
    options = parser.parse_args(argv[1:])

    try:
        return cli_whoami(options) or 0

    except KeyboardInterrupt:
        printerr()
        return 130

    except BadDingo as bad:
        printerr(bad)
        return 1

    except GenericError as bad:
        printerr(bad)
        return 1


if __name__ == "__main__":
    sys.exit(main())


# The end.
