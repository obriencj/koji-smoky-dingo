#! /usr/bin/env python

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


from __future__ import print_function

from kojismokydingo.cli import pretty_json, printerr
from kojismokydingo.cli.users import get_usertype_str, get_userstatus_str
from kojismokydingo.standalone import LonelyDingo
from kojismokydingo.users import collect_userinfo

import sys


class WhoAmI(LonelyDingo):
    # A LonelyDingo is a subclass of SmokyDingo which has an adaptive
    # layer to allow its instances to be called directly or as
    # console_scripts type entry_points. This means that you can get
    # to a working script a bit faster than starting from scratch,
    # because the option parsing, koji profile selection, session
    # initiation, and primary exception handling are all provided
    # already.


    # for custom scripts in your environment, you can also declare the
    # default profile by name. If unspecified or set to None, then the
    # -p/--profile command-line argument becomes required.
    default_profile = None


    # This blurb now becomes part of the --help output
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


if __name__ == "__main__":
    sys.exit(WhoAmI.main())


# The end.
