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


from operator import itemgetter
from unittest import TestCase
from unittest.mock import MagicMock

from kojismokydingo import NoSuchTag
from kojismokydingo.common import unique
from kojismokydingo.tags import ensure_tag, gather_tag_ids


TAG_1 = {
    "id": 1011,
    "name": "tag-1.0",
    "parents": [],
}

TAG_1_RELEASED = {
    "id": 1013,
    "name": "tag-1.0-released",
    "parents": [1011],
}

TAG_1_CANDIDATE = {
    "id": 1012,
    "name": "tag-1.0-candidate",
    "parents": [1011],
}

TAG_2 = {
    "id": 1021,
    "name": "tag-2.0",
    "parents": [1011],
}

TAG_2_RELEASED = {
    "id": 1023,
    "name": "tag-2.0-released",
    "parents": [1021, 1013],
}

TAG_2_CANDIDATE = {
    "id": 1022,
    "name": "tag-2.0-candidate",
    "parents": [1021],
}

_TAGS = (
    TAG_1, TAG_1_CANDIDATE, TAG_1_RELEASED,
    TAG_2, TAG_2_CANDIDATE, TAG_2_RELEASED,
)
TAGS = dict((t["name"], t) for t in _TAGS)
TAGS.update((t["id"], t) for t in _TAGS)

TAG_NAMES = [t["name"] for t in _TAGS]
TAG_IDS = [t["id"] for t in _TAGS]


def inheritance(taginfo):
    res = []

    for pid in taginfo["parents"]:
        res.append({"parent_id": pid})
        res.extend(inheritance(TAGS[pid]))

    return unique(res, key=itemgetter("parent_id"))


class TestGatherTagIDs(TestCase):


    def get_session(self, ver="1.22"):

        wanted = []
        inhers = []

        def mc(strict=False):
            if wanted:
                res = [[TAGS.get(w)] for w in wanted]
                wanted[:] = []
            elif inhers:
                res = [[inheritance(TAGS.get(w))] for w in inhers]
                inhers[:] = []
            else:
                self.assertFalse(True)
            return res

        sess = MagicMock()
        sess.getTag.side_effect = lambda t, blocked=False: wanted.append(t)
        sess.getFullInheritance.side_effect = inhers.append
        sess.multiCall.side_effect = mc
        sess.getKojiVersion.side_effect = [ver]

        return sess


    def test_gather_tag_ids(self):

        res = set()
        tids = gather_tag_ids(None, results=res)
        self.assertTrue(tids is res)

        tids = gather_tag_ids(None)
        self.assertFalse(tids)

        tids = gather_tag_ids(self.get_session(), shallow=TAG_NAMES)
        self.assertEqual(tids, set(TAG_IDS))

        tids = gather_tag_ids(self.get_session(), deep=TAG_NAMES)
        self.assertEqual(tids, set(TAG_IDS))

        tids = gather_tag_ids(self.get_session(), deep=["tag-2.0-released"])
        self.assertEqual(tids, set([1023, 1021, 1011, 1013]))

        tids = gather_tag_ids(self.get_session(ver="1.24"),
                              deep=["tag-2.0-released"])
        self.assertEqual(tids, set([1023, 1021, 1011, 1013]))


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
