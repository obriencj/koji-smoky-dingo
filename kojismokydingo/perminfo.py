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
Koji Smoki Dingo - info command perminfo

Get information about a permission

:author: cobrien@redhat.com
:license: GPL version 3
"""


from __future__ import print_function

from operator import itemgetter
from time import asctime, localtime

from . import AnonSmokyDingo, NoSuchPermission
from .common import pretty_json


def collect_perminfo(session, permission):
    for p in session.getAllPerms():
        # print(" checking", p)
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
                            options.verbose, options.by_date,
                            options.json)


#
# The end.
