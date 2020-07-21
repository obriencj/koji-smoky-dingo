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
from six import iterkeys, iteritems

from . import AnonSmokyDingo, NoSuchBuild, NoSuchTag, bulk_load_rpm_sigs
from .common import pretty_json, resplit


def filter_archives(session, archives, archive_types):
    # convert the list of string extensions from atypes into a set of
    # archive type IDs
    session.multicall = True
    for t in archive_types:
        session.getArchiveType(t)
    atypes = session.multiCall()
    atypes = set(t[0]["id"] for t in atypes if t and t[0])

    # RPM is a special type, which isn't considered an archive but
    # rather its own first-class type. However, we want to pretend
    # like it's any other archive type, so we'll give it the otherwise
    # unused ID of 0
    if "rpm" in archive_types:
        atypes.add(0)

    # find only those archives whose type_id is in the set of desired
    # archive types
    result = []
    for archive in archives:
        if archive["type_id"] in atypes:
            result.append(archive)

    return result


def gather_signed_rpms(session, archives, sigkeys):
    if not sigkeys:
        return archives

    results = []

    # an ID: RPM Archive mapping
    rpms = dict((rpm["id"], rpm) for rpm in archives)

    # now bulk load all the sigs for each RPM ID
    rpm_sigs = bulk_load_rpm_sigs(session, iterkeys(rpms))

    for rpm_id, rpm in iteritems(rpms):
        found = set(sig["sigkey"] for sig in rpm_sigs[rpm_id])
        for wanted in sigkeys:
            if wanted in found:
                rpm["sigkey"] = wanted
                results.append(rpm)
                break

    return results


def gather_build_archives(session, binfo, btype,
                          rpmkeys=(), path=None):

    bid = binfo["id"]
    pathinfo = PathInfo(path or "")

    if btype == "rpm":
        build_path = pathinfo.typedir(binfo, btype)
        found = session.listRPMs(buildID=bid)
        if rpmkeys:
            found = gather_signed_rpms(session, found, rpmkeys)
        for f in found:
            key = f["sigkey"] if rpmkeys else None
            rpmpath = pathinfo.signed(f, key) if key else pathinfo.rpm(f)
            f["filepath"] = join(build_path, rpmpath)

            # fake some archive members, since RPMs are missing these
            f["type_id"] = 0
            f["type_name"] = "rpm"

    elif btype == "maven":
        build_path = pathinfo.typedir(binfo, btype)
        found = session.listArchives(buildID=bid, type=btype)
        for f in found:
            f["filepath"] = join(build_path, pathinfo.mavenfile(f))

    elif btype == "win":
        build_path = pathinfo.typedir(binfo, btype)
        found = session.listArchives(buildID=bid, type=btype)
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

            for bt in known_btypes:
                found.extend(gather_build_archives(session, binfo,
                                                   bt, rpmkeys, path))

        archives = session.listArchives(buildID=bid, type=btype)
        for f in archives:
            abtype = f["btype"]
            if abtype in known_types:
                continue

            build_path = pathinfo.typedir(binfo, abtype)
            f["filepath"] = join(build_path, apath)

            found.append(archive)

    return found


