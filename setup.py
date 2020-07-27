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


"""
Koji Smoky Dingo - a collection of Koji command-line features for
advanced users.

Note that this package needs the kojismokydingometa plugin to be
installed in order for the plugins to be loaded by the Koji CLI.

:author: Christopher O'Brien  <obriencj@gmail.com>
:license: GPL version 3
"""


import setuptools


def config():
    conf_dict = setuptools.read_configuration("setup.cfg")
    return conf_dict


def setup():
    return setuptools.setup()


if __name__ == "__main__":
    setup()


#
# The end.
