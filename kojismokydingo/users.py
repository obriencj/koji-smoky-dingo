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
Koji Smoki Dingo - users and permissions

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from koji import ClientSession, ParameterError
from operator import itemgetter
from time import asctime, localtime
from typing import List, Optional, Union, cast

from . import NoSuchContentGenerator, NoSuchPermission, as_userinfo
from .types import (
    CGInfo, DecoratedPermInfo, DecoratedUserInfo, NamedCGInfo,
    PermSpec, PermUser, UserInfo, UserSpec, UserStatistics, UserType, )


__all__ = (
    "collect_cg_access",
    "collect_cgs",
    "collect_perminfo",
    "collect_userinfo",
    "collect_userstats",
)


def collect_userstats(
        session: ClientSession,
        user: UserSpec) -> UserStatistics:

    """
    Collects user statistics into a dict

    :param session: an active koji client session

    :param user: name of a user or their kerberos ID

    :raises NoSuchUser: if user is an ID or name which cannot be
      resolved

    :since: 2.0
    """

    userinfo = as_userinfo(session, user)

    with session.multicall() as mc:  # type: ignore
        calls = (
            ('build_count',
             mc.listBuilds(userID=userinfo['id'],
                           queryOpts={'countOnly': True})),

            ('last_build',
             mc.listBuilds(userID=userinfo['id'],
                           queryOpts={'limit': 1, 'order': '-build_id'})),

            ('package_count',
             mc.listPackages(userID=userinfo['id'], with_dups=True,
                             queryOpts={'countOnly': True})),

            ('task_count',
             mc.listTasks(opts={'owner': userinfo['id'], 'parent': None},
                          queryOpts={'countOnly': True})),

            ('last_task',
             mc.listTasks(opts={'owner': userinfo['id'], 'parent': None},
                          queryOpts={'limit': 1, 'order': '-id'})),
        )

    stats = {k: v.result for k, v in calls}

    # unwrap the last_build
    lst = stats['last_build']
    if lst:
        stats['last_build'] = lst[0]
    else:
        stats['last_build'] = None

    # and also the last_task
    lst = stats['last_task']
    if lst:
        stats['last_task'] = lst[0]
    else:
        stats['last_task'] = None

    return cast(UserStatistics, stats)


def collect_userinfo(
        session: ClientSession,
        user: UserSpec,
        stats: bool = True) -> DecoratedUserInfo:
    """
    Gather information about a named user, including the list of
    permissions the user has.

    Will convert the older `'krb_principal'` value (koji < 1.19) into
    a `'krb_principals'` list (koji >= 1.19) to provide some level of
    uniformity.

    :param session: an active koji client session

    :param user: name of a user or their kerberos ID

    :raises NoSuchUser: if user is an ID or name which cannot be
      resolved

    :since: 1.0
    """

    userinfo = cast(DecoratedUserInfo, as_userinfo(session, user))

    # depending on koji version, getUser resulted in either a
    # krb_principal or krb_principals entry (or neither if it's not
    # set up for kerberos). Let's normalize on the newer
    # krb_principals one by converting. See
    # https://pagure.io/koji/issue/1629

    if "krb_principal" in userinfo:
        krb = userinfo["krb_principal"]
        userinfo["krb_principals"] = [krb] if krb else []

    uid = userinfo["id"]

    userinfo["permissions"] = session.getUserPerms(uid)
    userinfo["content_generators"] = collect_cg_access(session, userinfo)

    ut = userinfo.get("usertype", UserType.NORMAL)
    if ut == UserType.NORMAL:
        if stats:
            userinfo["statistics"] = collect_userstats(session, userinfo)

    elif ut == UserType.GROUP:
        try:
            userinfo["members"] = session.getGroupMembers(uid)
        except Exception:
            # non-admin accounts cannot query group membership, so omit
            userinfo["members"] = None  # type: ignore

    return userinfo


def collect_cg_access(
        session: ClientSession,
        user: UserSpec) -> List[NamedCGInfo]:
    """
    List of content generators user has access to run CGImport with.

    :param session: an active koji client session

    :param user: Name, ID, or userinfo dict

    :raises NoSuchUser: if user is an ID or name which cannot be
      resolved

    :since: 1.0
    """

    userinfo = as_userinfo(session, user)
    username = userinfo["name"]

    found = []
    for cgname, val in session.listCGs().items():
        if username in val.get("users", ()):
            nval = cast(NamedCGInfo, val)
            nval["name"] = cgname
            found.append(nval)
    return found


def collect_cgs(
        session: ClientSession,
        name: Optional[str] = None) -> List[NamedCGInfo]:
    """
    :param name: only collect the given CG. Default, collect all

    :raises NoSuchContentGenerator: if name is specified and no
      content generator matches

    :since: 1.0
    """

    cgs = session.listCGs()

    if name:
        # filter the cgs dict down to just the named one
        if name in cgs:
            cgs = {name: cgs[name]}
        else:
            raise NoSuchContentGenerator(name)

    result = []

    # convert the cgs dict into a list, augmenting the cg data with
    # its own name
    for name, cg in cgs.items():
        ncg = cast(NamedCGInfo, cg)
        ncg["name"] = name
        result.append(ncg)

    return result


def collect_perminfo(
        session: ClientSession,
        permission: PermSpec) -> DecoratedPermInfo:
    """
    Gather information about a named permission, including the list of
    users granted the permission, as well as the date that the
    permission was granted and the user that granted it.

    :param session: an active koji client session

    :param permission: the ID or name of the permission

    :raises NoSuchPermission: if there is no matching permission found

    :since: 1.0
    """

    if isinstance(permission, int):
        field = itemgetter("id")
    else:
        field = itemgetter("name")

    for p in session.getAllPerms():
        if field(p) == permission:
            pinfo = cast(DecoratedPermInfo, p)
            break
    else:
        raise NoSuchPermission(permission)

    users = session.queryHistory(tables=["user_perms"],
                                 permission=permission,
                                 active=1)["user_perms"]

    for user in users:
        user["user_name"] = user.pop("user.name")
        user["permission_name"] = user.pop("permission.name")
        user["create_date"] = asctime(localtime(user["create_ts"]))

    pinfo["users"] = cast(List[PermUser], users)

    return pinfo


#
# The end.
