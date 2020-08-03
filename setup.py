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


def config():
    return dict(
        name = "kojismokydingo",
        version = "0.9.0",
        description = "A collection of Koji command-line plugins",
        author = "Christopher O'Brien",
        author_email = "obriencj@gmail.com",
        url = "https://github.com/obriencj/koji-smoky-dingo",

        license = "GNU General Public License v3 (GPLv3)",

        classifiers = [
            "Environment :: Console",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Topic :: Software Development :: Build Tools",
            ],


        packages = [
            "kojismokydingo",
            "kojismokydingo.cli",
            ],

        install_requires = [
            "koji",
            "six",
            ],

        zip_safe = True,

        entry_points = {
            "koji_smoky_dingo": [
                "affected-targets = kojismokydingo.cli.tags:AffectedTargets",
                "bulk-tag-builds = kojismokydingo.cli.builds:BulkTagBuilds",
                "check-hosts = kojismokydingo.cli.hosts:CheckHosts",
                "client-config = kojismokydingo.cli.clients:ClientConfig",
                "list-cgs = kojismokydingo.cli.users:ListCGs",
                "list-imported = kojismokydingo.cli.builds:ListImported",
                "list-tag-rpm-macros = kojismokydingo.cli.tags:ListTagRPMMacros",
                "latest-archives = kojismokydingo.cli.archives:LatestArchives",
                "list-build-archives = kojismokydingo.cli.archives:ListBuildArchives",
                "perminfo = kojismokydingo.cli.users:PermissionInfo",
                "renum-tag-inheritance = kojismokydingo.cli.tags:RenumTagInheritance",
                "swap-tag-inheritance = kojismokydingo.cli.tags:SwapTagInheritance",
                "userinfo = kojismokydingo.cli.users:UserInfo",
                ],
            })


def setup():
    import setuptools
    return setuptools.setup(**config())


if __name__ == "__main__":
    setup()


#
# The end.
