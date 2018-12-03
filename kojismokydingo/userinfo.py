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
Koji Smoki Dingo - info command userinfo

Get information about a user or kerberos principal from brew

:author: cobrien@redhat.com
:license: GPL version 3
"""


from __future__ import print_function

import sys

from json import dump

from . import AnonSmokyDingo, NoSuchUser


PRETTY_OPTIONS = {
    "indent": 4,
    "separators": (",", ": "),
    "sort_keys": True,
}


def collect_userinfo(session, user):
    userinfo = session.getUser(user)

    if userinfo is None:
        raise NoSuchUser(user)

    uid = userinfo["id"]

    perms = session.getUserPerms(uid)
    userinfo["permissions"] = perms

    if userinfo.get("usertype", 0) == 3:
        members = session.getGroupMembers(uid)
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


def cli_userinfo(session, name, json=False):

    userinfo = collect_userinfo(session, options.user)

    if json:
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


class cli(AnonSmokyDingo):

    description = "Show information about a user"


    def parser(self):
        parser = super(cli, self).parser()
        addarg = ap.add_argument

        addarg("user", action="store", metavar="USER",
               help="User name or principal")

        addarg("--json", action="store_true", default=False,
               help="Output information as JSON")

        return parser


    def handle(self, options):
        return cli_userinfo(options.session, options.user,
                            options.json)


#
# The end.
