#!/usr/bin/env python2


"""

Given a tag, check for imported builds.

author: cobrien@redhat.com

"""


import sys

from optparse import OptionParser
from socket import gaierror
from xmlrpclib import Fault, MultiCall, ServerProxy


BREW_SERVICE = "https://brewhub.engineering.redhat.com/brewhub"


def identify_imports(build_infos, reverse=False, by_cg=set()):
    """
    Given a sequence of build info dicts, emit those which are imports.

    if reverse is True, then behavior is flipped and only non-imports
    are emitted (and the by_cg parameter is ignored)

    If by_cg is not specified, then only non CG imports are emitted.
    If by_cg is specified, then emit only those imports which are from
    a content generator in that set (or all content generators if
    'all' is in the by_cg set).
    """

    all_cg = "all" in by_cg

    for build in build_infos:
        extra = build.get("extra", None)
        build_cg = extra.get("build_system", None) if extra else None

        is_import = build.get("task_id", None) is None

        if reverse:
            # looking for non-imports, regardless of CG or not
            if not is_import:
                yield build

        elif is_import:
            if build_cg:
                if all_cg or build_cg in by_cg:
                    # this is a CG import, and we wanted either this
                    # specific one or all of them
                    yield build

            elif not by_cg:
                # this isn't a CG import, and we didn't want it to be
                yield build


def chunk(seq, chunksize):
    return (seq[offset:offset+chunksize] for
            offset in xrange(0, len(seq), chunksize))


def chunk_load(brewhub, build_ids):
    """
    Try not to be cruel to brew, and only request 100 build info at a
    time
    """

    for bid_chunk in chunk(build_ids, 100):
        multicall = MultiCall(brewhub)
        for bid in bid_chunk:
            multicall.getBuild(bid)
        for binfo in multicall():
            yield binfo


def cli(options, nvr_list):

    brewhub = ServerProxy(options.brewhub)

    if len(nvr_list) == 1 and nvr_list[0] == "-":
        # special case, read list of NVRs from stdin
        nvr_list = (line.strip() for line in sys.stdin)
        nvr_list = [line for line in nvr_list if line]
        found_builds = list(chunk_load(brewhub, nvr_list))

    elif nvr_list:
        found_builds = list(chunk_load(brewhub, nvr_list))

    else:
        found_builds = list()

    if options.tag:
        call_args = {'__starstar': True,
                     'latest': False,
                     'inherit': options.inherit, }

        more_builds = brewhub.listTagged(options.tag, call_args)

        if not options.reverse:
            # the listTagged call doesn't return the extra information
            # we need to determine which CG something came from, so we
            # need to gather up full buildinfo data from those results
            # first.  However we happen to know that in reverse mode
            # we don't actually care about that, so we'll skip the
            # loading in that case.
            more_builds = chunk_load(brewhub, [b["id"] for b in more_builds])

        found_builds.extend(more_builds)

    matching = identify_imports(found_builds,
                                options.reverse,
                                set(options.cg))

    for build in matching:
        print build["nvr"]


def create_optparser():
    parse = OptionParser("%prog [OPTIONS] [NVR [NVR...]]",
                         description="Find imported builds by NVR. Specify"
                         " a single NVR of - to read list from stdin")

    parse.add_option("--brewhub", action="store", default=BREW_SERVICE,
                     help="URI for the brewhub service")

    parse.add_option("--tag", action="store", default=None,
                     help="look through a tag to find builds to filter")

    parse.add_option("--inherit", action="store_true", default=False,
                     help="use with --tag=TAG to follow inheritance"
                     " when searching for imported builds")

    parse.add_option("--reverse", action="store_true", default=False,
                     help="reverse behavior, list non-imports instead"
                     " of imports")

    parse.add_option("--cg", action="append", default=list(),
                     help="show content generator imports by build"
                     " system name. Default: display no CG builds."
                     " Specify 'all' to see CG imports from any system."
                     " May be specified more than once.")

    return parse


def main(args):
    parser = create_optparser()
    options, args = parser.parse_args(args)

    try:
        cli(options, args[1:])

    except KeyboardInterrupt:
        print
        return 130

    except Fault as xmlf:
        print >> sys.stderr, xmlf.faultString
        return -1

    except gaierror as dns:
        print >> sys.stderr, dns.message
        print >> sys.stderr, "Try using --brewhub with an IP address"
        return -2

    else:
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))


#
# The end.
