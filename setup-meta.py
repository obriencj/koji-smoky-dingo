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
Koji Smoky Dingo Meta - an entry_points adapter for Koji's CLI
plugin loading mechanism

Note that in order for this meta-plugin in koji_cli_plugins to be
installed in a way that the Koji CLI will be able to see, this package
needs to be installed using either:

  python setup.py install --root=/ --prefix=/usr

:author: Christopher O'Brien  <obriencj@gmail.com>
:license: GPL version 3
"""


from setuptools import setup


setup(
    name = 'kojismokydingo-meta',
    version = '0.9.0',

    packages = [
        # the koji meta-plugin
        'koji_cli_plugins',
    ],

    # the koji_cli_plugins namespace package needs to be a plain
    # directory that koji will look through
    zip_safe = False,

    # PyPI metadata
    description = "An entry_points adapter for Koji's CLI plugin system",

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
