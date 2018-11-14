#! /usr/bin/env python

# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, see
# <http://www.gnu.org/licenses/>.


"""
A collection of koji command-line plugins I find useful

:author: Christopher O'Brien  <obriencj@gmail.com>
:license: GPL version 3
"""


from setuptools import setup


setup(
    name = "koji-smoky-dingo",
    version = "0.9.0",

    packages = [
        "koji_cli_plugins",
    ],

    # install_requires = ["koji", ],

    description = "A collection of koji command-line plugins",

    # PyPI information
    author = "Christopher O'Brien",
    author_email = "obriencj@gmail.com",
    url = "https://github.com/obriencj/koji-smoky-dingo",
    license = "GNU General Public License",

    zip_safe = False,

    classifiers = [
        "Intended Audience :: Developers",
    ],
)


#
# The end.
