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


from datetime import datetime
from mock import MagicMock
from unittest import TestCase

from kojismokydingo import NoSuchChannel
from kojismokydingo.hosts import gather_hosts_checkins


HOST_1 = {
    "id": 1,
    "name": "host-01",
}


HOST_2 = {
    "id": 2,
    "name": "host-02",
}


HOST_3 = {
    "id": 3,
    "name": "joey-ramone",
}


BUILDERS = (
    HOST_1,
    HOST_2,
)


CHAN = {
    "id": 101,
    "name": "example-channel",
}


UPDATES = {
    1: {"result": "2020-10-10 14:22",
        "expect": datetime(2020, 10, 10, 14, 22)},
    2: {"result": None,
        "expect": None},
}


class TestHostCheckins(TestCase):


    def test_gather_hosts_checkins(self):
        sess = MagicMock()

        listhosts = sess.listHosts
        listhosts.side_effect = [[dict(b) for b in BUILDERS]]

        getchan = sess.getChannel
        getchan.side_effect = [CHAN]

        lu_ask = []
        lastupdate = sess.getLastHostUpdate
        lastupdate.side_effect = lu_ask.append

        mc = sess.multiCall
        mc.side_effect = lambda **k: ([UPDATES[i]["result"]] for i in lu_ask)

        hosts = gather_hosts_checkins(sess,
                                      arches=None,
                                      channel="example-channel",
                                      skiplist=['joey*'])

        self.assertEqual(len(hosts), 2)

        self.assertEqual(getchan.call_count, 1)
        self.assertEqual(getchan.call_args[0][0], "example-channel")

        self.assertEqual(listhosts.call_count, 1)

        self.assertEqual(lastupdate.call_count, 2)
        self.assertEqual(lastupdate.call_count, 2)

        self.assertEqual(mc.call_count, 1)

        for bldr in hosts:
            bldr_id = bldr["id"]
            self.assertEqual(UPDATES[bldr_id]["expect"], bldr["last_update"])


#
# The end.
