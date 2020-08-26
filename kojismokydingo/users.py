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

:author: cobrien@redhat.com
:license: GPL version 3
"""


from koji import ParameterError, USERTYPES, USER_STATUS
from six import iteritems
from time import asctime, localtime

from . import NoSuchContentGenerator, NoSuchPermission, NoSuchUser


# just borrowing from Koji's definitions
USER_NORMAL = USERTYPES['NORMAL']
USER_HOST = USERTYPES['HOST']
USER_GROUP = USERTYPES['GROUP']

STATUS_NORMAL = USER_STATUS['NORMAL']
STATUS_BLOCKED = USER_STATUS['BLOCKED']


def as_userinfo(session, user):
    """
    Resolves user to a userinfo dict.

    If user is a str or int, then getUser will be invoked. If user is
    already a dict, it's presumed to be a userinfo already and it's
    returned unaltered.

    :param user: Name, ID, or User Info describing a koji user

    :type user: Union[str, int, dict]

    :rtype: dict

    :raises NoSuchUser: when user cannot be resolved via
        session.getUser
    """

    if isinstance(user, (str, int)):
        # an API incompatibility emerged at some point in Koji's past,
        # so we need to try the new way first and fall back to the
        # older signature if that fails
        try:
            info = session.getUser(user, False, True)
        except ParameterError:
            info = session.getUser(user)

    elif isinstance(user, dict):
        info = user

    else:
        info = None

    if not info:
        raise NoSuchUser(user)

    return info


def collect_userinfo(session, user):
    """
    Gather information about a named user, including the list of
    permissions the user has.

    :param user: name of a user or their kerberos ID
    :type user: str

    :rtype: dict

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

    perms = session.getUserPerms(uid)
    userinfo["permissions"] = perms

    if userinfo.get("usertype", USER_NORMAL) == USER_GROUP:
        try:
            userinfo["members"] = session.getGroupMembers(uid)
        except Exception:
            # non-admin accounts cannot query group membership, so omit
            userinfo["members"] = None

    cgs = collect_cg_access(session, userinfo)
    userinfo["content_generators"] = cgs

    return userinfo


def collect_cg_access(session, user):
    """
    List of names of content generators user has access to run
    CGImport with.

    :param user: Name, ID, or userinfo dict

    :type user: Union[str, id, dict]

    :rtype: list[dict]

    :raises NoSuchUser:
    """

    userinfo = as_userinfo(session, user)
    user = userinfo["name"]

    found = []
    for cgname, val in iteritems(session.listCGs()):
        if username in val.get("users", ()):
            found.append(cgname)
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
    for name, cg in iteritems(cgs):
        cg["name"] = name
        result.append(cg)

    return result


def collect_perminfo(session, permission):
    """
    Gather information about a named permission, including the list of
    users granted the permission, as well as the date that the
    permission was granted and the user that granted it.

    :param permission: the string name of a permission

    :type permission: str

    :rtype: dict
    """

    for p in session.getAllPerms():
        if p["name"] == permission:
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
