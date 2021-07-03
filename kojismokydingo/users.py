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


from koji import ParameterError
from operator import itemgetter
from time import asctime, localtime

from . import NoSuchContentGenerator, NoSuchPermission, as_userinfo
from .types import UserType


__all__ = (
    "collect_cg_access",
    "collect_cgs",
    "collect_perminfo",
    "collect_userinfo",
)


def collect_userinfo(session, user):
    """
    Gather information about a named user, including the list of
    permissions the user has.

    Will convert the older `'krb_principal'` value (koji < 1.19) into
    a `'krb_principals'` list (koji >= 1.19) to provide some level of
    uniformity.

    :param user: name of a user or their kerberos ID

    :raises NoSuchUser:
    """

    userinfo = as_userinfo(session, user)

    # depending on koji version, getUser resulted in either a
    # krb_principal or krb_principals entry (or neither if it's not
    # set up for kerberos). Let's normalize on the newer
    # krb_principals one by converting. See
    # https://pagure.io/koji/issue/1629

    if "krb_principal" in userinfo:
        krb = userinfo.pop("krb_principal")
        userinfo["krb_principals"] = [krb] if krb else []

    uid = userinfo["id"]

    userinfo["permissions"] = session.getUserPerms(uid)
    userinfo["content_generators"] = collect_cg_access(session, userinfo)

    if userinfo.get("usertype", UserType.NORMAL) == UserType.GROUP:
        try:
            userinfo["members"] = session.getGroupMembers(uid)
        except Exception:
            # non-admin accounts cannot query group membership, so omit
            userinfo["members"] = None

    return userinfo


def collect_cg_access(session, user):
    """
    List of content generators user has access to run CGImport with.

    :param user: Name, ID, or userinfo dict

    :raises NoSuchUser: if user is an ID or name which cannot be
      resolved
    """

    userinfo = as_userinfo(session, user)
    username = userinfo["name"]

    found = []
    for cgname, val in session.listCGs().items():
        if username in val.get("users", ()):
            val["name"] = cgname
            found.append(val)
    return found


def collect_cgs(session, name=None):
    """
    :param name: only collect the given CG. Default, collect all

    :type name: str, optional

    :rtype: list[dict]

    :raises NoSuchContentGenerator: if name is specified and no
      content generator matches
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
        cg["name"] = name
        result.append(cg)

    return result


def collect_perminfo(session, permission):
    """
    Gather information about a named permission, including the list of
    users granted the permission, as well as the date that the
    permission was granted and the user that granted it.

    :param permission: the ID or name of the permission
    :type permission: int or str

    :rtype: dict

    :raises NoSuchPermission: if there is no matching permission found
    """

    if isinstance(permission, int):
        field = itemgetter("id")
    else:
        field = itemgetter("name")

    for p in session.getAllPerms():
        if field(p) == permission:
            pinfo = p
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

    pinfo["users"] = users

    return pinfo


#
# The end.
