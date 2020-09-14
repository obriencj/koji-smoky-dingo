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
    bulk_load, bulk_load_builds, bulk_load_tags)
from ..builds import (
    BuildFilter,
    as_buildinfo,
    build_dedup, build_id_sort, build_nvr_sort,
    decorate_build_archive_data, filter_imported,
    gather_component_build_ids, iter_bulk_tag_builds)
from ..tags import gather_tag_ids
from ..common import chunkseq, unique


SORT_BY_ID = "sort-by-id"
SORT_BY_NVR = "sort-by-nvr"


def cli_bulk_tag_builds(session, tagname, nvrs,
                        sorting=None,
                        owner=None, inherit=False,
                        force=False, notify=False,
                        verbose=False, strict=False):

    # set up the verbose debugging output function
    if verbose:
        def debug(message, *args):
            printerr(message % args)
    else:
        def debug(message, *args):
            pass

    # fetch the destination tag info (and make sure it actually
    # exists)
    taginfo = session.getTag(tagname)
    if not taginfo:
        raise NoSuchTag(tagname)
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
    builds = bulk_load_builds(session, unique(nvrs), err=strict)
    builds = itervalues(builds)

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


    def parser(self):
        argp = super(BulkTagBuilds, self).parser()
        addarg = argp.add_argument

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

        group = argp.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--nvr-sort", action="store_const",
               dest="sorting", const=SORT_BY_NVR, default=None,
               help="pre-sort build list by NVR, so highest NVR is"
               " tagged last")

        addarg("--id-sort", action="store_const",
               dest="sorting", const=SORT_BY_ID, default=None,
               help="pre-sort build list by build ID, so most recently"
               " completed build is tagged last")

        return argp


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


def cli_list_imported(session, tagname=None, nvr_list=None,
                      inherit=False, negate=False,
                      cg_list=()):

    """
    CLI handler for `koji list-imported`
    """

    if nvr_list:
        nvr_list = unique(nvr_list)
        builds = bulk_load_builds(session, nvr_list, err=True)
        builds = list(itervalues(builds))

    elif tagname:
        taginfo = session.getTag(tagname)
        if not taginfo:
            raise NoSuchTag(tagname)

        builds = session.listTagged(taginfo["id"], inherit=inherit)

    else:
        # from the CLI, one of these should be specified.
        builds = ()

    if cg_list or not negate:
        # we'll be trying to match content generators, which will
        # require us doing some extra work to actually determine what
        # content generators were used to produce a build. This will
        # mean digging through every archive in every build, then
        # finding the buildroots for each... so we only want to do
        # this if we'll actually be using the additional info!
        decorate_build_archive_data(session, builds,
                                    with_cg=bool(cg_list))

    for build in filter_imported(builds, by_cg=cg_list, negate=negate):
        print(build["nvr"])


class ListImported(AnonSmokyDingo):

    description = "Detect imported builds"


    def parser(self):
        argp = super(ListImported, self).parser()

        group = argp.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("tag", nargs="?", action="store", default=None,
               metavar="TAGNAME",
               help="Tag containing builds to check.")

        addarg("-f", "--file", action="store", default=None,
               dest="nvr_file", metavar="NVR_FILE",
               help="Read list of builds from file, one NVR per line."
               " Set to - to read from stdin.")

        addarg = argp.add_argument

        addarg("-i", "--inherit", action="store_true", default=False,
               help="also scan any parent tags when checking"
               " for imported builds")

        addarg("-n", "--negate", action="store_true", default=False,
               help="inverted behavior, list non-imports instead"
               " of imports")

        addarg("-c", "--content-generator", dest="cg_list",
               action="append", default=list(),
               metavar="CG_NAME",
               help="show content generator imports by build"
               " system name. Default: display no CG builds."
               " Specify 'any' to see CG imports from any system."
               " May be specified more than once.")

        return argp


    def validate(self, parser, options):
        if not (options.tag or options.nvr_file):
            parser.error("Please specify either a tag to scan, or"
                         " --file=NVR_FILE")

        options.cg_list = resplit(options.cg_list)

        try:
            options.nvr_list = read_clean_lines(options.nvr_file)
        except IOError as ioe:
            parser.error("Unable to read NVR list %s" % ioe)


    def handle(self, options):
        nvr_list = read_clean_lines(options.nvr_file)

        return cli_list_imported(self.session,
                                 tagname=options.tag,
                                 nvr_list=nvr_list,
                                 inherit=options.inherit,
                                 negate=options.negate,
                                 cg_list=options.cg_list)


class BuildFiltering(AnonSmokyDingo):

    def parser(self):
        parser = super(BuildFiltering, self).parser()

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

        return parser