def _fake_maven_build(archive, pathinfo, btype="maven", cache={}):
    """
    produces something that looks like a build info dict based on the
    values from within a maven archive dict. This can then be used
    with a koji.PathInfo instance to determine the path to a build
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


def gather_latest_archives(session, tagname, btype,
                           rpmkeys=(), path=None):

    pathinfo = PathInfo(path or "")

    if btype == "rpm":
        found, builds = session.getLatestRPMS(tagname)

        # decorate the build info with its path data
        for bld in builds:
            bld["build_path"] = pathinfo.typedir(bld, btype)

        builds = dict((bld["id"], bld) for bld in builds)

        if rpmkeys:
            found = gather_signed_rpms(session, found, rpmkeys)

        for f in found:
            bld = builds[f["build_id"]]
            key = f["sigkey"] if rpmkeys else None
            rpmpath = pathinfo.signed(f, key) if key else pathinfo.rpm(f)
            f["filepath"] = join(bld["build_path"], rpmpath)

            # fake some archive members, since RPMs are missing these
            f["type_id"] = 0
            f["type_name"] = "rpm"

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
            for bt in known_btypes:
                found.extend(gather_latest_archives(session, tagname,
                                                    bt, rpmkeys, path))

        # now only gather archives that are not in the known_types
        builds = session.getLatestBuilds(tagname)
        for bld in builds:
            # TODO: convert this into a multicall chunking generator
            archives = session.listArchives(buildID=bld["id"], type=btype)
            for archive in archives:
                abtype = archive["btype"]
                if abtype in known_btypes:
                    continue

                build_path = pathinfo.typedir(bld, abtype)
                archive["filepath"] = join(build_path, archive["filename"])
                found.append(archive)

    return found


def cli_list_build_archives(session, nvr, btype,
                            atypes=(), rpmkeys=(),
                            path=None, json=False):

    # quick sanity check, and we'll work with the build info rather
    # than the NVR from here on out
    binfo = session.getBuild(nvr)
    if not binfo:
        raise NoSuchBuild(nvr)

    found = gather_build_archives(session, binfo, btype,
                                  rpmkeys, path)

    if atypes:
        found = filter_archives(session, found, atypes)

    if json:
        pretty_json(found)

    else:
        for f in found:
            print(f["filepath"])


def cli_latest_tag_archives(session, tagname, btype,
                            atypes=(), rpmkeys=(),
                            path=None, json=False):

    # quick sanity check
    tinfo = session.getTag(tagname)
    if not tinfo:
        raise NoSuchTag(tagname)

    found = gather_latest_archives(session, tagname, btype,
                                   rpmkeys, path)

    if atypes:
        found = filter_archives(session, found, atypes)

    if json:
        pretty_json(found)

    else:
        for f in found:
            print(f["filepath"])


def _shared_args(goptions, parser):

    addarg = parser.add_argument
    addarg("--json", action="store_true", default=False,
           help="Output archive information as JSON")

    addarg("--urls", "-U", action="store_const",
           dest="path", const=goptions.topurl, default=goptions.topdir,
           help="Present archives as URLs using the configured topurl."
           " Default: use the configured topdir")

    grp = parser.add_argument_group("Build Filtering Options")
    grp = grp.add_mutually_exclusive_group()
    addarg = grp.add_argument

    addarg("--build-type", action="store", metavar="TYPE",
           dest="btype", default=None,
           help="Only show archives for the given build type. Example"
           " types are rpm, maven, image, win. Default: show all"
           " archives.")

    addarg("--rpm", action="store_const", dest="btype",
           const="rpm",
           help="--build-type=rpm")

    addarg("--maven", action="store_const", dest="btype",
           const="maven",
           help="--build-type=maven")

    addarg("--image", action="store_const", dest="btype",
           const="image",
           help="--build-type=image")

    addarg("--win", action="store_const", dest="btype",
           const="win",
           help="--build-type=win")

    grp = parser.add_argument_group("Archive Filtering Options")
    addarg = grp.add_argument

    addarg("--archive-type", "-a", action="append", metavar="EXT",
           dest="atypes", default=[],
           help="Only show archives with the given archive type."
           " Can be specified multiple times. Default: show all")

    grp = parser.add_argument_group("RPM Options")
    addarg = grp.add_argument

    addarg("--key", "-k", dest="keys", metavar="KEY",
           action="append", default=[],
           help="Only show RPMs signed with the given key. Can be"
           " specified multiple times to indicate any of the keys is"
           " valid. Preferrence is in order defined. Default: show"
           " unsigned RPMs")

    addarg("--unsigned", action="store_true",
           help="Allow unsigned copies if no signed copies are"
           " found when --key=KEY is specified. Otherwise if keys are"
           " specified, then only RPMs signed with one of those keys"
           " are shown.")

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


    def validate(self, parser, options):
        options.atypes = resplit(options.atypes)

        keys = resplit(options.keys)
        if keys and options.unsigned:
            keys.append('')
        options.keys = keys


    def handle(self, options):
        return cli_list_build_archives(self.session, options.nvr,
                                       btype=options.btype,
                                       atypes=options.atypes,
                                       rpmkeys=options.keys,
                                       path=options.path,
                                       json=options.json)


class cli_tag(AnonSmokyDingo):

    group = "info"
    description = "List latest archives from a tag"


    def parser(self):
        parser = super(cli_tag, self).parser()
        addarg = parser.add_argument

        addarg("tag", metavar="TAGNAME",
               help="The tag containing the archives")

        return _shared_args(self.goptions, parser)


    def validate(self, parser, options):
        options.atypes = resplit(options.atypes)

        keys = resplit(options.keys)
        if keys and options.unsigned:
            keys.append('')
        options.keys = keys


    def handle(self, options):
        return cli_latest_tag_archives(self.session, options.tag,
                                       btype=options.btype,
                                       atypes=options.atypes,
                                       rpmkeys=options.keys,
                                       path=options.path,
                                       json=options.json)


#
# The end.
