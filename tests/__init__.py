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


import koji

from mock import MagicMock, PropertyMock, patch
from six.moves import zip
from unittest import TestCase

from kojismokydingo import iter_bulk_load


class TestBulkLoad(TestCase):


    def setUp(self):
        self.prep = patch('koji.ClientSession._prepCall').start()
        self.prep.return_value = (None, None, None)
        self.send = patch('koji.ClientSession._sendCall').start()
        self.session = koji.ClientSession('FAKE_URL')


    def tearDown(self):
        patch.stopall()


    def test_iter_bulk_load(self):
        # validates that the iter_bulk_load utility is indeed breaking up
        # the list of keys into the appropriate sized chunks and
        # invoking the function in a multicall loop, then yielding the
        # key:result pairs.

        # these are our pretend results for the expected multicall
        # invocations.
        self.send.side_effect = [
            [[100 + v] for v in range(i, i+5)] for i in range(0, 25, 5)
        ]

        x = iter_bulk_load(self.session, self.session.ImpossibleDream,
                           range(0, 25), True, size=5)
        x = list(x)

        self.assertEqual(x, list(zip(range(0, 25), range(100, 125))))

        self.assertEqual(self.prep.call_count, 5)
        self.assertEqual(self.send.call_count, 5)

        # we'll validate that the prep mock was triggered five times, each
        # with five invocations to the ImpossibleDream endpoint, with a
        # single incrementing integer argument.
        for prep, offset in zip(self.prep.call_args_list, range(0, 25, 5)):

            # the multicall invocation itself
            mc = prep[0]
            self.assertEqual(mc[0], "multiCall")

            # the first argument to the multiCall invocation is a list
            # of endpoints to call and the args
            calls = mc[1][0]
            self.assertEqual(len(calls), 5)

            for i, call in enumerate(calls):
                self.assertEqual(call['methodName'], "ImpossibleDream")
                self.assertEqual(call['params'], (i + offset,))


#
# The end.
