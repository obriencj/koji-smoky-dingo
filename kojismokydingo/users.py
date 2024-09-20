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


from koji import ClientSession, GenericError, ParameterError
from operator import itemgetter
from time import asctime, localtime
from typing import List, Optional, Union, cast

from . import (
    NoSuchContentGenerator, NoSuchPermission, NoSuchUser,
    as_userinfo, bulk_load_users, version_check, )
from .types import (
    CGInfo, DecoratedPermInfo, DecoratedUserInfo, NamedCGInfo,
    PermSpec, PermUser, UserInfo, UserSpec, UserStatistics,
    UserGroup, UserType, )


__all__ = (
    "collect_cg_access",
    "collect_cgs",
    "collect_perminfo",
    "collect_userinfo",
    "collect_userstats",
    "get_group_members",
    "get_user_groups",
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

    with session.multicall() as mc:
        build_count = mc.listBuilds(userID=userinfo['id'],
                                    queryOpts={'countOnly': True})

        package_count = mc.listPackages(userID=userinfo['id'],
                                        with_dups=True,
                                        queryOpts={'countOnly': True})

        task_count = mc.listTasks(opts={'owner': userinfo['id'],
                                        'parent': None},
                                  queryOpts={'countOnly': True})

        last_build = mc.listBuilds(userID=userinfo['id'],
                                   queryOpts={'limit': 1,
                                              'order': '-build_id'})

        last_task = mc.listTasks(opts={'owner': userinfo['id'],
                                       'parent': None},
                                 queryOpts={'limit': 1,
                                            'order': '-id'})

    stats: UserStatistics = {
        # I haven't figured out how to indicate that the queryOpts
        # with countOnly set changes the return type to int.
        'build_count': build_count.result,      # type: ignore
        'package_count': package_count.result,  # type: ignore
        'task_count': task_count.result,        # type: ignore

        # just need to unwrap the list if any
        'last_build': last_build.result[0] if last_build.result else None,
        'last_task': last_task.result[0] if last_task.result else None,
    }

    return stats


def get_user_groups(
        session: ClientSession,
        user: UserSpec) -> List[UserGroup]:
    """
    Identify groups that a user is a member of

    :param session: an active koji client session

    :param user: name or ID of a potential member

    :returns: list of groups that user is a member of

    :raises NoSuchUser: if user could not be found

    :since: 2.2
    """

    user = as_userinfo(session, user)
    uid = user["id"]

    if version_check(session, (1, 35)):
        # added in 1.35
        return session.getUserGroups(uid) or []

    else:
        hist = session.queryHistory(tables=["user_groups"], active=True)
        return [{"name": g["group.name"], "id": g["group_id"]}
                for g in hist["user_groups"]
                if g["user_id"] == uid]


def get_group_members(
        session: ClientSession,
        user: UserSpec) -> List[UserInfo]:

    """
    An anonymous version of the admin-only ``getGroupMembers`` hub
    API call. Uses ``queryHistory`` to gather still-active group
    additions

    :param session: an active koji client session

    :param user: name or ID of a user group

    :returns: list of users that are members of the given group

    :raises NoSuchUser: if no matching user group was found

    :since: 2.2
    """

    # getGroupMembers returns a list of dicts, with keys: id,
    # krb_principals, name, usertype. However, the call requires the
    # admin permission prior to 1.35

    # queryHistory is anonymous, and returns a dict mapping table to a
    # list of events. In those events are keys: "user.name" and
    # "user_id" which we can use to then lookup the rest of the
    # information

    user = as_userinfo(session, user)

    if user["usertype"] != UserType.GROUP:
        # we shortcut this because querying by a non-existent group ID
        # causes hub to return all group memberships
        return []

    if version_check(session, (1, 35)):
        return session.getGroupMembers(user["id"]) or []

    else:
        hist = session.queryHistory(tables=["user_groups"],
                                    active=True, user=user["id"])

        uids = map(itemgetter("user_id"), hist["user_groups"])
        found = bulk_load_users(session, uids, err=False)
        return list(filter(None, found.values()))


def collect_userinfo(
        session: ClientSession,
        user: UserSpec,
        stats: bool = False,
        members: bool = False) -> DecoratedUserInfo:
    """
    Gather information about a named user, including the list of
    permissions the user has.

    Will convert the older `'krb_principal'` value (koji < 1.19) into
    a `'krb_principals'` list (koji >= 1.19) to provide some level of
    uniformity.

    :param session: an active koji client session

    :param user: name of a user or their kerberos ID

    :param stats: collect user statistics

    :param members: look up group members and memberships

    :raises NoSuchUser: if user is an ID or name which cannot be
      resolved

    :since: 2.2
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

        if members:
            userinfo["ksd_groups"] = get_user_groups(session, uid)

    elif ut == UserType.GROUP:
        if members:
            userinfo["ksd_members"] = get_group_members(session, uid)

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
