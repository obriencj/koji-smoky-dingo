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
Koji Smoky Dingo - info command check-hosts

Simple utility for querying brew to check for builders which are
enabled but which are not checking in.

:author: cobrien@redhat.com
:license: GPL version 3
"""


from __future__ import print_function

from datetime import datetime, timedelta
from fnmatch import fnmatchcase
from functools import partial
from six.moves import filterfalse as ifilterfalse, zip as izip

from . import AnonSmokyDingo, BadDingo


class NoSuchChannel(BadDingo):
    complaint = "No such builder channel"


def get_channel_id(session, channel_name):
    chan_data = session.getChannel(channel_name)
    if chan_data is None:
        raise NoSuchChannel(channel_name)

    return chan_data["id"]


def namematch(patterns, bldr):
    bldr = bldr["name"]
    for pattern in patterns:
        if fnmatchcase(bldr, pattern):
            return True
    return False


def get_hosts_checkins(session, arches=None, channel=None, skiplist=None):

    arches = arches or None
    chan_id = get_channel_id(session, channel) if channel else None

    bldrs = session.listHosts(arches, chan_id, None, True, None, None)

    if skiplist:
        bldrs = ifilterfalse(partial(namematch, skiplist), bldrs)

    bldrs = {b["id"]: b for b in bldrs}
    bldr_ids = list(bldrs.keys())

    session.multicall = True
    for bid in bldr_ids:
        session.getLastHostUpdate(bid)
    mc = session.multiCall()

    for bid, data in izip(bldr_ids, mc):
        if data:
            data = data + " UTC"
            data = datetime.strptime(data, "%Y-%m-%d %H:%M:%S.%f %Z")

        bldrs[bid]["last_update"] = data

    return bldrs


def cli_check_hosts(session, timeout=60, arches=(), channel=None,
                    ignore=(), quiet=False, shush=False):

    timeout = datetime.utcnow() - timedelta(seconds=(timeout * 60))

    bldr_data = get_hosts_checkins(session,
                                   arches=arches,
                                   channel=channel,
                                   skiplist=ignore)

    collected = []

    for bldr in bldr_data.values():
        lup = bldr["last_update"]

        if lup:
            if lup < timeout:
                collected.append((bldr["name"], lup))
        else:
            collected.append((bldr["name"], " --"))

    if quiet:
        for host, _lup in sorted(collected):
            print(host)

    else:
        for host, lup in sorted(collected):
            print(host, lup)

        if collected or not shush:
            # only print the summary if we have MIA builders or
            # options.shush isn't set

            print()
            print("Found", len(collected),
                  "hosts that have not checked in since", timeout)

    return 1 if collected else 0


class cli(AnonSmokyDingo):

    description = "Show enabled builders which aren't checking in"


    def parser(self):
        parser = super(cli, self).parser()
        addarg = parser.add_argument

        addarg("--timeout", action="store", default=60, type=int,
               help="Timeout in minutes before builder is considered"
               " AWOL (default: 60)")

        addarg("--channel", action="store", default=None,
               help="Limit check to builders in this channel")

        addarg("--arch", dest="arches", action="append", default=[],
               help="Limit check to builders of this architecture. Can be"
               " specified multiple times")

        addarg("--ignore", action="append", default=[],
               help="Hostname pattern to ignore. Can be specified"
               " multiple times")

        addarg("--ignore-file", action="store", default=None,
               help="File containing ignore patterns")

        addarg("-q", "--quiet", dest="quiet", action="store_true",
               default=False,
               help="Only print builder names, not checkin time or summary")

        addarg("-s", "--shush", dest="shush", action="store_true",
               default=False,
               help="Only print summary when 1 or more builders are failing"
               " to check in (cron-job friendly)")

        return parser


    def handle(self, options):

        ignore = options.ignore
        if options.ignore_file:
            with open(options.ignore_file, "rt") as ignf:
                for line in ignf:
                    line = line.strip()
                    if line:
                        ignore.append(line)

        return cli_check_hosts(options.session, options.timeout,
                               options.arches, options.channel,
                               ignore,
                               options.quiet, options.shush)


#
# The end.
