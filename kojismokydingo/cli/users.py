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
Koji Smoky Dingo - CLI User Commands

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from __future__ import print_function

from operator import itemgetter

from . import AnonSmokyDingo, pretty_json
from ..users import (
    USER_NORMAL, USER_HOST, USER_GROUP,
    STATUS_NORMAL, STATUS_BLOCKED,
    collect_cgs, collect_perminfo, collect_userinfo)


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
    val = userinfo.get("status", STATUS_NORMAL) or STATUS_NORMAL
    if val == STATUS_NORMAL:
        return "NORMAL (enabled)"
    elif val == STATUS_BLOCKED:
        return "BLOCKED (disabled)"
    else:
        return "Unknown (%i)" % val


def cli_userinfo(session, user, json=False):

    userinfo = collect_userinfo(session, user)

    if json:
        pretty_json(userinfo)
        return

    print("User: {name} [{id}]".format(**userinfo))

    krb_princs = userinfo.get("krb_principals", None)
    if krb_princs:
        print("Kerberos principals:")
        for kp in sorted(krb_princs):
            print(" ", kp)

    print("Type:", get_usertype_str(userinfo))
    print("Status:", get_userstatus_str(userinfo))

    cgs = userinfo.get("content_generators", None)
    if cgs:
        print("Content generators:")
        for cg in sorted(cgs):
            print(" ", cg)

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


class UserInfo(AnonSmokyDingo):

    group = "info"
    description = "Show information about a user"


    def parser(self):
        parser = super(UserInfo, self).parser()
        addarg = parser.add_argument

        addarg("user", action="store", metavar="USER",
               help="User name or principal")

        addarg("--json", action="store_true", default=False,
               help="Output information as JSON")

        return parser


    def handle(self, options):
        return cli_userinfo(self.session, options.user,
                            json=options.json)


def cli_perminfo(session, permission,
                 verbose=False, by_date=False,
                 json=False):

    perminfo = collect_perminfo(session, permission)

    if json:
        pretty_json(perminfo)
        return

    print("Permission: {name} [{id}]".format(**perminfo))

    users = perminfo["users"]
    if users:
        print("Users:")
        if verbose:
            fmt = "  {user_name} [by {creator_name} on {create_date}]"
        else:
            fmt = "  {user_name}"

        orderkey = itemgetter("create_event" if by_date else "user_name")
        for user in sorted(users, key=orderkey):
            print(fmt.format(**user))


class PermissionInfo(AnonSmokyDingo):

    description = "Show information about a permission"


    def parser(self):
        parser = super(PermissionInfo, self).parser()
        addarg = parser.add_argument

        addarg("permission", action="store", metavar="PERMISSION",
               help="Name of permission")

        addarg("--verbose", "-v", action="store_true", default=False,
               help="Also show who granted the permission and when")

        addarg("--by-date", "-d", action="store_true", default=False,
               help="Sory users by date granted. Otherwise, sort by name")

        addarg("--json", action="store_true", default=False,
               help="Output information as JSON")

        return parser


    def handle(self, options):
        return cli_perminfo(self.session, options.permission,
                            verbose=options.verbose,
                            by_date=options.by_date,
                            json=options.json)


def cli_list_cgs(session, name=None, json=False):

    cgs = collect_cgs(session, name=name)

    if json:
        pretty_json(cgs)
        return

    for cginfo in sorted(cgs, key=itemgetter("id")):
        print("Content generator: {name} [{id}]".format(**cginfo))

        users = cginfo.get("users")
        if users:
            print("Users:")
            for user in sorted(users):
                print(" ", user)

        print()


class ListCGs(AnonSmokyDingo):

    description = "List content generators and their users"


    def parser(self):
        parser = super(ListCGs, self).parser()
        addarg = parser.add_argument

        addarg("--name", action="store", default=None,
               help="Only show the given content generator")

        addarg("--json", action="store_true", default=False,
               help="Output information as JSON")

        return parser


    def handle(self, options):
        return cli_list_cgs(self.session,
                            name=options.name,
                            json=options.json)


#
# The end.
