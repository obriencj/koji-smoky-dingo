#! /usr/bin/env python2

"""
Get information about a user or kerberos principal from brew

author: cobrien@redhat.com
"""


from __future__ import print_function

from argparse import ArgumentParser
from functools import partial
from json import dump
from socket import gaierror
from xmlrpc.client import Fault, ServerProxy

import sys


BREW_SERVICE = "https://brewhub.engineering.redhat.com/brewhub"


PRETTY_OPTIONS = {
    "indent": 4,
    "separators": (",", ": "),
    "sort_keys": True,
}


class NoSuchUser(Exception):
    pass


def collect_userinfo(brewhub, user):
    userinfo = brewhub.getUser(user)

    if userinfo is None:
        raise NoSuchUser(user)

    uid = userinfo["id"]

    perms = brewhub.getUserPerms(uid)
    userinfo["permissions"] = perms

    if userinfo.get("usertype", 0) == 3:
        members = brewhub.getGroupMembers(uid)
        userinfo["members"] = members

    return userinfo


def get_usertype_str(userinfo):
    val = userinfo.get("usertype", 0) or 0
    if val == 0:
        return "NORMAL (user)"
    elif val == 1:
        return "HOST (builder)"
    elif val == 2:
        return "GROUP"
    else:
        return "Unknown (%i)" % val


def get_userstatus_str(userinfo):
    val = userinfo.get("userstatus", 0) or 0
    if val == 0:
        return "NORMAL (enabled)"
    elif val == 1:
        return "BLOCKED (disabled)"
    else:
        return "Unknown (%i)" % val


def cli(options):

    brewhub = ServerProxy(options.brewhub, allow_none=True)
    userinfo = collect_userinfo(brewhub, options.user)

    if options.json:
        dump(userinfo, sys.stdout, **PRETTY_OPTIONS)
        print()
        return

    print("User: {name} [{id}]".format(**userinfo))

    krb = userinfo.get("krb_principal", None)
    if krb:
        print("Kerberos principal:", krb)

    print("Type:", get_usertype_str(userinfo))
    print("Status:", get_userstatus_str(userinfo))

    perms = userinfo.get("permissions", None)
    if perms:
        print("Permissions:")
        for perm in sorted(perms):
            print(" ", perm)

    members = userinfo.get("members", None)
    if members:
        print("Members:")
        for member in sorted(members):
            print(" ", member)


def create_argparser(called_by):
    ap = ArgumentParser(prog=called_by,
                        description="Get information about a brew user")

    arg = ap.add_argument

    arg("--brewhub", action="store", default=BREW_SERVICE,
        help="URI for the brewhub service")

    arg("--json", action="store_true", default=False,
        help="Output information as JSON")

    arg("user", action="store",
        help="User name or principal")

    return ap


def main(args=None):

    if args is None:
        args = sys.argv

    called_by = sys.argv[0]
    args = sys.argv[1:]

    parser = create_argparser(called_by)
    options = parser.parse_args(args)

    printerr = partial(print, file=sys.stderr)

    try:
        cli(options)

    except KeyboardInterrupt:
        printerr()
        return 130

    except Fault as xmlf:
        printerr(xmlf.faultString)
        return -1

    except gaierror as dns:
        printerr(dns)
        printerr("Try using --brewhub with an IP address")
        return -2

    except NoSuchUser as nsu:
        printerr("No such user:", nsu)
        return -4

    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())


#
# The end.
