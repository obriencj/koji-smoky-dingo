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

from . import SmokyDingo, NoSuchUser


PRETTY_OPTIONS = {
    "indent": 4,
    "separators": (",", ": "),
    "sort_keys": True,
}


USER_NORMAL = 0
USER_HOST = 1
USER_GROUP = 2

STATUS_NORMAL = 0
STATUS_BLOCKED = 1


def collect_userinfo(session, user):
    userinfo = session.getUser(user)

    if userinfo is None:
        raise NoSuchUser(user)

    uid = userinfo["id"]

    perms = session.getUserPerms(uid)
    userinfo["permissions"] = perms

    if userinfo.get("usertype", USER_NORMAL) == USER_GROUP:
        try:
            userinfo["members"] = session.getGroupMembers(uid)
        except Exception:
            # non-admin accounts cannot query group membership, so omit
            userinfo["members"] = None

    return userinfo


def get_usertype_str(userinfo):
    val = userinfo.get("usertype", 0) or 0
    if val == USER_NORMAL:
        return "NORMAL (user)"
    elif val == USER_HOST:
        return "HOST (builder)"
    elif val == USER_GROUP:
        return "GROUP"
    else:
        return "Unknown (%i)" % val


def get_userstatus_str(userinfo):
    val = userinfo.get("userstatus", STATUS_NORMAL) or STATUS_NORMAL
    if val == STATUS_NORMAL:
        return "NORMAL (enabled)"
    elif val == STATUS_BLOCKED:
        return "BLOCKED (disabled)"
    else:
        return "Unknown (%i)" % val


def cli_userinfo(session, user, json=False):

    userinfo = collect_userinfo(session, user)

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
        for member in sorted(members, key=lambda m: m.get("name")):
            print(" {name} [{id}]".format(**member))


class cli(SmokyDingo):

    group = "info"
    description = "Show information about a user"


    def parser(self):
        parser = super(cli, self).parser()
        addarg = parser.add_argument

        addarg("user", action="store", metavar="USER",
               help="User name or principal")

        addarg("--json", action="store_true", default=False,
               help="Output information as JSON")

        return parser


    def handle(self, options):
        return cli_userinfo(self.session, options.user,
                            options.json)


#
# The end.
