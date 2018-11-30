#!/usr/bin/env python2


"""
Given a list of NVRs or a --tag=TAG this utility will produce a list
of NVRs which were used to build those released packages.

A --lookaside=TAG can be specified to limit the results to only those
which are not part of another release. This is useful for layered
products which do not want to end up emitting a list of every package
in RHEL that was used to create the buildroot.

author: cobrien@redhat.com
"""


import sys

from itertools import izip
from optparse import OptionParser
from socket import gaierror
from xmlrpclib import Fault, MultiCall, ServerProxy


class NoSuchBuild(Exception):
    pass


class NoSuchTag(Exception):
    pass


class NoSuchTask(Exception):
    pass


BREW_SERVICE = "https://brewhub.engineering.redhat.com/brewhub"


# filter of the acceptable values for the --type option
BUILD_TYPES = ("all", "build", "maven", "wrapperRPM")


# TODO: these are the only sub-task types which can have a
# buildroot. If there are more, add them to this tuple and it should
# Just Work.
BUILDROOT_TASKS = ('buildArch', 'buildMaven', 'wrapperRPM')


def chunk_seq(seq, chunksize):
    return (seq[offset:offset+chunksize] for
            offset in xrange(0, len(seq), chunksize))


def find_task_components(brewhub, task_info, skip_ids=set()):
    """
    Given a task, look up all the component builds and return a dictionary of
    components as {build_id: build_info, ...}

    Omits any build_id from output if it is in the skip_ids set
    """

    method = task_info['method']
    tid = task_info['id']

    # collect all of the tasks for this build which can contain
    # components (RPMs or Maven archives)
    tasks = list()

    if method in ('build', 'maven'):
        ts = brewhub.listTasks({'parent': tid, 'decode': True})
        tasks.extend(t for t in ts if t['method'] in BUILDROOT_TASKS)

    elif method in BUILDROOT_TASKS:
        tasks.append(task_info)

    # collect the build IDs of all the components in all the build
    # roots in all the tasks
    bids = set()

    for task in tasks:

        # Get the buildroot with the highest ID associated with the
        # task. Only the latest one is what we want
        brid = brewhub.listBuildroots({"__starstar": True,
                                       'queryOpts': {'order': '-id',
                                                     'limit': 1},
                                       'taskID': task['id']})[0]['id']

        # some builds are RPM based
        for c in brewhub.listRPMs({'__starstar': True,
                                   'componentBuildrootID': brid}):
            bids.add(c['build_id'])

        # others are maven based
        for c in brewhub.listArchives({'__starstar': True,
                                       'componentBuildrootID': brid}):
            bids.add(c['build_id'])

        # in addition to the above, the wrapperRPM also should be
        # considered dependant on the maven build it is wrapping. Any
        # BR in the spec will have already been brought in by the
        # steps above.
        if task['method'] == 'wrapperRPM':
            c = task['request'][2]
            bids.add(c['id'])

    # don't look up build information for something we've already found
    bids.difference_update(skip_ids)

    # convert all of our build IDs into infos at once
    multicall = MultiCall(brewhub)
    for bid in bids:
        multicall.getBuild(bid)

    # emit the build ID:info pairs
    return izip(bids, multicall())


def find_components(brewhub, build_info, skip_ids=set()):
    """
    Given a build info dictionary, discover the task that generated
    the build and from there find all component archives and RPMs used
    to immediately produce it. skip_ids is an optional set of IDs
    which have already been found, and which we don't need to query
    brew for again.
    """

    tid = build_info['task_id']
    if not tid:
        # imported rather than built. No components for this build
        return ()

    task = brewhub.getTaskInfo(tid, True)
    return find_task_components(brewhub, task, skip_ids)


def collect_inheritance(brewhub, tag):
    """
    given a tag ID, recursively discover all parent tags, and return
    the set of tag IDs in the full inheritance
    """

    return set(t['parent_id'] for t in brewhub.getFullInheritance(tag))


def _debug_on(msg):
    print >> sys.stderr, msg


def _debug_off(msg):
    pass


def _filter_imports(brewhub, newfound, imports):
    """
    Filters a dictionary of {build_id: build_info, ...} by whether or
    not the builds are imports. If imports is True, then all
    non-import builds will be stripped from newfound. If imports is
    False, then all import builds will be stripped from newfound.
    """

    if imports is None:
        return

    for bid, binfo in newfound.items():
        if binfo.get("task_id", None) is None:
            if not imports:
                # this is an import, and we want only non-imports
                newfound.pop(bid)
        elif imports:
            # this is not an import, and we want only imports
            newfound.pop(bid)


