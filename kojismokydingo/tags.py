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
Koji Smoky Dingo - tags and targets

:author: cobrien@redhat.com
:license: GPL version 3
"""


from collections import OrderedDict
from itertools import chain
from six import iteritems, itervalues

from . import NoSuchTag


def get_affected_targets(session, tagname_list):

    tags = list()
    for tname in set(tagname_list):
        tag = session.getTag(tname)
        if not tag:
            raise NoSuchTag(tname)
        else:
            tags.append(tag)

    session.multicall = True
    for tag in tags:
        session.getFullInheritance(tag['id'], reverse=True)
    parents = [p[0] for p in session.multiCall() if p]

    tagids = set(chain(*((ch['tag_id'] for ch in ti) for ti in parents)))
    tagids.update(tag['id'] for tag in tags)

    session.multicall = True
    for ti in tagids:
        session.getBuildTargets(buildTagID=ti)

    return list(chain(*(t[0] for t in session.multiCall() if t)))


def renum_inheritance(inheritance, begin, step):
    """
    a new copy of the tag inheritance data, renumbered
    """

    renumbered = list()

    for index, inher in enumerate(inheritance):
        data = dict(inher)
        data['priority'] = begin + (index * step)
        renumbered.append(data)

    return renumbered


def find_inheritance(inheritance, parent_id):
    for i in inheritance:
        if i["parent_id"] == parent_id:
            return i
    else:
        return None


def get_tag_extras(taginfo, into=None):

    found = OrderedDict() if into is None else into

    for key, val in iteritems(taginfo["extra"]):
        if key not in found:
            found[key] = {
                "name": key,
                "value": val,
                "tag_name": taginfo["name"],
                "tag_id": taginfo["id"],
            }

    return found


def collect_tag_extras(session, tagname):
    """
    Similar to session.getBuildConfig but with additional information
    recording which tag in the inheritance supplied the setting.

    Returns an OrderedDict of tag extra settings, keyed by the name of
    the setting. Each setting is represented as its own dict composed
    of the following keys:
      * name - the extra setting key
      * value - the extra setting value
      * tag_name - the name of the tag this setting came from
      * tag_id - the ID of the tag this setting came from
    """

    taginfo = session.getTag(tagname)
    if not taginfo:
        raise NoSuchTag(tagname)

    # this borrows heavily from the hub implementation of
    # getBuildConfig, but gives us a chance to record what tag in the
    # inheritance that the setting is coming from

    found = get_tag_extras(taginfo)

    inher = session.getFullInheritance(taginfo["id"])

    session.multicall = True
    for link in inher:
        if not link["noconfig"]:
            session.getTag(link["parent_id"])
    tags = (t[0] for t in session.multiCall())

    for tag in tags:
        get_tag_extras(tag, into=found)

    return found


#
# The end.
