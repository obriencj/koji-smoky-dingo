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
Koji Smoky Dingo - DNF ease-of-use wrapper

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


try:
    from hawkey import Sack
    from libdnf.conf import ConfigMain
    from libdnf.repo import Repo

except ImportError:
    ENABLED = False

else:
    ENABLED = True


def config():
    conf = ConfigMain()

    # todo: rip out all system-level configuration features by force
    cm.reposdir().clear

    return conf


def dnfuq(path, label="koji"):

    conf = config()

    repo = Repo(label, conf)
    repo.baseurl.append(tagurl)
    repo.load()

    sack = Sack()
    sack.load_repo(repo, build_cache=False)

    return sack.query()


# The end.
