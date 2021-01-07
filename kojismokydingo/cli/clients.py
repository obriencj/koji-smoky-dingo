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
    as_buildinfo, as_taginfo, as_targetinfo, as_hostinfo,
    as_taskinfo, as_userinfo, )
from ..clients import rebuild_client_config


def cli_client_config(session, goptions,
                      only=(), quiet=False, config=False, json=False):

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


OPEN_LOADFN = {
    "build": as_buildinfo,
    "tag": as_taginfo,
    "target": as_targetinfo,
    "user": as_userinfo,
    "host": as_hostinfo,
    "task": as_taskinfo,
}


OPEN_CMD = {
    "linux": "xdg-open",
    "darwin": "open",
    "win32": "start",
}


OPEN_URL = {
    "build": "buildinfo?buildID={id}",
    "tag": "taginfo?tagID={id}",
    "target": "buildtargetinfo?targetID={id}",
    "user": "userinfo?userID={id}",
    "host": "hostinfo?hostID={id}",
    "task": "taskinfo?taskID={id}",
}


def cli_open(session, goptions, datatype, element,
             command=None):

    datatype = datatype.lower()

    loadfn = OPEN_LOADFN.get(datatype)
    if loadfn is None:
        raise BadDingo("Unsupported type for open %s" % datatype)

    if command is None:
        command = OPEN_CMD.get(sys.platform)

    if command is None:
        raise BadDingo("Unable to determine command for launching browser")

    weburl = goptions.weburl
    if not weburl:
        raise BadDingo("Client has no weburl configured")

    loaded = loadfn(session, element)

    weburl = weburl.rstrip("/")
    typeurl = OPEN_URL.get(datatype).format(**loaded)

    cmd = "".join((command, ' "', weburl, "/", typeurl, '"'))
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


    def handle(self, options):
        return cli_open(self.session, self.goptions,
                        datatype=options.datatype,
                        element=options.element,
                        command=options.command)


#
# The end.
