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

from . import BadDingo


try:
    from hawkey import Query, Sack
    from libdnf.conf import ConfigMain, ConfigRepo, Option
    from libdnf.repo import Repo

    PRIO_RUNTIME = Option.Priority_RUNTIME
    PRIO_REPO = Option.Priority_REPOCONFIG

except ImportError:
    ENABLED = False

else:
    ENABLED = True


def __requirednf():
    if not ENABLED:
        raise BadDingo("requires libdnf")


def dnf_config():
    __requirednf()

    cm = ConfigMain()

    # cm.gpgcheck().set(PRIO_RUNTIME, False)
    # cm.max_parallel_downloads().set(PRIO_RUNTIME, 1)
    # cm.password().set(PRIO_RUNTIME, "")
    # cm.proxy().set(PRIO_RUNTIME, "")
    # cm.proxy_username().set(PRIO_RUNTIME, "")
    # cm.proxy_password().set(PRIO_RUNTIME, "")
    # cm.proxy_sslcacert().set(PRIO_RUNTIME, "")
    # cm.proxy_sslclientcert().set(PRIO_RUNTIME, "")
    # cm.proxy_sslclientkey().set(PRIO_RUNTIME, "")
    # cm.proxy_sslverify().set(PRIO_RUNTIME, False)
    # cm.reposdir().set(PRIO_RUNTIME, "")
    # cm.sslcacert().set(PRIO_RUNTIME, "")
    # cm.sslclientcert().set(PRIO_RUNTIME, "")
    # cm.sslclientkey().set(PRIO_RUNTIME, "")
    # cm.sslverify().set(PRIO_RUNTIME, False)
    # cm.username().set(PRIO_RUNTIME, "")
    # cm.user_agent().set(PRIO_RUNTIME, "koji-smoky-dingo")

    # TODO: where should the cache actually live?
    cm.cachedir().set(PRIO_REPO, "/tmp")

    return cm


def dnf_repo(path, label="koji"):
    __requirednf()

    if "://" not in path:
        path = "file://" + abspath(path)

    repoconf = ConfigRepo(dnf_config())

    repoconf.enabled().set(PRIO_REPO, True)
    repoconf.name().set(PRIO_REPO, label)
    repoconf.baseurl().set(PRIO_REPO, path)

    repoconf.this.disown()
    return Repo(label, repoconf)


def dnfuq(path, label="koji"):
    __requirednf()

    r = dnf_repo(path, label)
    r.load()

    sack = Sack()
    sack.load_repo(r, build_cache=True)

    q = Query(sack, 0)
    return q.available()


def whatprovides(path, ask, label="koji"):
    q = dnfuq(path, label)

    qwp = q.filter(provides__glob=ask)
    if qwp:
        q = qwp
    else:
        q = q.filterm(file__glob=ask)

    return q


# The end.
