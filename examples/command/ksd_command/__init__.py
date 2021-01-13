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
An example project that uses Koji Smoky Dingo to add new commands
to Koji
"""


from __future__ import print_function

from kojismokydingo.cli import AnonSmokyDingo, SmokyDingo, pretty_json
from kojismokydingo.cli.users import get_usertype_str, get_userstatus_str
from kojismokydingo.users import collect_userinfo


class BeepBoop(AnonSmokyDingo):

    # this is similar to setting the group and description
    # individually
    """
    [misc] Just some beeps and boops
    """

    def handle(self, options):
        # The name of the command is defined by the entry_point hook's
        # name. This means we can, if we so desire, have a single
        # command serve multiple purposes.

        if self.name == "boop":
            print(self.name, "beep")
        else:
            print(self.name, "boop")


class WhoAmI(SmokyDingo):


    # The group that this command is a part of. For a normal
    # SmokyDingo subclass "misc" is the default value.
    group = "misc"

    # This blurb appears alongside the command name in `koji help`
    description = """
    Print identity and information about the currently logged-in user
    """

    # Can be set to a str that is a permisison name to perform a check
    # prior to the handle method being called. None is the default
    # value, meaning no special permission is required.
    permission = None


    def arguments(self, parser):
        # use this method to decorate the default ArgumentParser instance
        # with more arguments

        parser.add_argument("--json", action="store_true", default=False,
                            help="Output as JSON")

        return parser


    def handle(self, options):
        # implemented very similarly to the userinfo command

        myinfo = self.session.getLoggedInUser()
        myinfo = collect_userinfo(self.session, myinfo)

        if options.json:
            pretty_json(myinfo)
            return

        print("User: {name} [{id}]".format(**myinfo))

        krb_princs = myinfo.get("krb_principals", None)
        if krb_princs:
            print("Kerberos principals:")
            for kp in sorted(krb_princs):
                print(" ", kp)

        print("Type:", get_usertype_str(myinfo))
        print("Status:", get_userstatus_str(myinfo))

        perms = myinfo.get("permissions", None)
        if perms:
            print("Permissions:")
            for perm in sorted(perms):
                print(" ", perm)


#
# The end.
