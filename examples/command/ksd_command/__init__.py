


from __future__ import print_function

from kojismokydingo.cli import AnonSmokyDingo, SmokyDingo, pretty_json
from kojismokydingo.cli.users import get_usertype_str, get_userstatus_str
from kojismokydingo.users import collect_userinfo


class BeepBoop(AnonSmokyDingo):

    """
    [misc] BEEP BOOP
    """

    def handle(self, options):
        # The name of the command is defined by the entry_point hook's
        # name. This means we can, if so desired, have a single
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


    def parser(self):
        # if you're certain your commands will only be used on Python
        # 3, feel free to use the more modern form of super(). But if
        # you're going to support older hosts that run Python 2, gotta
        # do it this way.
        parser = super(WhoAmI, self).parser()

        parser.add_argument("--json", action="store_true", default=False,
                            help="Output as JSON")

        return parser


    def handle(self, options):
        # implemented very similarly to the userinfo command

        myinfo = self.session.getLoggedInUser()
        collect_userinfo(self.session, myinfo)

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


# The end.
