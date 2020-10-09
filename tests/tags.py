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


from mock import MagicMock
from unittest import TestCase

from kojismokydingo import NoSuchTag
from kojismokydingo.tags import ensure_tag


class TestEnsureTag(TestCase):

    DATA = {
        "id": 1,
        "name": "example-1.0-build",
    }


    def session(self, results, ver="1.23"):
        sess = MagicMock()

        send = sess.getTag
        send.side_effect = results

        create = sess.createTag
        create.side_effect = [1]

        vercheck = sess.getKojiVersion
        vercheck.side_effect = [ver]

        return sess, send, create


    def test_ensure_tag_create(self):

        key = "example-1.0-build"

        sess, send, create = self.session([None, self.DATA])
        res = ensure_tag(sess, key)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 2)
        self.assertEqual(send.call_args_list[0][0], (key,))
        self.assertEqual(send.call_args_list[0][1], {"blocked": True})
        self.assertEqual(send.call_args_list[1][0], (1,))
        self.assertEqual(send.call_args_list[1][1], {"blocked": True})
        self.assertEqual(create.call_count, 1)


    def test_ensure_tag_exists(self):

        key = "example-1.0-build"

        sess, send, create = self.session([self.DATA])
        res = ensure_tag(sess, key)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (key,))
        self.assertEqual(send.call_args_list[0][1], {"blocked": True})
        self.assertEqual(create.call_count, 0)


#
# The end.
