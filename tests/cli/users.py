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

from kojismokydingo.cli.users import cli_userinfo
from kojismokydingo.types import AuthType, UserStatus, UserType


class TestUserInfo(TestCase):


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

        sess.getUser.side_effect = do_getUser
        sess.getUserPerms.side_effect = do_getUserPerms

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
            Permissions:
              coolguy
            """)
        print("testing", expected)
        self.assertEqual(expected, res)


#
# The end.
