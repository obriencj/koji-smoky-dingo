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


from koji import ClientSession
from operator import itemgetter
from typing import Optional, Union

from . import AnonSmokyDingo, int_or_str, pretty_json
from ..types import (
    AuthType, TaskState, UserInfo, UserSpec, UserStatus, UserType, )
from ..users import (
    collect_cgs, collect_perminfo, collect_userinfo, )


__all__ = (
    "ShowCGInfo",
    "ShowPermissionInfo",
    "ShowUserInfo",

    "cli_cginfo",
    "cli_perminfo",
    "cli_userinfo",
    "get_userauth_str",
    "get_userstatus_str",
    "get_usertype_str",
)


def get_usertype_str(userinfo: UserInfo) -> str:
    """
    Provide a human-readable label for the koji user type enum value
    in a koji user info dict.

    :param userinfo: user info

    :since: 1.0
    """

    val = userinfo.get("usertype") or UserType.NORMAL

    if val == UserType.NORMAL:
        return "NORMAL (user)"
    elif val == UserType.HOST:
        return "HOST (builder)"
    elif val == UserType.GROUP:
        return "GROUP"
    else:
        return f"Unknown ({val})"


def get_userstatus_str(userinfo: UserInfo) -> str:
    """
    Provide a human-readable label for the koji user status enum value
    in a koji user info dict.

    :param userinfo: user info

    :since: 1.0
    """

    val = userinfo.get("status") or UserStatus.NORMAL
    if val == UserStatus.NORMAL:
        return "NORMAL (enabled)"
    elif val == UserStatus.BLOCKED:
        return "BLOCKED (disabled)"
    else:
        return f"Unknown ({val})"


def get_userauth_str(userinfo: UserInfo) -> Optional[str]:
    """
    Provide a human-readable label for the koji auth type enum value
    in a koji user info dict. Returns None if the auth

    :param userinfo: user info

    :since: 2.0
    """

    val = userinfo.get("authtype")
    if val is None:
        return None
    elif val == AuthType.GSSAPI:
        return "GSSAPI"
    elif val == AuthType.KERB:
        return "Kerberos ticket"
    elif val == AuthType.NORMAL:
        return "Password"
    elif val == AuthType.SSL:
        return "SSL certificate"
    else:
        return f"Unknown ({val})"


def cli_userinfo(
        session: ClientSession,
        user: UserSpec,
        stats: bool = False,
        json: bool = False):
    """
    Implements the ``koji userinfo`` command

    :param session: an active koji client session

    :param user: user specification to output information about

    :param stats: include simple user stats

    :param json: produce JSON output

    :raises NoSuchUser: if the user specification doesn't correlate to
      a known user

    :since: 1.0
    """

    userinfo = collect_userinfo(session, user, stats)

    if json:
        pretty_json(userinfo)
        return

    print(f"User: {userinfo['name']} [{userinfo['id']}]")

    auth = get_userauth_str(userinfo)
    if auth:
        print("Authentication method:", auth)

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
        for cg in sorted(cgs, key=itemgetter("name")):
            print(f"{cg['name']} [{cg['id']}]")

    perms = userinfo.get("permissions", None)
    if perms:
        print("Permissions:")
        for perm in sorted(perms):
            print(" ", perm)

    members = userinfo.get("members", None)
    if members:
        print("Members:")
        for member in sorted(members, key=lambda m: m.get("name")):
            print(f"{member['name']} [{member['id']}]")

    data = userinfo.get("statistics", None)
    if data:
        print("Statistics:")
        print(" Owned packages:", data.get("package_count", 0))
        print(" Submitted tasks:", data.get("task_count", 0))
        print(" Created builds:", data.get("build_count", 0))

        tdat = data.get("last_task")
        if tdat:
            print(f" Last task: {tdat['method']} [{tdat['id']}]"
                  f" {tdat['create_time'].split('.')[0]}")

        bdat = data.get("last_build")
        if bdat:
            print(f" Last build: {bdat['nvr']} [{bdat['build_id']}]"
                  f" {bdat['creation_time'].split('.')[0]}")


class ShowUserInfo(AnonSmokyDingo):

    group = "info"
    description = "Show information about a user"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("user", action="store", type=int_or_str, metavar="USER",
               help="User name or principal")

        addarg("--stats", action="store_true", default=False,
               help="Include user statistics")

        addarg("--json", action="store_true", default=False,
               help="Output information as JSON")

        return parser


    def handle(self, options):
        return cli_userinfo(self.session, options.user,
                            stats=options.stats,
                            json=options.json)


def cli_perminfo(
        session: ClientSession,
        permission: str,
        verbose: bool = False,
        by_date: bool = False,
        json: bool = False):
    """
    Implements the ``koji perminfo`` command

    :param session: an active koji client session

    :param permission: the permission name to display information about

    :param verbose: also display who granted the permission and when

    :param by_date: sort the user list by the date they were granted the
      permission

    :param json: output the data as JSON

    :since: 1.0
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


class ShowPermissionInfo(AnonSmokyDingo):

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


def cli_cginfo(
        session: ClientSession,
        name: Optional[str] = None,
        json: bool = False):
    """
    Implements the ``koji cginfo`` command

    :param session: an active koji client session

    :param name: only display information about the content generator with
      this name

    :param json: output the data as JSON

    :since: 1.0
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


class ShowCGInfo(AnonSmokyDingo):

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