def _filter_tags(brewhub, newfound, limit, lookaside):
    """
    Filters a dictionary of {build_id: build_info, ...} by whether or
    not the builds reside in particular tags. limit and lookaside are
    sets of tag IDs. If a build is tagged into a tag in the lookaside,
    then it will be stripped from newfound. If limit is not empty, and
    a build is not tagged into a tag in the limit, then it will be
    stripped from newfound.
    """

    keys = list(newfound.iterkeys())

    # dig up tags for 100 builds at a time in a multicall
    for keychunk in chunk_seq(keys, 100):
        multicall = MultiCall(brewhub)
        for bid in keychunk:
            multicall.listTags(bid)

        for bid, btags in izip(keychunk, multicall()):
            # we only want the tag IDs
            btags = set(t['id'] for t in btags)

            if limit and btags.isdisjoint(limit):
                # don't want it, not tagged in the limit
                newfound.pop(bid)
            elif not btags.isdisjoint(lookaside):
                # don't want it, it's in the lookaside
                newfound.pop(bid)


def _filter_types(brewhub, newfound, buildtypes):
    """
    Filters a dictionary of {build_id: build_info, ...} by whether or
    not the builds are produced by a particular task type. Since
    imported builds have no associated task, they are not impacted by
    this filtering. If that method of a build's task is not a member
    of the buildtypes list, then it will be removed from newfound.
    """

    keys = list(newfound.iterkeys())

    # be polite about all these task lookups, get them 100 at a
    # time to prevent hangups
    for keychunk in chunk_seq(keys, 100):

        # We don't try and search a taskinfo for builds without a
        # task_id. That means we also can't izip the keychunk with the
        # multicall results anymore -- hence we need to collect a list
        # of build IDs that we're actually searching on.
        searched = []

        multicall = MultiCall(brewhub)
        for bid in keychunk:
            binfo = newfound[bid]
            if binfo.get("task_id", None) is not None:
                searched.append(bid)
                multicall.getTaskInfo(binfo["task_id"], False)

        for bid, task in izip(searched, multicall()):
            # print bid, task['method'], buildtypes
            if task and task['method'] not in buildtypes:
                newfound.pop(bid)


def filter_found_builds(brewhub, newfound, debug,
                        limit=set(), lookaside=set(),
                        imports=None, buildtypes=()):
    """
    Given a brewhub connection and a dictionary of builds, filter out
    unwanted builds from the dictionary.  If limit is specified, then
    only builds in the list of tags inside the limit are allowed. If
    lookaside is specified, then only builds which are not in the
    lookaside tags are allowed. If imports is True then only imports,
    if imports is False, then only non-imports, if imports is None
    then either. If buildtypes, then only the builds with a task
    method matching will be allowed.
    """

    # fastest filter is checking for imports, so let's do that first.
    # the imports param is either None, True, or False. None means we
    # don't care whether it's an import or not. True means only
    # imports (so filter out non-imports. False means only non-imports
    # (so filter out imports).
    if imports is not None:
        # debug("filtering by import status")
        _filter_imports(brewhub, newfound, imports)

    # next fastest step is getting the tags for each build, so let's
    # do that filtering if we can
    if limit or lookaside:
        # debug("filtering by component builds' tags")
        _filter_tags(brewhub, newfound, limit, lookaside)

    # the slowest filtering operation is by build type. if buildtypes
    # is empty or contains "all", then we aren't doing that type of
    # filtering.  Otherwise, we're going to look at the taskinfo for
    # each build, and drop any with a task method that doesn't match.
    if buildtypes and "all" not in buildtypes:
        # debug("filtering by component builds' types")
        _filter_types(brewhub, newfound, buildtypes)


def cli(options, nvr_list):

    brewhub = ServerProxy(options.brewhub)

    debug = _debug_on if options.debug else _debug_off

    # setup the lookaside as a set of IDs for the tags in the
    # flattened inheritance of each tag named in the options.
    lookaside = set()
    for ltag in options.lookaside:
        tag = brewhub.getTag(ltag)
        if not tag:
            raise NoSuchTag(ltag)
        lookaside.add(tag['id'])
        lookaside.update(collect_inheritance(brewhub, ltag))

    for ltag in options.shallow_lookaside:
        tag = brewhub.getTag(ltag)
        if not tag:
            raise NoSuchTag(ltag)
        lookaside.add(tag['id'])

    # setup the limit as a set of IDs for each tag named in the
    # options.
    limit = set()
    for ltag in options.limit:
        tag = brewhub.getTag(ltag)
        if not tag:
            raise NoSuchTag(ltag)
        limit.add(tag['id'])
        limit.update(collect_inheritance(brewhub, ltag))

    for ltag in options.shallow_limit:
        tag = brewhub.getTag(ltag)
        if not tag:
            raise NoSuchTag(ltag)
        limit.add(tag['id'])

    # this is the id:binfo mapping of the builds we want BRs for
    builds = dict()

    for nvr in nvr_list:
        binfo = brewhub.getBuild(nvr)
        if not binfo:
            raise NoSuchBuild(nvr)
        builds[binfo['id']] = binfo

    for tagname in options.tag:
        tag = brewhub.getTag(tagname)
        if not tag:
            raise NoSuchTag(tagname)
        for binfo in brewhub.listTagged(tag['id']):
            builds[binfo['id']] = binfo

    tasks = list()
    for taskid in options.task:
        task = brewhub.getTaskInfo(int(taskid))
        if not task:
            raise NoSuchTask(taskid)
        else:
            tasks.append(task)

    # this is the id:binfo mapping of builds we have discovered as
    # part of a buildroot.
    found = dict()

    # this is whatever we've found per depth, we bootstrap it for the
    # depth 0 to be our original search builds
    newfound = builds
    skip_ids = set(builds.iterkeys())

    # create a filtering function, since only one argument will be
    # changing between invocations
    def filter_found(found_builds):
        filter_found_builds(brewhub, found_builds, debug,
                            limit=limit, lookaside=lookaside,
                            imports=options.imports,
                            buildtypes=options.bytype)

    if tasks:
        debug("searching for components of %i tasks" % len(tasks))

        for tinfo in tasks:
            comp = dict(find_task_components(brewhub, tinfo, skip_ids))
            skip_ids.update(comp.iterkeys())
            filter_found(comp)
            found.update(comp)

    # find all the components (and optionally all the components of
    # the components, to whatever depth)
    for depth in xrange(0, options.depth+1):

        searchspace = newfound.values()
        newfound = dict()

        debug("searching for components of %i builds" % len(searchspace))

        # fill newfound with the components of the buildroots of
        # every build in the prior round's discovered components.
        for binfo in searchspace:
            comp = dict(find_components(brewhub, binfo, skip_ids))

            # for every component we found, add that component to the
            # skip_ids so we don't ever consider it again
            skip_ids.update(comp.iterkeys())

            # now filter the components, then add whatever remains to the
            # growing collection in newfound
            filter_found(comp)
            newfound.update(comp)

            debug(" + %i components of %s" % (len(comp), binfo['nvr']))

        debug(" = %i components at depth %i" % (len(newfound), depth))

        # add whatever we found at this depth to the final collection
        # of components
        found.update(newfound)

    # finally, print out any build NVRs, sorted by name and ID
    for _n, _i, nvr in sorted((binfo['name'], bid, binfo['nvr'])
                              for bid, binfo in found.iteritems()):
        print nvr


