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
Koji Smoky Dingo - hosts utilities

:author: cobrien@redhat.com
:license: GPL version 3
"""

from datetime import datetime
from operator import itemgetter
from six import iterkeys
from six.moves import zip

from . import NoSuchChannel
from .common import globfilter


def get_hosts_checkins(session, arches=None, channel=None, skiplist=None):

    arches = arches or None

    # listHosts only accepts channel filtering by the ID, so let's
    # resolve those. This should also work if channel is already an
    # ID, and should validate that the channel exists.
    if channel:
        chan_data = session.getChannel(channel)
        if chan_data is None:
            raise NoSuchChannel(channel)
        chan_id = chan_data["id"]
    else:
        chan_id = None

    bldrs = session.listHosts(arches, chan_id, None, True, None, None)

    if skiplist:
        bldrs = globfilter(bldrs, skiplist,
                           key=itemgetter("name"), invert=True)

    # collect a mapping of builder ids to builder info
    bldrs = dict((b["id"], b) for b in bldrs)

    # correlate the update timestamps with the builder info
    bldr_ids = list(iterkeys(bldrs))

    session.multicall = True
    for bid in bldr_ids:
        session.getLastHostUpdate(bid)
    mc = session.multiCall()

    for bid, data in zip(bldr_ids, mc):
        data = data[0] if data else None

        if data:
            data = data + " UTC"
            data = datetime.strptime(data, "%Y-%m-%d %H:%M:%S.%f %Z")

        bldrs[bid]["last_update"] = data

    return bldrs


#
# The end.
