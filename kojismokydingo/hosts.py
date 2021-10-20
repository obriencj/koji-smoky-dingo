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
Koji Smoky Dingo - Host Utilities

Functions for working with Koji hosts

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""

from koji import ClientSession
from typing import Dict, Iterable, List, Optional, cast

from . import NoSuchChannel, iter_bulk_load
from .common import globfilter, parse_datetime
from .types import DecoratedHostInfo, HostInfo


__all__ = (
    "gather_hosts_checkins",
)


def gather_hosts_checkins(
        session: ClientSession,
        arches: Optional[List[str]] = None,
        channel: Optional[str] = None,
        skiplist: Optional[List[str]] = None) -> List[DecoratedHostInfo]:
    """
    Similar to session.listHosts, but results are decorated with a new
    "last_update" entry, which is the timestamp for the host's most
    recent check-in with the hub. This can be used to identify
    builders which are enabled, but no longer responding.

    :param session: an active koji client session

    :param arches: List of architecture names to filter builders by.
        Default, all arches

    :param channel: Channel name to filter builders by. Default,
        builders in any channel.

    :param skiplist: List of glob-style patterns of builders to
        omit. Default, all builders included

    :since: 1.0
    """

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

    loaded: Iterable[HostInfo]
    loaded = session.listHosts(arches, chan_id, None, True, None, None)
    loaded = filter(None, loaded)

    if skiplist:
        loaded = globfilter(loaded, skiplist, key="name", invert=True)

    # collect a mapping of builder ids to builder info
    bldrs: Dict[int, DecoratedHostInfo]
    bldrs = {b["id"]: cast(DecoratedHostInfo, b) for b in loaded}

    updates = iter_bulk_load(session, session.getLastHostUpdate, bldrs)

    # correlate the update timestamps with the builder info
    for bldr_id, data in updates:
        data = parse_datetime(data, strict=False) if data else None
        bldrs[bldr_id]["last_update"] = data

    return list(bldrs.values())


#
# The end.
