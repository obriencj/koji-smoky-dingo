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
Koji Smoky Dingo - info command client-config

Get information about local client configuration settings

:author: cobrien@redhat.com
:license: GPL version 3
"""


from __future__ import print_function

import sys

from configparser import ConfigParser
from koji import ParameterError
from six import iterkeys

from . import AnonSmokyDingo
from .common import pretty_json


def rebuild_client_config(goptions, session):
    opts = {
        "server": session.baseurl,
        "weburl": goptions.weburl,
        "topurl": goptions.topurl,
        "topdir": goptions.topdir,
    }
    opts.update(session.opts)

    return (goptions.profile, opts)


def cli_client_config(goptions, session,
                      only=(), quiet=False, config=False, json=False):

    profile, opts = rebuild_client_config(goptions, session)

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
        cfg = ConfigParser(defaults=opts, default_section=profile)
        cfg.write(sys.stdout)
        return

    if quiet:
        for k in only:
            print(opts[k])
    else:
        for k in only:
            print("%s: %s" % (k, opts[k]))

    print()

class cli(AnonSmokyDingo):

    group = "info"
    description = "Show client profile settings"


    def parser(self):
        parser = super(cli, self).parser()
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


    def handle(self, options):
        return cli_client_config(self.goptions, self.session,
                                 only=options.only,
                                 quiet=options.quiet,
                                 config=options.cfg,
                                 json=options.json)


#
# The end.
