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

from koji import PathInfo
from os.path import join

from . import AnonSmokyDingo


def gather_build_artifacts(session, nvr,
                           btype=None, path=None,
                           pattern=None, signature=None):
    pass


def gather_tag_artifacts(session, tagname, btype, path=None,
                         pattern=None, signature=None):

    pathinfo = PathInfo(path or "")

    if btype == "rpm":
        found, builds = session.getLatestRPMS(tagname)

        # decorate the build info with its path data
        for bld in builds:
            bld["build_path"] = pathinfo.typedir(bld, btype)

        builds = dict((bld["id"], bld) for bld in builds)

        for f in found:
            bld = builds["build_id"]
            f["filepath"] = join(bld["build_path"], pathinfo.rpm(f))

    elif btype == "maven":
        found = session.getLatestMavenArchives(tagname)
        for f in found:
            f["filepath"] = pathinfo.mavenfile(f)

    else:
        builds = session.getLatestBuilds(tagname)
        found = []
        for bld in builds:
            build_path = pathinfo.typedir(bld, btype)
            archives = session.listArchives(buildID=bld["id"], type=btype)
            for archive in archives:
                archive["filepath"] = join(build_path, archive["filename"])

            found.extend(archives)

    # TODO: additional filtering
    return found


def cli_list_build_artifacts(session, nvr):
    pass


def cli_list_tag_artifacts(session, tagname, btype,
                           path=None, pattern=None, signature=None):

    found = gather_tag_artifacts(session, tagname, btype,
                                 path, pattern, signature)

    for f in found:
        print(f["filepath"])


def _shared_args(goptions, parser):

    grp = parser.add_argument_group("Filtering options")
    addarg = grp.add_argument

    addarg("--btype", action="store", default=None,
           help="Only show artifacts for the given btype")

    addarg("--glob", action="store", default=None,
           help="Only show artifacts matching the given filename glob")

    addarg("--signature", "-S", action="append", default=[],
           help="Only show artifacts signed with the given key. Can"
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
    description = "List artifacts from a build"


    def parser(self):
        parser = super(cli_build, self).parser()
        addarg = parser.add_argument

        addarg("nvr", metavar="NVR",
               help="The NVR containing the artifacts")

        return _shared_args(self.goptions, parser)


    def handle(self, options):
        return cli_list_build_artifacts(self.session, options.nvr,
                                        btype=options.btype,
                                        path=options.path,
                                        pattern=options.glob,
                                        signature=options.signature)


class cli_tag(AnonSmokyDingo):

    group = "info"
    description = "List artifacts from a tag"


    def parser(self):
        parser = super(cli_tag, self).parser()
        addarg = parser.add_argument

        addarg("tag", metavar="TAGNAME",
               help="The tag containing the artifacts")

        return _shared_args(self.goptions, parser)


    def handle(self, options):
        return cli_list_tag_artifacts(self.session, options.tag,
                                      btype=options.btype,
                                      path=options.path,
                                      pattern=options.glob,
                                      signature=options.signature)


#
# The end.
