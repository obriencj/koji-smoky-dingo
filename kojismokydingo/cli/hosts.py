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
Koji Smoky Dingo - CLI Host Commands

Simple utility for querying brew to check for builders which are
enabled but which are not checking in.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from __future__ import print_function

from datetime import datetime, timedelta

from . import AnonSmokyDingo
from ..hosts import gather_hosts_checkins


def cli_check_hosts(session, timeout=60, arches=(), channel=None,
                    ignore=(), quiet=False, shush=False):

    timeout = datetime.utcnow() - timedelta(seconds=(timeout * 60))

    bldr_data = gather_hosts_checkins(session,
                                      arches=arches,
                                      channel=channel,
                                      skiplist=ignore)

    collected = []

    for bldr in bldr_data:
        lup = bldr["last_update"]
        if lup and lup.tzinfo is not None:
            lup = lup.replace(tzinfo=None)

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


class CheckHosts(AnonSmokyDingo):

    description = "Show enabled builders which aren't checking in"


    def arguments(self, parser):
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

        return cli_check_hosts(self.session, options.timeout,
                               options.arches, options.channel,
                               ignore,
                               options.quiet, options.shush)


#
# The end.
