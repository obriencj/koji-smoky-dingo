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


from __future__ import print_function

import sys

from os import system
from six import iterkeys
from six.moves.configparser import ConfigParser

from . import AnonSmokyDingo, BadDingo, int_or_str, pretty_json
from .. import (
    as_archiveinfo, as_buildinfo, as_channelinfo, as_hostinfo,
    as_packageinfo, as_repoinfo, as_rpminfo, as_taginfo, as_targetinfo,
    as_taskinfo, as_userinfo, )
from ..builds import BUILD_COMPLETE
from ..clients import rebuild_client_config
from ..common import load_plugin_config


__all__ = (
    "CannotOpenURL",
    "ClientConfig",
    "ClientOpen",

    "cli_client_config",
    "cli_open",
    "get_open_command",
    "get_open_url",
)


class CannotOpenURL(BadDingo):
    """
    A problem occured opening a URL

    :since: 1.1
    """

    complaint = "Cannot open URL"


def cli_client_config(session, goptions,
                      only=(), quiet=False, config=False, json=False):
    """
    Implements the ``koji client-config`` command

    :since: 1.0
    """

    profile, opts = rebuild_client_config(session, goptions)

    if only:
        # supporting RHEL 6 means supporting python 2.6, which doesn't
        # have dict comprehensions.
        opts = dict((k, opts[k]) for k in only if k in opts)
    else:
        only = sorted(iterkeys(opts))

    if json:
        pretty_json(opts)
        return

    if config:
        # under python3 we'd just set defaults and the default section
        # name, but koji still operates under python2 (see RHEL 6), so
        # we need to be sure to work under both environments.
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


def _get_build_dir_url(session, goptions, buildid):
    """
    :since: 1.1
    """

    topurl = goptions.topurl

    if not topurl:
        raise CannotOpenURL("Client has no topurl configured")

    topurl = topurl.rstrip("/")

    build = as_buildinfo(session, buildid)

    if build["state"] != BUILD_COMPLETE:
        raise CannotOpenURL("Build directory is not available")

    name = build["name"]
    version = build["version"]
    release = build["release"]

    return "/".join((topurl, "packages", name, version, release))


def _get_tag_repo_dir_url(session, goptions, tagid):
    """
    :since: 1.1
    """

    topurl = goptions.topurl
    if not topurl:
        raise CannotOpenURL("Client has no topurl configured")
    topurl = topurl.rstrip("/")

    tag = as_taginfo(session, tagid)
    repo = as_repoinfo(session, tag)

    return "/".join((topurl, "repos", tag['name'], str(repo['id'])))


def _get_tag_latest_dir_url(session, goptions, tagid):
    """
    :since: 1.1
    """

    topurl = goptions.topurl
    if not topurl:
        raise CannotOpenURL("Client has no topurl configured")
    topurl = topurl.rstrip("/")

    tag = as_taginfo(session, tagid)
    as_repoinfo(session, tag)

    return "/".join((topurl, "repos", tag['name'], "latest"))


OPEN_LOADFN = {
    "archive": as_archiveinfo,
    "build": as_buildinfo,
    "channel": as_channelinfo,
    "host": as_hostinfo,
    "package": as_packageinfo,
    "repo": as_repoinfo,
    "rpm": as_rpminfo,
    "tag": as_taginfo,
    "target": as_targetinfo,
    "task": as_taskinfo,
    "user": as_userinfo,
}


def _get_type_url(session, goptions, datatype, fmt, element):
    """
    :since: 1.1
    """

    weburl = goptions.weburl
    if not weburl:
        raise CannotOpenURL("Client has no weburl configured")
    weburl = weburl.rstrip("/")

    loadfn = OPEN_LOADFN.get(datatype)
    if loadfn is None:
        raise CannotOpenURL("Unsupported type for open %s" % datatype)

    loaded = loadfn(session, element)
    typeurl = fmt.format(**loaded)

    return "/".join((weburl, typeurl))


OPEN_URL = {
    "archive": "archiveinfo?archiveID={id}",
    "build": "buildinfo?buildID={id}",
    "channel": "channelinfo?channelID={id}",
    "host": "hostinfo?hostID={id}",
    "package": "packageinfo?packageID={id}",
    "repo": "repoinfo?repoID={id}",
    "rpm": "rpminfo?rpmID={id}",
    "tag": "taginfo?tagID={id}",
    "target": "buildtargetinfo?targetID={id}",
    "task": "taskinfo?taskID={id}",
    "user": "userinfo?userID={id}",

    "build-dir": _get_build_dir_url,
    "tag-repo-dir": _get_tag_repo_dir_url,
    "tag-latest-dir": _get_tag_latest_dir_url,
}


def get_open_url(session, goptions, datatype, element):
    """
    Given a client configuration, datatype, and element identifier,
    produce a URL referencing the hub or topdir path for that record.

    :param session: an active koji client session

    :param goptions: koji client options

    :param datatype: name of the data type

    :param element: identifier for an element of the given data type

    :since: 1.1
    """

    opener = OPEN_URL.get(datatype)
    if opener is None:
        raise BadDingo("Unsupported type for open: %s" % datatype)

    if callable(opener):
        url = opener(session, goptions, element)
    else:
        url = _get_type_url(session, goptions, datatype, opener, element)

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
        raise BadDingo("Unable to determine default open command")

    return command


def cli_open(session, goptions, datatype, element,
             command=None):
    """
    Implements the ``koji open`` command

    :since: 1.0
    """

    datatype = datatype.lower()

    if command is None:
        command = get_open_command(goptions.profile)

    url = get_open_url(session, goptions, datatype, element)

    # special case triggered by using '-p' or '-c -' just prints URL
    # to stdout
    if command == "-":
        print(url)
        return 0

    # if the configured open command has a {url} marker in it, then we
    # want to swap that in. Otherwise we'll just append it quoted
    if "{url}" in command:
        cmd = command.format(url=url)
    else:
        cmd = '%s "%s"' % (command, url)

    return system(cmd)


class ClientOpen(AnonSmokyDingo):

    group = "info"
    description = "Launch web UI for koji data elements"


    def arguments(self, parser):
        addarg = parser.add_argument

        known = ", ".join(sorted(OPEN_URL))
        hlp = "The koji data element type. Supported types: " + known
        addarg("datatype", type=str, metavar="TYPE", help=hlp)

        addarg("element", type=int_or_str, metavar="KEY",
               help="The key for the given element type.")

        group = parser.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--command", "-c", default=None, metavar="COMMAND",
               help="Command to exec with the discovered koji web URL")

        addarg("--print", "-p", default=None, dest="command",
               action="store_const", const="-",
               help="Print URL to stdout rather than executing a command")

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
