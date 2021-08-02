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
Koji Smoky Dingo - CLI Client Commands

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import sys

from configparser import ConfigParser
from os import system

from . import AnonSmokyDingo, BadDingo, int_or_str, pretty_json
from .. import (
    as_archiveinfo, as_buildinfo, as_hostinfo, as_rpminfo,
    as_repoinfo, as_taginfo, as_targetinfo, as_taskinfo, as_userinfo, )
from ..clients import rebuild_client_config
from ..common import load_plugin_config


__all__ = (
    "ClientConfig",
    "ClientOpen",

    "cli_client_config",
    "cli_open",
    "get_open_command",
)


def cli_client_config(session, goptions,
                      only=(), quiet=False, config=False, json=False):

    profile, opts = rebuild_client_config(session, goptions)

    if only:
        opts = {k: opts[k] for k in only if k in opts}
    else:
        only = sorted(opts)

    if json:
        pretty_json(opts)
        return

    if config:
        cfg = ConfigParser()
        cfg._sections[profile] = opts
        cfg.write(sys.stdout)
        return

    if quiet:
        for k in only:
            print(opts[k])
    else:
        for k in only:
            print("%s: %s" % (k, opts[k]))

    print()


class ClientConfig(AnonSmokyDingo):

    group = "info"
    description = "Show client profile settings"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("only", nargs="*", default=(),
               metavar="SETTING",
               help="Limit to these settings (default: all settings)")

        grp = parser.add_mutually_exclusive_group()
        addarg = grp.add_argument

        addarg("--quiet", "-q", action="store_true", default=False,
               help="Do not print setting keys")

        addarg("--json", action="store_true", default=False,
               help="Output settings as JSON")

        addarg("--cfg", action="store_true", default=False,
               help="Output settings as a config file")

        return parser


    def activate(self):
        # entirely local, do not even attempt to connect to koji
        pass


    def handle(self, options):
        return cli_client_config(self.session, self.goptions,
                                 only=options.only,
                                 quiet=options.quiet,
                                 config=options.cfg,
                                 json=options.json)


def get_build_dir(session, goptions, buildid):
    topurl = goptions.topurl
    if not topurl:
        raise BadDingo("Client has no topurl configured")
    topurl = topurl.rstrip("/")

    build = as_buildinfo(session, buildid)
    name = build["name"]
    version = build["version"]
    release = build["release"]

    return f"{topurl}/packages/{name}/{version}/{release}"


def get_tag_repo_dir(session, goptions, tagid):
    topurl = goptions.topurl
    if not topurl:
        raise BadDingo("Client has no topurl configured")
    topurl = topurl.rstrip("/")

    tag = as_taginfo(session, tagid)
    repo = as_repoinfo(session, tag)

    return f"{topurl}/repos/{tag['name']}/{repo['id']}"


def get_tag_latest_dir(session, goptions, tagid):
    topurl = goptions.topurl
    if not topurl:
        raise BadDingo("Client has no topurl configured")
    topurl = topurl.rstrip("/")

    tag = as_taginfo(session, tagid)
    as_repoinfo(session, tag)

    return f"{topurl}/repos/{tag['name']}/latest"


OPEN_LOADFN = {
    "archive": as_archiveinfo,
    "build": as_buildinfo,
    "host": as_hostinfo,
    "repo": as_repoinfo,
    "rpm": as_rpminfo,
    "tag": as_taginfo,
    "target": as_targetinfo,
    "task": as_taskinfo,
    "user": as_userinfo,
}


def get_type_url(session, goptions, datatype, fmt, element):

    weburl = goptions.weburl
    if not weburl:
        raise BadDingo("Client has no weburl configured")
    weburl = weburl.rstrip("/")

    loadfn = OPEN_LOADFN.get(datatype)
    if loadfn is None:
        raise BadDingo("Unsupported type for open %s" % datatype)

    loaded = loadfn(session, element)
    typeurl = fmt.format(**loaded)

    return f'{weburl}/{typeurl}'


OPEN_URL = {
    "archive": "archiveinfo?archiveID={id}",
    "build": "buildinfo?buildID={id}",
    "host": "hostinfo?hostID={id}",
    "repo": "repoinfo?repoID={id}",
    "rpm": "rpminfo?rpmID={id}",
    "tag": "taginfo?tagID={id}",
    "target": "buildtargetinfo?targetID={id}",
    "task": "taskinfo?taskID={id}",
    "user": "userinfo?userID={id}",

    "build-dir": get_build_dir,
    "tag-repo-dir": get_tag_repo_dir,
    "tag-latest-dir": get_tag_latest_dir,
}


def get_open_url(session, goptions, datatype, element):

    opener = OPEN_URL.get(datatype)
    if opener is None:
        raise BadDingo(f"Unsupported type for open {datatype}")

    if callable(opener):
        url = opener(session, goptions, element)
    else:
        url = get_type_url(session, goptions, datatype, opener, element)

    return url


OPEN_CMD = {
    "darwin": "open",
    "linux": "xdg-open",
    "win32": "start",
}


def get_open_command(profile=None, err=True):
    """
    Determine the command used to open URLs. Attempts to load
    profile-specific plugin configuration under the heading 'open' and
    the key 'command' first. If that doesn't find a command, then fall
    back to the per-platform mappings in the `OPEN_CMD` dict.

    :param profile: name of koji profile

    :type profile: str, optional

    :param err: raise an exception if no command is discovered. If False
      then will return None instead

    :type err: bool, optional

    :rtype: str

    :raises BadDingo: when `err` is True and no command could be found
    """

    default_command = OPEN_CMD.get(sys.platform)

    conf = load_plugin_config("open", profile)
    command = conf.get("command", default_command)

    if err and command is None:
        raise BadDingo("Unable to determine command for launching browser")

    return command


def cli_open(session, goptions, datatype, element,
             command=None):

    datatype = datatype.lower()

    if command is None:
        command = get_open_command(goptions.profile)

    url = get_open_url(session, goptions, datatype, element)

    # if the configured open command has a {url} marker in it, then we
    # want to swap that in. Otherwise we'll just append it quoted
    if "{url}" in command:
        cmd = command.format(url=url)
    else:
        cmd = f'{command} "{url}"'

    system(cmd)


class ClientOpen(AnonSmokyDingo):

    group = "info"
    description = "Launch web UI for koji data elements"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("datatype", type=str, metavar="TYPE",
               help="The koji data element type. build, tag, target, user,"
               " host, rpm, archive, task")

        addarg("element", type=int_or_str, metavar="KEY",
               help="The key for the given element type.")

        addarg("--command", "-c", default=None, metavar="COMMAND",
               help="Command to exec with the discovered koji web URL")

        return parser


    def validate(self, parser, options):
        # we made it so cli_open will attempt to discover a command if
        # one isn't specified, but we want to do it this way to
        # generate an error unique to this particular command. The
        # `get_open_command` method can be used as a fallback for
        # cases where other commands or plugins want to trigger a URL
        # opening command

        command = options.command

        if not command:
            default_command = OPEN_CMD.get(sys.platform)
            command = self.get_plugin_config("command", default_command)
            options.command = command

        if not command:
            parser.error("Unable to determine a default COMMAND for"
                         " opening URLs.\n"
                         "Please specify via the '--command' option.")


    def handle(self, options):
        command = options.command or self.get_plugin_config("command")

        return cli_open(self.session, self.goptions,
                        datatype=options.datatype,
                        element=options.element,
                        command=command)


#
# The end.
