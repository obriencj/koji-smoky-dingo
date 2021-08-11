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
Koji Smoky Dingo - Client Utils

Some simple functions for working with the local client configuration

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import sys


__all__ = (
    "rebuild_client_config",
)


def rebuild_client_config(session, goptions):
    """
    Reconstructs a koji client configuration based on the fields of a
    session and a session's goptions. Returns a tuple containing the
    active profile's name, and the configuration as a dict.

    :rtype: (str, dict)
    """

    opts = {
        "server": session.baseurl,
        "weburl": goptions.weburl,
        "topurl": goptions.topurl,
        "topdir": goptions.topdir,
    }
    opts.update(session.opts)

    return (goptions.profile, opts)


#
# The end.