def cli_list_components(session, nvr_list, task=False,
                        limit=(), shallow_limit=(),
                        lookaside=(), shallow_lookaside=(),
                        imported=None, cg_list=(),
                        btypes=(),
                        sorting=None):

    if not nvr_list:
        return

    # setup the limit as a set of IDs for each tag named in the
    # options.
    limit_ids = gather_tag_ids(session, deep=limit,
                               shallow=shallow_limit)

    # setup the lookaside as a set of IDs for the tags in the
    # flattened inheritance of each tag named in the options.
    lookaside_ids = gather_tag_ids(session, deep=lookaside,
                                   shallow=shallow_lookaside)

    bf = BuildFilter(session,
                     limit_tag_ids=limit_ids,
                     lookaside_tag_ids=lookaside_ids,
                     imported=imported,
                     cg_list=cg_list,
                     btypes=btypes)

    if task:
        print("Not yet implemented")
        return 1

    else:
        # load the initial set of builds, this also verifies our input
        loaded = bulk_load_builds(session, nvr_list)

        # load the components for each of those builds
        bids = [b["id"] for b in itervalues(loaded)]
        components = gather_component_build_ids(session, bids)

        # now we need to turn those components build IDs into build_infos
        bids = chain(*itervalues(components))
        builds = bulk_load_builds(session, bids)

    # do the filtering
    builds = bf(itervalues(builds))

    if sorting == SORT_BY_NVR:
        builds = build_nvr_sort(builds)

    elif sorting == SORT_BY_ID:
        builds = build_id_sort(builds)

    # print("Identified %i components of %s:" % (len(builds), nvr))
    for binfo in builds:
        print(binfo["nvr"])


class ListComponents(BuildFiltering):

    description = "List a build's component dependencies"


    def parser(self):
        parser = super(ListComponents, self).parser()
        addarg = parser.add_argument

        addarg("nvr", nargs="*",
               help="Build NVR to list components of")

        addarg("-f", "--file", action="store", default=None,
               dest="nvr_file", metavar="NVR_FILE",
               help="Read list of builds from file, one NVR per line."
               " Specify - to read from stdin.")

        addarg("--task", action="store_true", default=False,
               help="Specify task IDs instead of build NVRs")

        group = parser.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--nvr-sort", action="store_const",
               dest="sorting", const=SORT_BY_NVR, default=None,
               help="Sort output by NVR in ascending order")

        addarg("--id-sort", action="store_const",
               dest="sorting", const=SORT_BY_ID, default=None,
               help="Sort output by Build ID in ascending order")

        return parser


    def handle(self, options):
        nvrs = list(options.nvr)

        if options.nvr_file:
            nvrs.extend(read_clean_lines(options.nvr_file))

        return cli_list_components(self.session, nvrs,
                                   task=options.task,
                                   limit=options.limit,
                                   shallow_limit=options.shallow_limit,
                                   lookaside=options.lookaside,
                                   shallow_lookaside=options.shallow_lookaside,
                                   imported=options.imported,
                                   cg_list=options.cg_list,
                                   btypes=options.btypes,
                                   sorting=options.sorting)


def cli_filter_builds(session, nvr_list,
                      limit=(), shallow_limit=(),
                      lookaside=(), shallow_lookaside=(),
                      imported=None, cg_list=(),
                      btypes=(),
                      sorting=None):

    # setup the limit as a set of IDs for each tag named in the
    # options.
    limit_ids = gather_tag_ids(session, deep=limit,
                               shallow=shallow_limit)

    # setup the lookaside as a set of IDs for the tags in the
    # flattened inheritance of each tag named in the options.
    lookaside_ids = gather_tag_ids(session, deep=lookaside,
                                   shallow=shallow_lookaside)

    loaded = bulk_load_builds(session, nvr_list)

    bf = BuildFilter(session,
                     limit_tag_ids=limit_ids,
                     lookaside_tag_ids=lookaside_ids,
                     imported=imported,
                     cg_list=cg_list,
                     btypes=btypes)

    builds = bf(itervalues(loaded))

    if sorting == SORT_BY_NVR:
        builds = build_nvr_sort(builds, dedup=False)

    elif sorting == SORT_BY_ID:
        builds = build_id_sort(builds, dedup=False)

    for binfo in builds:
        print(binfo["nvr"])


class FilterBuilds(BuildFiltering):

    description = "Filter a list of NVRs by various criteria"

    def parser(self):
        parser = super(FilterBuilds, self).parser()
        addarg = parser.add_argument

        addarg("nvr", nargs="*", default=[])

        addarg("-f", "--file", action="store", default=None,
               dest="nvr_file", metavar="NVR_FILE",
               help="Read list of builds from file, one NVR per line."
               " Specify - to read from stdin.")

        group = parser.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--nvr-sort", action="store_const",
               dest="sorting", const=SORT_BY_NVR, default=None,
               help="Sort output by NVR in ascending order")

        addarg("--id-sort", action="store_const",
               dest="sorting", const=SORT_BY_ID, default=None,
               help="Sort output by Build ID in ascending order")

        return parser


    def handle(self, options):
        nvrs = list(options.nvr)

        if options.nvr_file:
            nvrs.extend(read_clean_lines(options.nvr_file))

        return cli_filter_builds(self.session, nvrs,
                                 limit=options.limit,
                                 shallow_limit=options.shallow_limit,
                                 lookaside=options.lookaside,
                                 shallow_lookaside=options.shallow_lookaside,
                                 imported=options.imported,
                                 cg_list=options.cg_list,
                                 btypes=options.btypes,
                                 sorting=options.sorting)


#
# The end.
