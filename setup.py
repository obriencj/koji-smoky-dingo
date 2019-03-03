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
Koji Smoky Dingo - a collection of koji command-line features for
advanced users.

:author: Christopher O'Brien  <obriencj@gmail.com>
:license: GPL version 3
"""


from setuptools import setup


setup(
    name = 'kojismokydingo',
    version = '0.9.0',

    packages = [
        # everything else
        'kojismokydingo',
    ],

    requires = [
        "koji",
        "six",
    ],

    # these are used by the koji meta-plugin to provide additional
    # commands, one per entry_point
    entry_points = {
        'koji_smoky_dingo': [
            'affected-targets = kojismokydingo.affected_targets:cli',
            'check-hosts = kojismokydingo.check_hosts:cli',
            'list-imported = kojismokydingo.identify_imported:cli',
            'bulk-tag-builds = kojismokydingo.mass_tag:cli',
            'renum-tag-inheritance = kojismokydingo.renum_tag:cli',
            'swap-tag-inheritance = kojismokydingo.swap_inheritance:cli',
            'userinfo = kojismokydingo.userinfo:cli',
        ],
    },

    zip_safe = True,

    # PyPI metadata
    description = "A collection of koji command-line plugins",

    author = "Christopher O'Brien",
    author_email = "obriencj@gmail.com",
    url = "https://github.com/obriencj/koji-smoky-dingo",
    license = "GNU General Public License",

    classifiers = [
        "Intended Audience :: Developers",
    ],
)


#
# The end.
