#! /usr/bin/env python3

"""
Simple utility for querying brew to check for builders which are
enabled but which are not checking in.

author: cobrien@redhat.com
"""


import sys

from datetime import datetime, timedelta
from fnmatch import fnmatchcase
from functools import partial
from itertools import filterfalse
from argparse import ArgumentParser
from socket import gaierror
from xmlrpc.client import Fault, MultiCall, ServerProxy


BREW_SERVICE = "https://brewhub.engineering.redhat.com/brewhub"


class NoSuchChannel(Exception):
    pass


def get_channel_id(brewhub, channel_name):
    chan_data = brewhub.getChannel(channel_name)
    if chan_data is None:
        raise NoSuchChannel(channel_name)

    return chan_data["id"]


def namematch(patterns, bldr):
    bldr = bldr["name"]
    for pattern in patterns:
        if fnmatchcase(bldr, pattern):
            return True
    return False


def get_hosts_checkins(brewhub, arches=None, channel=None, skiplist=None):

    arches = arches or None
    chan_id = get_channel_id(brewhub, channel) if channel else None

    bldrs = brewhub.listHosts(arches, chan_id, None, True, None, None)

    if skiplist:
        bldrs = filterfalse(partial(namematch, skiplist), bldrs)

    bldrs = {b["id"]: b for b in bldrs}
    bldr_ids = list(bldrs.keys())

    mc = MultiCall(brewhub)
    for bid in bldr_ids:
        mc.getLastHostUpdate(bid)

    for bid, data in zip(bldr_ids, mc()):
        if data:
            data = data + " UTC"
            data = datetime.strptime(data, "%Y-%m-%d %H:%M:%S.%f %Z")

        bldrs[bid]["last_update"] = data

    return bldrs


def cli(options):

    ignore = options.ignore
    if options.ignore_file:
        with open(options.ignore_file, "rt") as ignf:
            for line in ignf:
                line = line.strip()
                if line:
                    ignore.append(line)

    timeout = datetime.utcnow() - timedelta(seconds=(options.timeout * 60))

    brewhub = ServerProxy(options.brewhub, allow_none=True)

    bldr_data = get_hosts_checkins(brewhub,
                                   arches=options.arches,
                                   channel=options.channel,
                                   skiplist=ignore)

    collected = []

    for bldr in bldr_data.values():
        lup = bldr["last_update"]

        if lup:
            if lup < timeout:
                collected.append((bldr["name"], lup))
        else:
            collected.append((bldr["name"], " --"))

    if options.quiet:
        for host, _ in sorted(collected):
            print(host)

    else:
        for host, lup in sorted(collected):
            print(host, lup)

        mia_c = len(collected)
        if mia_c or not options.shush:
            # only print the summary if we have MIA builders or
            # options.shush isn't set

            print()
            print("Found", mia_c,
                  "hosts that have not checked in since", timeout)

    if collected:
        return 1
    else:
        return 0


def create_argparser(called_by):

    ap = ArgumentParser(prog=called_by,
                        description="Check for enabled builders which"
                        " haven't checked in recently")

    arg = ap.add_argument

    arg("--brewhub", action="store", default=BREW_SERVICE,
        help="URI for the brewhub service")

    arg("--channel", action="store", default=None,
        help="Limit check to builders in this channel")

    arg("--arch", dest="arches", action="append", default=[],
        help="Limit check to builders of this architecture. Can be"
        " specified multiple times")

    arg("--timeout", action="store", default=60, type=int,
        help="Timeout in minutes before builder is considered"
        " AWOL (default: 60)")

    arg("--ignore", action="append", default=[],
        help="Hostname pattern to ignore. Can be specified"
        " multiple times")

    arg("--ignore-file", action="store", default=None,
        help="File containing ignore patterns")

    arg("-q", "--quiet", dest="quiet", action="store_true", default=False,
        help="Only print builder names, not checkin time or summary")

    arg("-s", "--shush", dest="shush", action="store_true", default=False,
        help="Only print summary when 1 or more builders are failing"
        " to check in (cron-job friendly)")

    return ap


def main(args=None):

    if args is None:
        args = sys.argv

    called_by, *args = args

    parser = create_argparser(called_by)
    options = parser.parse_args(args)

    printerr = partial(print, file=sys.stderr)

    try:
        result = cli(options)

    except KeyboardInterrupt:
        printerr()
        return 130

    except Fault as xmlf:
        printerr(xmlf.faultString)
        return -1

    except gaierror as dns:
        printerr(dns.message)
        printerr("Try using --brewhub with an IP address")
        return -2

    except NoSuchChannel as no_chan:
        printerr("No such builder channel:", no_chan)
        return -3

    else:
        return result


if __name__ == "__main__":
    sys.exit(main())


#
# The end.
