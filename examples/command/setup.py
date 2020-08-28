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


from setuptools import setup


setup(
    name = "ksd-command",
    version = "1.0.0",

    description = "Example Koji client commands using kojismokydingo",
    license = "GNU General Public License v3 (GPLv3)",

    packages = [
        "ksd_command",
    ],

    install_requires = [
        "kojismokydingo",
    ],

    entry_points = {
        "koji_smoky_dingo": [
            "boop = ksd_command:BeepBoop",
            "beep = ksd_command:BeepBoop",
            "whoami = ksd_command:WhoAmI",
        ],
    })


# The end.
