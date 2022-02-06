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
An example project that uses Koji Smoky Dingo to add new commands
to Koji
"""


from os import system

from abc import abstractmethod
from kojismokydingo.sift import Sieve, ensure_str


class ExecSieve(Sieve):

    # we'll use the same name sieve predicate for tag and build
    # filtering
    name = "exec"


    def __init__(self, sifter, cmd, *args):
        # we use the init signiture to define how the sieve is allowed
        # to be invoked inside of a filter. By default, a Sieve will
        # allow any number of arguments. We want to ensure there is at
        # least one command str, and then any number of arguments to
        # that command.

        cmd = ensure_str(cmd)
        args = map(ensure_str, args)
        super(ExecSieve, self).__init__(sifter, cmd, *args)


    @abstractmethod
    def info_name(self, info):
        pass


    def check(self, session, info):
        # produces a cmd list from the tokens we were instantiated with,
        # and the info_name of the given info type.

        cmd = list(self.tokens)
        cmd.append(self.info_name(info))

        # a return code of 0 indicates that the command was
        # successful. For this example, we'll consider that to mean
        # that this info should be included.

        result = system(' '.join(cmd))
        return result == 0


class ExecBuildSieve(ExecSieve):

    def info_name(self, info):
        # the info name for builds will be the NVR
        return info["nvr"]


class ExecTagSieve(ExecSieve):

    def info_name(self, info):
        # the info name for tags will be the tag name
        return info["name"]


#
# The end.
