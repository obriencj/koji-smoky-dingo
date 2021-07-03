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


from operator import itemgetter

from . import AnonSmokyDingo, int_or_str, pretty_json
from ..types import UserStatus, UserType
from ..users import (
    collect_cgs, collect_perminfo, collect_userinfo, )


__all__ = (
    "CGInfo",
    "PermissionInfo",
    "UserInfo",

    "cli_cginfo",
    "cli_perminfo",
    "cli_userinfo",
    "get_userstatus_str",
    "get_usertype_str",
)


def get_usertype_str(userinfo):
    """
    Provide a human-readable label for the koji user type enum value
    in a koji user info dict.

    :param userinfo: user info
    :type userinfo: dict

    :rtype: str
    """

    val = userinfo.get("usertype") or UserType.Normal

    if val == UserType.NORMAL:
        return "NORMAL (user)"
    elif val == UserType.HOST:
        return "HOST (builder)"
    elif val == UserType.GROUP:
        return "GROUP"
    else:
        return "Unknown (%i)" % val


def get_userstatus_str(userinfo):
    """
    Provide a human-readable label for the koji user status enum value
    in a koji user info dict.

    :param userinfo: user info
    :type userinfo: dict

    :rtype: str
    """

    val = userinfo.get("status") or UserStatus.NORMAL
    if val == UserStatus.NORMAL:
        return "NORMAL (enabled)"
    elif val == UserStatus.BLOCKED:
        return "BLOCKED (disabled)"
    else:
        return "Unknown (%i)" % val


def cli_userinfo(session, user, json=False):
    """
    Implements the ``koji userinfo`` command
    """

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
            print(" {name} [{id}]".format(**cg))

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


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("user", action="store", type=int_or_str, metavar="USER",
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
    """
    Implements the ``koji perminfo`` command
    """

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


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("permission", action="store", metavar="PERMISSION",
               type=int_or_str,
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


def cli_cginfo(session, name=None, json=False):
    """
    Implements the ``koji cginfo`` command
    """

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


class CGInfo(AnonSmokyDingo):

    description = "List content generators and their users"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("--name", action="store", default=None,
               help="Only show the given content generator")

        addarg("--json", action="store_true", default=False,
               help="Output information as JSON")

        return parser


    def handle(self, options):
        return cli_cginfo(self.session,
                          name=options.name,
                          json=options.json)


#
# The end.
