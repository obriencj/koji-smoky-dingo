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
Koji Smoky Dingo - Bulk tagging commands

Allows for large numbers of builds to be tagged rapidly, via multicall
to tagBuildBypass

:author: cobrien@redhat.com
:license: GPL version 3
"""


from __future__ import print_function

import sys

from functools import partial
from itertools import chain
from six import itervalues

from . import (
    AnonSmokyDingo, TagSmokyDingo,
    printerr, read_clean_lines, resplit)
from .. import (
    NoSuchTag, NoSuchUser,
    as_buildinfo, as_taginfo,
    bulk_load, bulk_load_builds, bulk_load_tags)
from ..builds import (
    BuildFilter,
    build_dedup, build_id_sort, build_nvr_sort,
    decorate_build_archive_data, filter_imported,
    gather_component_build_ids, gather_wrapped_builds,
    iter_bulk_tag_builds)
from ..tags import gather_tag_ids
from ..common import chunkseq, unique


SORT_BY_ID = "sort-by-id"
SORT_BY_NVR = "sort-by-nvr"


def cli_bulk_tag_builds(session, tagname, nvrs,
                        sorting=None,
                        owner=None, inherit=False,
                        force=False, notify=False,
                        verbose=False, strict=False):

    """
    CLI handler for `koji bulk-tag-builds`
    """

    # set up the verbose debugging output function
    if verbose:
        def debug(message, *args):
            printerr(message % args)
    else:
        def debug(message, *args):
            pass

    # fetch the destination tag info (and make sure it actually
    # exists)
    taginfo = as_taginfo(session, tagname)
    tagid = taginfo["id"]

    # figure out how we're going to be dealing with builds that don't
    # have a matching pkg entry already. Someone needs to own them...
    ownerid = None
    if owner:
        ownerinfo = session.getUser(owner)
        if not ownerinfo:
            raise NoSuchUser(owner)
        ownerid = ownerinfo["id"]

    # load the buildinfo for all of the NVRs
    debug("Fed with %i builds", len(nvrs))

    # validate our list of NVRs first by attempting to load them
    loaded = bulk_load_builds(session, unique(nvrs), err=strict)
    builds = itervalues(loaded)

    # sort/dedup as requested
    if sorting == SORT_BY_NVR:
        debug("NVR sorting specified")
        builds = build_nvr_sort(builds)
    elif sorting == SORT_BY_ID:
        debug("ID sorting specified")
        builds = build_id_sort(builds)
    else:
        debug("No sorting specified, preserving feed order")
        builds = build_dedup(builds)

    # at this point builds is a list of build info dicts
    if verbose:
        debug("Sorted and trimmed duplicates to %i builds", len(builds))
        for build in builds:
            debug(" %s %i", build["nvr"], build["id"])

    if not builds:
        debug("Nothing to do!")
        return

    # check for missing package listings, and add as necessary
    packages = session.listPackages(tagID=tagid,
                                    inherited=inherit)
    packages = set(pkg["package_id"] for pkg in packages)

    package_todo = []

    for build in builds:
        pkgid = build["package_id"]
        if pkgid not in packages:
            packages.add(pkgid)
            package_todo.append((pkgid, ownerid or build["owner_id"]))

    if package_todo:
        # we've got some package listings that need adding

        debug("Beginning package additions")
        session.multicall = True
        for pkgid, oid in package_todo:
            session.packageListAdd(tagid, pkgid, owner=oid,
                                   force=force)
        done = session.multiCall(strict=strict)

        # verify the results of our add-pkg calls. If strict was set
        # then the multicall would have raised an exception, but we
        # need to present any issues for the non-strict cases as well
        for res, pad in zip(done, package_todo):
            if "faultCode" in res:
                printerr("Error adding package", pad[0],
                         ":", res["faultString"])
        debug("Package additions completed")

    # and finally, tag the builds themselves in chunks of 100
    debug("Begining build tagging")
    counter = 0
    for done in iter_bulk_tag_builds(session, tagid, builds,
                                     force=force, notify=notify,
                                     size=100, strict=strict):

        for build, res in done:
            # same as with the add-pkg -- if strict was True then any
            # issues would raise an exception, but for non-strict
            # invocations we need to present the error messages
            if "faultCode" in res:
                printerr("Error tagging build", build["nvr"],
                         ":", res["faultString"])

        # and of course display the courtesy counter so the user
        # knows we're actually doing something
        counter += len(done)
        debug(" tagged %i/%i", counter, len(builds))

    debug("All done!")


class BulkTagBuilds(TagSmokyDingo):

    group = "bind"
    description = "Quickly tag a large number of builds"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Tag to associate builds with")

        addarg("-v", "--verbose", action="store_true", default=False,
               help="Print debugging information")

        addarg("--owner", action="store", default=None,
               help="Force missing package listings to be created"
               " with the specified owner")

        addarg("--no-inherit", action="store_false", default=True,
               dest="inherit", help="Do not use parent tags to"
               " determine existing package listing.")

        addarg("-f", "--file", action="store", default="-",
               dest="nvr_file", metavar="NVR_FILE",
               help="Read list of builds from file, one NVR per line."
               " Omit for default behavior: read build NVRs from stdin")

        addarg("--strict", action="store_true", default=False,
               help="Stop processing at the first failure")

        addarg("--force", action="store_true", default=False,
               help="Force tagging.")

        addarg("--notify", action="store_true", default=False,
               help="Send tagging notifications.")

        group = parser.add_argument_group("Tagging order of builds")
        group = group.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--nvr-sort", action="store_const",
               dest="sorting", const=SORT_BY_NVR, default=None,
               help="pre-sort build list by NVR, so highest NVR is"
               " tagged last")

        addarg("--id-sort", action="store_const",
               dest="sorting", const=SORT_BY_ID, default=None,
               help="pre-sort build list by build ID, so most recently"
               " completed build is tagged last")

        return parser


    def handle(self, options):
        nvrs = read_clean_lines(options.nvr_file)

        return cli_bulk_tag_builds(self.session, options.tag, nvrs,
                                   sorting=options.sorting,
                                   owner=options.owner,
                                   inherit=options.inherit,
                                   force=options.force,
                                   notify=options.notify,
                                   verbose=options.verbose,
                                   strict=options.strict)


class BuildFiltering():


    def filtering_arguments(self, parser):

        grp = parser.add_argument_group("Filtering by tag")
        addarg = grp.add_argument

        addarg("--lookaside", action="append", default=list(),
               help="Omit builds found in this tag or its parent tags")

        addarg("--shallow-lookaside", action="append", default=list(),
               help="Omit builds found directly in this tag")

        addarg("--limit", action="append", default=list(),
               help="Limit results to builds found in this tag or its"
               " parent tags")

        addarg("--shallow-limit", action="append", default=list(),
               help="Limit results to builds found directly in this tag")

        grp = parser.add_argument_group("Filtering by type")
        addarg = grp.add_argument

        addarg("--type", action="append", dest="btypes",
               default=[],
               help="Limit to builds of this BType")

        addarg("-c", "--content-generator", dest="cg_list",
               action="append", default=list(),
               metavar="CG_NAME",
               help="show content generator imports by build"
               " system name. Default: display no CG builds."
               " Specify 'any' to see CG imports from any system."
               " May be specified more than once.")

        grp = grp.add_mutually_exclusive_group()
        addarg = grp.add_argument
        addarg("--imports", action="store_true",
               dest="imported", default=None,
               help="Limit to imported builds")

        addarg("--no-imports", action="store_false",
               dest="imported", default=None,
               help="Invert the imports checking")

        grp = parser.add_argument_group("Filtering by state")
        grp = grp.add_mutually_exclusive_group()
        addarg = grp.add_argument
        addarg("--completed", action="store_const", const=1,
               dest="state", default=None,
               help="Limit to completed builds")

        addarg("--deleted", action="store_const", const=2,
               dest="state", default=None,
               help="Limit to deleted builds")

        return parser


    def build_filter(self, options):
        session = self.session

        # setup the limit as a set of IDs for each tag named in the
        # options.
        limit_ids = gather_tag_ids(session, deep=options.limit,
                                   shallow=options.shallow_limit)

        # setup the lookaside as a set of IDs for the tags in the
        # flattened inheritance of each tag named in the options.
        lookaside_ids = gather_tag_ids(session, deep=options.lookaside,
                                       shallow=options.shallow_lookaside)

        return BuildFilter(self.session,
                           limit_tag_ids=limit_ids,
                           lookaside_tag_ids=lookaside_ids,
                           imported=options.imported,
                           cg_list=options.cg_list,
                           btypes=options.btypes)


def cli_list_components(session, nvr_list,
                        tag=None, inherit=False, latest=False,
                        build_filter=None, sorting=None):

    """
    CLI handler for `koji list-component-builds`
    """

    nvr_list = unique(nvr_list)

    if nvr_list:
        # load the initial set of builds, this also verifies our input
        found = bulk_load_builds(session, nvr_list)
        loaded = dict((b["id"], b) for b in itervalues(found))

    else:
        loaded = {}

    if tag:
        # mix in any tagged builds
        tag = as_taginfo(session, tag)
        found = session.listTagged(tag["id"], inherit=inherit, latest=latest)
        loaded.update((b["id"], b) for b in found)

    # the build IDs of all the builds we've loaded, combined from the
    # initial nvr_list, plus the builds from tag
    bids = list(loaded)

    # now that we have bids (the build IDs to gather components from)
    # we can begin the real work.
    components = gather_component_build_ids(session, bids)

    # now we need to turn those components build IDs into build_infos
    found = bulk_load_builds(session, chain(*itervalues(components)))

    # we'll also want the underlying builds used to produce any
    # standalone wrapperRPM builds, as those are not recorded as
    # normal buildroot components
    tids = [b["task_id"] for b in itervalues(loaded) if b["task_id"]]
    wrapped = gather_wrapped_builds(session, tids)

    builds = list(itervalues(found))
    builds.extend(itervalues(wrapped))

    # do the filtering
    if build_filter:
        builds = build_filter(builds)

    if sorting == SORT_BY_NVR:
        builds = build_nvr_sort(builds)

    elif sorting == SORT_BY_ID:
        builds = build_id_sort(builds)

    # print("Identified %i components of %s:" % (len(builds), nvr))
    for binfo in builds:
        print(binfo["nvr"])


class ListComponents(AnonSmokyDingo, BuildFiltering):

    description = "List a build's component dependencies"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("nvr", nargs="*",
               help="Build NVR to list components of")

        addarg("-f", "--file", action="store", default=None,
               dest="nvr_file", metavar="NVR_FILE",
               help="Read list of builds from file, one NVR per line."
               " Specify - to read from stdin.")

        group = parser.add_argument_group("Components of tagged builds")
        addarg = group.add_argument

        addarg("--tag", action="store", default=None,
               help="Look for components of builds in this tag")

        addarg("--inherit", action="store_true", default=False,
               help="Follow inheritance")

        addarg("--latest", action="store_true", default=False,
               help="Limit to latest builds")

        group = parser.add_argument_group("Sorting of builds")
        group = group.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--nvr-sort", action="store_const",
               dest="sorting", const=SORT_BY_NVR, default=None,
               help="Sort output by NVR in ascending order")

        addarg("--id-sort", action="store_const",
               dest="sorting", const=SORT_BY_ID, default=None,
               help="Sort output by Build ID in ascending order")

        # additional build filtering arguments
        parser = self.filtering_arguments(parser)

        return parser


    def handle(self, options):
        nvrs = list(options.nvr)

        if options.nvr_file:
            nvrs.extend(read_clean_lines(options.nvr_file))

        bf = self.build_filter(options)

        return cli_list_components(self.session, nvrs,
                                   tag=options.tag,
                                   inherit=options.inherit,
                                   latest=options.latest,
                                   build_filter=bf,
                                   sorting=options.sorting)


def cli_filter_builds(session, nvr_list,
                      tag=None, inherit=False, latest=False,
                      build_filter=None, sorting=None, strict=False):

    """
    CLI handler for `koji filter-builds`
    """

    nvr_list = unique(nvr_list)

    if nvr_list:
        loaded = bulk_load_builds(session, nvr_list, err=strict)
        builds = itervalues(loaded)
    else:
        builds = ()

    if tag:
        taginfo = as_taginfo(session, tag)
        listTagged = partial(session.listTagged, taginfo["id"],
                             inherit=inherit, latest=latest)

        builds = list(builds)

        # server-side optimization if we're doing filtering by btype
        if build_filter and build_filter._btypes:
            for btype in build_filter._btypes:
                builds.extend(listTagged(type=btype))
        else:
            builds.extend(listTagged())

    if build_filter:
        builds = build_filter(builds)

    if sorting == SORT_BY_NVR:
        builds = build_nvr_sort(builds, dedup=False)

    elif sorting == SORT_BY_ID:
        builds = build_id_sort(builds, dedup=False)

    for binfo in builds:
        print(binfo["nvr"])


class FilterBuilds(AnonSmokyDingo, BuildFiltering):

    description = "Filter a list of NVRs by various criteria"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("nvr", nargs="*", default=[])

        addarg("-f", "--file", action="store", default=None,
               dest="nvr_file", metavar="NVR_FILE",
               help="Read list of builds from file, one NVR per line."
               " Specify - to read from stdin.")

        addarg("--strict", action="store_true", default=False,
               help="Error if any of the NVRs do not resolve into a"
               " real build. Otherwise, bad NVRs are ignored.")

        group = parser.add_argument_group("Working from tagged builds")
        addarg = group.add_argument

        addarg("--tag", action="store", default=None,
               help="Filter using the builds in this tag")

        addarg("--inherit", action="store_true", default=False,
               help="Follow inheritance")

        addarg("--latest", action="store_true", default=False,
               help="Limit to latest builds")

        group = parser.add_argument_group("Sorting of output builds")
        group = group.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--nvr-sort", action="store_const",
               dest="sorting", const=SORT_BY_NVR, default=None,
               help="Sort output by NVR in ascending order")

        addarg("--id-sort", action="store_const",
               dest="sorting", const=SORT_BY_ID, default=None,
               help="Sort output by Build ID in ascending order")

        # additional build filtering arguments
        parser = self.filtering_arguments(parser)

        return parser


    def handle(self, options):
        nvrs = list(options.nvr)

        if options.nvr_file:
            nvrs.extend(read_clean_lines(options.nvr_file))

        bf = self.build_filter(options)

        return cli_filter_builds(self.session, nvrs,
                                 build_filter=bf,
                                 tag=options.tag,
                                 inherit=options.inherit,
                                 latest=options.latest,
                                 sorting=options.sorting)


#
# The end.
