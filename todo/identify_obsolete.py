#!/usr/bin/env python2


"""

Given a release tag and a candidate tag, produce a list of NVRs in the
candidate tag which are obsolete (built before a matching build in the
release tag).

When using the --reverse option, this will instead produce a list of
NVRs in the candidate tag which are newer than a matching build in the
release tag.

author: cobrien@redhat.com

"""


import sys

from optparse import OptionParser
from socket import gaierror
from xmlrpclib import Fault, ServerProxy


BREW_SERVICE="https://brewhub.engineering.redhat.com/brewhub"


# filter of the acceptable values for the --type option
TYPES = ("all", "build", "maven", "wrapperRPM")


def group_builds(builds):

    """ given a list of builds, group them by name """

    ret = {}
    for build in builds:
        key = build["name"]
        buildlist = ret.get(key, None)
        if buildlist is None:
            buildlist = list()
            ret[key] = buildlist
        buildlist.append(build)
    return ret
    

def filter_by_type(brewhub, typename, builds):

    """ given a list of buildinfo dicts, will return a list of those
    builds which were created by a task whose method matches
    typename. See the TYPES global for known types.

    This is somewhat expensive and slow, as it needs to look up the
    task info for every item in the builds list. """

    results = list()
    for build in builds:
        task = brewhub.getTaskInfo(build['task_id'])
        if task and task['method'] == typename:
            results.append(build)
    return results

    
def cli(options, release_tag, candidate_tag):
        
    brewhub = ServerProxy(options.brewhub)

    release_builds = brewhub.listTagged(release_tag, 
                                        {'__starstar': True,
                                         'latest': True,
                                         'inherit': options.inherit })

    candidate_builds = brewhub.listTagged(candidate_tag)

    rdict = group_builds(release_builds)
    cdict = group_builds(candidate_builds)
    
    obsolete = list()
    
    for name, builds in rdict.items():
        ref_tid = max(b["task_id"] for b in builds)
        found = cdict.get(name, [])

        for fb in found:
            if options.reverse:
                if fb["task_id"] > ref_tid:
                    obsolete.append(fb)
            else:
                if fb["task_id"] <= ref_tid:
                    obsolete.append(fb)

    # since it takes a task lookup, it's faster to filter by type
    # AFTER doing the comparison
    if options.bytype != "all":
        obsolete = filter_by_type(brewhub, options.bytype, obsolete)

    if not options.quiet:
        if options.reverse:
            msg = ("There are %i builds (type: %s) tagged in %s which are"
                   " newer than a build in %s")
        else:
            msg = ("There are %i builds (type: %s) tagged in %s which are"
                   " obsoleted by a build in %s")
        msg = msg % (len(obsolete), options.bytype, candidate_tag, release_tag)
        print >> sys.stderr, msg
        if len(obsolete):
            print >> sys.stderr, "-" * 40

    # sort builds by name,task_id and print the nvr
    obsolete = [(b['name'],b['task_id'],b) for b in obsolete]
    for _name,_task,b in sorted(obsolete):
        print b['nvr']


def create_optparser():
    parse = OptionParser("%prog [OPTIONS] RELEASE_TAG CANDIDATE_TAG",
                         description="Find obsoleted builds left in a"
                         " candidate tag")

    parse.add_option("--reverse", action="store_true", default=False,
                     help="reverse behavior, thus showing only builds in"
                     " the candidate tag which are newer than in the"
                     " release tag")

    parse.add_option("--inherit", action="store_true", default=False,
                     help="look through the entire inheritance of the"
                     " release tag for builds")

    parse.add_option("--type", action="store", dest="bytype",
                     type="choice", choices=TYPES, default="all",
                     help="filter by a single task type: build, maven,"
                     " wrapperRPM. Default: all")

    parse.add_option("--brewhub", action="store", default=BREW_SERVICE,
                     help="URI for the brewhub service")

    parse.add_option("--quiet", action="store_true",
                     help="do not print summary information")

    return parse


def main(args):
    parser = create_optparser()
    options, args = parser.parse_args(args)
    
    if len(args) > 3:
        parser.error("Too many arguments: please specify only a release"
                    " tag name and a candidate tag name")

    elif len(args) < 3:
        parser.error("Not enough arguments: please specify both a release"
                     " tag name and a candidate tag name")

    name, release, candidate = args

    try:
        cli(options, release, candidate)
        
    except KeyboardInterrupt, ki:
        return 130
        
    except Fault, xmlf:
        print >> sys.stderr, xmlf.faultString
        return -1

    except gaierror, dns:
        print >> sys.stderr, dns.message
        print >> sys.stderr, "Try using --brewhub with an IP address"
        return -2

    else:
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))


#
# The end.
