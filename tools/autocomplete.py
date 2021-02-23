#! /usr/bin/env python

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

from argparse import ArgumentParser
from os.path import dirname, join
from pkg_resources import EntryPoint
from shtab import complete

import sys


def gather_commands():

    wanted = join(dirname(__file__), "..")
    if sys.path[0] != wanted:
        sys.path.insert(0, wanted)

    from setup import COMMANDS

    for keyval in COMMANDS.items():
        ep = EntryPoint.parse("=".join(keyval))
        yield ep.name, ep.resolve()


def create_superparser():
    parser = ArgumentParser("koji")

    subparsers = parser.add_subparsers()
    subparsers.required = True
    subparsers.dest = "subcommand"

    for name, cmdclass in gather_commands():
        cmdinst = cmdclass(name)
        cmdp = subparsers.add_parser(name)
        cmdinst.arguments(cmdp)

    return parser


def completion_script(shell="bash"):
    return complete(create_superparser(), shell=shell, root_prefix="ksd")


if __name__ == '__main__':
    print(completion_script())


#
# The end.
