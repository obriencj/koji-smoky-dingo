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


from os.path import abspath
from tempfile import TemporaryDirectory

from . import BadDingo


try:
    from dnf.base import Base
    from dnf.conf.config import MainConf
    from dnf.sack import _build_sack

except ImportError:
    ENABLED = False

else:
    ENABLED = True


def __requirednf():
    if not ENABLED:
        raise BadDingo("requires libdnf")


def dnf_config(tmpdir):
    __requirednf()

    if not tmpdir:
        raise BadDingo("cannot execute query without cache dir")

    mc = MainConf()
    mc.cachedir = tmpdir

    return mc


def dnf_sack(config, path, label="koji"):
    __requirednf()

    if "://" not in path:
        path = "file://" + abspath(path)

    base = Base(config)
    base.repos.add_new_repo(label, config, baseurl=path)

    base._sack = _build_sack(base)
    base._add_repo_to_sack(base.repos[label])

    return base.sack


@contextmanager
def dnfuq(path, label="koji", cachedir="/tmp"):
    with TemporaryDirectory(dir=cachedir) as tmpdir:
        d = DNFuq(path, label, tmpdir)
        yield d
        d.cachedir = None
        d._sack = None


class DNFuq:

    def __init__(path, label="koji", cachedir="/tmp"):
        self.path = path
        self.label = label
        self.cachedir = cachedir
        self.sack = None


    def query(self):
        if self.sack is None:
            conf = dnf_conf(self.cachedir)
            self.sack = dnf_sack(conf, self.path, self.label)
        return self.sack.query()


    def whatprovides(self, ask):
        q = self.query().filterm(provides__glob=ask)
        return q.run()


    def whatrequires(self, ask):
        q = self.query().filterm(requires__glob=ask)
        return q.run()


# The end.