def create_optparser():
    parse = OptionParser("%prog [OPTIONS] [NVR [NVR...]]",
                         description="Find component builds for"
                         " a list of NVRs or an entire tag.")

    parse.add_option("--tag", action="append", default=list(),
                     help="Find BRs for all builds in TAG. Can be specified"
                     " multiple times. Does not follow inheritance")

    parse.add_option("--lookaside", action="append", default=list(),
                     help="Tag name to filter BRs from. Can be specified"
                     " multiple times. Follows inheritance")

    parse.add_option("--shallow-lookaside", action="append", default=list(),
                     help="Tag name to filter BRs from. Can be specified"
                     " multiple times. Does not follow inheritance")

    parse.add_option("--limit", action="append", default=list(),
                     help="Limit BRs to specific tags and their parents."
                     " Can be specified multiple times.")

    parse.add_option("--shallow-limit", action="append", default=list(),
                     help="Limit BRs to specific tags. Can be specified"
                     " multiple times. Does not follow inheritance")

    parse.add_option("--depth", action="store", default=0, type='int',
                     help="Recursive BR seek depth")

    parse.add_option("--brewhub", action="store", default=BREW_SERVICE,
                     help="URI for the brewhub service")

    parse.add_option("--debug", action="store_true", default=False,
                     help="Print debugging output to stderr")

    parse.add_option("--task", action="append", default=list(),
                     help="Find BRs of this task. Can be specified"
                     " multiple times.")

    parse.add_option("--imports", action="store_true", default=None,
                     help="Only list imports")

    parse.add_option("--no-imports", action="store_true", default=None,
                     help="Only list non-imports")

    parse.add_option("--type", action="append", dest="bytype",
                     default=list(), choices=BUILD_TYPES,
                     help="Limit BRs to a specific type (may be specified"
                     "more than once)")

    return parse


def main(args):
    parser = create_optparser()
    options, args = parser.parse_args(args)

    if len(args) < 2 and not options.tag and not options.task:
        parser.error("Please specify a list of NVRs, a tag via the"
                     " --tag=TAG option, or a task via the"
                     " --task=TASK option")

    elif options.depth < 0:
        parser.error("Stop that. Make depth a non-negative integer or I"
                     " will turn this car around and there will be no"
                     " Disney World for anyone.")

    elif options.depth > 5:
        parser.error("You're out of your depth.")

    if options.no_imports:
        if options.imports:
            parser.error("--imports and --no-imports are mutually exclusive")
        else:
            # converge imports and no_imports into just imports
            options.imports = False

    try:
        cli(options, args[1:])

    except KeyboardInterrupt:
        print
        return 130

    except Fault, xmlf:
        print >> sys.stderr, xmlf.faultString
        return -1

    except gaierror, dns:
        print >> sys.stderr, dns.message
        print >> sys.stderr, "Try using --brewhub with an IP address"
        return -2

    except NoSuchTag, nst:
        print >> sys.stderr, "No such tag:", nst.message
        return -3

    except NoSuchBuild, nsb:
        print >> sys.stderr, "No such build:", nsb.message
        return -4

    except NoSuchTask, nstask:
        print >> sys.stderr, "No such task:", nstask.message
        return -5

    else:
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))


#
# The end.
