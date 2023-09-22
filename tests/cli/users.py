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


from io import StringIO
from textwrap import dedent
from unittest import TestCase
from unittest.mock import MagicMock, patch

from kojismokydingo.cli.users import (
    cli_userinfo, get_userauth_str,
    get_userstatus_str, get_usertype_str, )
from kojismokydingo.types import AuthType, UserStatus, UserType


class ShowUserInfoTest(TestCase):


    def userinfo(self):
        return {
            "authtype": AuthType.KERB,
            "id": 100,
            "krb_principal": "obriencj@PREOCCUPIED.NET",
            "krb_principals": ["obriencj@PREOCCUPIED.NET",],
            "name": "obriencj",
            "status": UserStatus.NORMAL,
            "usertype": UserType.NORMAL,
        }


    def session(self):
        sess = MagicMock()

        def do_getUser(userInfo = None, strict = False, krb_princs = True):
            if userInfo in (None, 100, "obriencj"):
                return self.userinfo()
            else:
                return None

        def do_getUserPerms(userID = None):
            if userID in (None, 100, "obriencj"):
                return ["coolguy", ]
            else:
                return []

        def do_getUserGroups(userID = None):
            if userID in (None, 100, "obrienc"):
                return [{"name": "ldap/CoolGuys",
                         "group_id": 500,}]
            else:
                return []

        def do_getGroupMembers(userID = None):
            if userID == 500:
                return [self.userinfo()]
            else:
                return []

        sess.getUser.side_effect = do_getUser
        sess.getUserPerms.side_effect = do_getUserPerms
        sess.getUserGroups.side_effect = do_getUserGroups
        sess.getKojiVersion.return_value = "1.35"

        return sess


    def test_cli_userinfo(self):

        sess = self.session()
        with patch("sys.stdout", new=StringIO()) as out:
            cli_userinfo(sess, 100)
            res = out.getvalue()

        expected = dedent(
            """\
            User: obriencj [100]
            Authentication method: Kerberos ticket
            Kerberos principals:
              obriencj@PREOCCUPIED.NET
            Type: NORMAL (user)
            Status: NORMAL (enabled)
            Groups:
              ldap/CoolGuys [500]
            Permissions:
              coolguy
            """)
        self.assertEqual(expected, res[:len(expected)])


class EnumTextTest(TestCase):


    def test_usertype_str(self):

        def check(val):
            info = {"usertype": val}
            return get_usertype_str(info)

        pairs = (
            (0, "NORMAL (user)"),
            (1, "HOST (builder)"),
            (2, "GROUP"),
            (3, "Unknown (3)"),
            (99, "Unknown (99)"),
        )

        for val, exp in pairs:
            self.assertEqual(check(val), exp)


    def test_userstatus_str(self):

        def check(val):
            info = {"status": val}
            return get_userstatus_str(info)

        pairs = (
            (0, "NORMAL (enabled)"),
            (1, "BLOCKED (disabled)"),
            (2, "Unknown (2)"),
            (99, "Unknown (99)"),
        )

        for val, exp in pairs:
            self.assertEqual(check(val), exp)


    def test_userauth_str(self):

        def check(val):
            info = {"authtype": val}
            return get_userauth_str(info)

        pairs = (
            (0, "Password"),
            (1, "Kerberos ticket"),
            (2, "SSL certificate"),
            (3, "GSSAPI"),
            (4, "Unknown (4)"),
            (99, "Unknown (99)"),
        )

        for val, exp in pairs:
            self.assertEqual(check(val), exp)


#
# The end.
