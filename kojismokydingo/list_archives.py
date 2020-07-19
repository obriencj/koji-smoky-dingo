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


from __future__ import print_function

from fnmatch import fnmatch
from koji import PathInfo
from os.path import join

from . import AnonSmokyDingo, NoSuchBuild, NoSuchTag


def gather_build_archives(session, binfo, btype, path=None,
                          pattern=None, signature=None):

    pathinfo = PathInfo(path or "")

    if btype == "rpm":
        build_path = pathinfo.typedir(binfo, btype)
        found = session.listArchives(buildID=binfo["id"], type=btype)
        for f in found:
            f["filepath"] = join(build_path, pathinfo.rpm(f))

    elif btype == "maven":
        build_path = pathinfo.typedir(binfo, btype)
        found = session.listArchives(buildID=binfo["id"], type=btype)
        for f in found:
            f["filepath"] = join(build_path, pathinfo.mavenfile(f))

    elif btype == "win":
        build_path = pathinfo.typedir(binfo, btype)
        found = session.listArchives(buildID=binfo["id"], type=btype)
        for f in found:
            f["filepath"] = join(build_path, pathinfo.winfile(f))

    else:
        known_btypes = ("rpm", "maven", "win")
        found = []

        if btype is None:
            # this may look redundant, but specifying the individual
            # btypes to the listArchives call will result in
            # additional data returned from koji for some types. Also,
            # the individual types have different path expansions.
            # Therefore we call those types first. Later we'll use a
            # btype of None to get all the archives, and we will
            # filter out the types we've already processed.

            for btype in known_btypes:
                found.extend(gather_build_archives(session, binfo, btype,
                                                   path, pattern, signature))

        archives = session.listArchives(buildID=binfo["id"], type=btype)
        for f in archives:
            abtype = f["btype"]
            if abtype in known_types:
                continue

            build_path = pathinfo.typedir(binfo, abtype)
            f["filepath"] = join(build_path, apath)

            found.append(archive)

    # TODO: additional filtering
    return found


def _fake_maven_build(archive, pathinfo, btype="maven", cache={}):
    """
    produces something that looks like a build info dict based on the
    values from within a maven archive dict.
    """

    bid = archive["build_id"]
    if bid in cache:
        return cache[bid]

    bld = {
        "id": bid,
        "name": archive["build_name"],
        "version": archive["build_version"],
        "release": archive["build_release"],
        "epoch": archive["build_epoch"],
        "volume_id": archive["volume_id"],
        "volume_name": archive["volume_name"],
        "package_id": archive["pkg_id"],
        "package_name": archive["build_name"],
    }
    bld["build_path"] = pathinfo.typedir(bld, btype)
    cache[bid] = bld

    return bld


def gather_tag_archives(session, tagname, btype, path=None,
                        pattern=None, signature=None):

    pathinfo = PathInfo(path or "")

    if btype == "rpm":
        found, builds = session.getLatestRPMS(tagname)

        # decorate the build info with its path data
        for bld in builds:
            bld["build_path"] = pathinfo.typedir(bld, btype)

        builds = dict((bld["id"], bld) for bld in builds)

        for f in found:
            bld = builds[f["build_id"]]
            f["filepath"] = join(bld["build_path"], pathinfo.rpm(f))

    elif btype == "maven":
        found = session.getLatestMavenArchives(tagname)
        for f in found:
            bld = _fake_maven_build(f, pathinfo)
            f["filepath"] = join(bld["build_path"], pathinfo.mavenfile(f))

    elif btype == "win":
        builds = session.getLatestBuilds(tagname, type=btype)
        found = []
        for bld in builds:
            archives = session.listArchives(buildID=bld["id"], type=btype)
            for f in archives:
                build_path = pathinfo.typedir(bld, btype)
                f["filepath"] = join(build_path, pathinfo.winfile(f))
            found.extend(archives)

    else:
        known_btypes = ("rpm", "maven", "win")
        found = []

        if btype is None:
            # We're searching for all btypes, but these types have
            # special path handling, so let's get them out of the way
            # first.
            for btype in known_btypes:
                found.extend(gather_tag_archives(session, tagname, btype,
                                                 path, pattern, signature))

        # now only gather archives that are not in the known_types
        builds = session.getLatestBuilds(tagname)
        for bld in builds:
            # TODO: convert this into a multicall chunking generator
            archives = session.listArchives(buildID=bld["id"])
            for archive in archives:
                abtype = archive["btype"]
                if abtype in known_btypes:
                    continue

                build_path = pathinfo.typedir(bld, abtype)
                archive["filepath"] = join(build_path, archive["filename"])
                found.append(archive)

    # TODO: additional filtering
    return found


def cli_list_build_archives(session, nvr, btype,
                             path=None, pattern=None, signature=None):

    # quick sanity check, and we'll work with the build info rather
    # than the NVR from here on out
    binfo = session.getBuild(nvr)
    if not binfo:
        raise NoSuchBuild(nvr)

    found = gather_build_archives(session, binfo, btype,
                                  path, pattern, signature)

    for f in found:
        print(f["filepath"])


def cli_list_tag_archives(session, tagname, btype,
                           path=None, pattern=None, signature=None):

    # quick sanity check
    tinfo = session.getTag(tagname)
    if not tinfo:
        raise NoSuchTag(tagname)

    found = gather_tag_archives(session, tagname, btype,
                                path, pattern, signature)

    for f in found:
        print(f["filepath"])


def _shared_args(goptions, parser):

    grp = parser.add_argument_group("Filtering options")
    addarg = grp.add_argument

    addarg("--btype", action="store", default=None,
           help="Only show archives for the given btype")

    addarg("--glob", action="store", default=None,
           help="Only show archives matching the given filename glob")

    addarg("--signature", "-S", action="append", default=[],
           help="Only show archives signed with the given key. Can"
           " be specified multiple times to indicate any of the keys"
           " is valid. Preferrence is in order defined. Only applies"
           " to RPMs")

    addarg("--unsigned", dest="signature",
           action="append_const", const=None,
           help="Fall-back to unsigned copies if no signed copies are"
           " found when --signature=[SIG] is specified")

    grp = parser.add_mutually_exclusive_group()
    addarg = grp.add_argument

    addarg("--path", action="store", default=None)

    addarg("--files", "-F", action="store_const",
           dest="path", const=goptions.topdir,
           help="Present as file paths")

    addarg("--urls", "-U", action="store_const",
           dest="path", const=goptions.topurl,
           help="Present as URLs")

    return parser


class cli_build(AnonSmokyDingo):

    group = "info"
    description = "List archives from a build"


    def parser(self):
        parser = super(cli_build, self).parser()
        addarg = parser.add_argument

        addarg("nvr", metavar="NVR",
               help="The NVR containing the archives")

        return _shared_args(self.goptions, parser)


    def handle(self, options):
        return cli_list_build_archives(self.session, options.nvr,
                                       btype=options.btype,
                                       path=options.path,
                                       pattern=options.glob,
                                       signature=options.signature)


class cli_tag(AnonSmokyDingo):

    group = "info"
    description = "List archives from a tag"


    def parser(self):
        parser = super(cli_tag, self).parser()
        addarg = parser.add_argument

        addarg("tag", metavar="TAGNAME",
               help="The tag containing the archives")

        return _shared_args(self.goptions, parser)


    def handle(self, options):
        return cli_list_tag_archives(self.session, options.tag,
                                     btype=options.btype,
                                     path=options.path,
                                     pattern=options.glob,
                                     signature=options.signature)


#
# The end.
