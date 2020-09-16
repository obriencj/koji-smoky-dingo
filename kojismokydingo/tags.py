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

from . import as_taginfo, as_targetinfo, bulk_load, bulk_load_tags


def resolve_tag(session, name, target=False):
    """
    Given a name, resolve it to a taginfo.

    If target is False, name is treated as a tag's name.

    If target is True, name is treated as a target's name, and the
    resulting taginfo will be from that target's build tag.

    :param name: Tag or Target name

    :type name: str

    :param target: name specified a target rather than a tag, fetch
      the build tag name from the target and look up that. Default,
      name specifies a tag.

    :type target: bool, optional

    :raises NoSuchTag:

    :raises NoSuchTarget:

    :rtype: dict
    """

    if target:
        tinfo = as_targetinfo(session, name)
        name = tinfo.get("build_tag_name", name)

    return as_taginfo(session, name)


def get_affected_targets(session, tagnames):

    tags = [as_taginfo(session, t) for t in set(tagnames)]

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


def find_inheritance_parent(inheritance, parent_id):
    """
    :param inheritance: the output of a getFullInheritance call

    :type inheritance: list(dict)

    :param parent_id: the ID of a parent tag to look for in the
        inheritance data.

    :returns: matching inheritance link data, or None if none are
        found with the given parent_id

    :rtype: dict
    """

    for i in inheritance:
        if i["parent_id"] == parent_id:
            return i
    else:
        return None


def convert_tag_extras(taginfo, into=None, prefix=None):
    """
    :param into: Existing dict to collect extras into. Default, create
        a new OrderedDict

    :type into: dict, optional

    :param prefix: Only gather and convert extras with key's having
        this prefix. Default, gather all keys not already found.

    :type prefix: str, optional

    :rtype: dict
    """

    found = OrderedDict() if into is None else into

    for key, val in iteritems(taginfo["extra"]):
        if prefix and not key.startswith(prefix):
            continue

        if key not in found:
            found[key] = {
                "name": key,
                "value": val,
                "tag_name": taginfo["name"],
                "tag_id": taginfo["id"],
            }

    return found


def collect_tag_extras(session, taginfo, prefix=None):
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

    :param taginfo: koji tag info dict, or tag name

    :type taginfo: int or str or dict

    :param prefix: Extra name prefix to select for. If set, only tag
      extra fields whose key starts with the prefix string will be
      collected. Default, collect all.

    :type prefix: str, optional

    :rtype: collections.OrderedDict[str, dict]
    """

    taginfo = as_taginfo(session, taginfo)

    # this borrows heavily from the hub implementation of
    # getBuildConfig, but gives us a chance to record what tag in the
    # inheritance that the setting is coming from

    found = convert_tag_extras(taginfo, prefix=prefix)

    inher = session.getFullInheritance(taginfo["id"])

    session.multicall = True
    for link in inher:
        if not link["noconfig"]:
            session.getTag(link["parent_id"])
    tags = (t[0] for t in session.multiCall())

    for tag in tags:
        convert_tag_extras(tag, into=found, prefix=prefix)

    return found


def gather_tag_ids(session, shallow=(), deep=(), results=None):
    """
    Load IDs from shallow tags, and load IDs from deep tags and all
    their parents. Returns a set of all IDs found.

    If results is specified, it must be a set instance into which the
    disovered tag IDs will be added. Otherwise a new set will be
    allocated and returned.

    :param shallow: list of tag names to resolve IDs for
    :type shallow: list[str], optional

    :param deep: list of tag names to resolve IDs and parent IDs for
    :type deep: list[str], optional

    :param results: storage for resolved IDs. Default, create a new set
    :type results: set[int], optional

    :rtype: set[int]
    """

    results = set() if results is None else results

    if not (shallow or deep):
        return results

    seek = list(shallow) if shallow else []

    if deep and not isinstance(deep, (list, tuple)):
        deep = list(deep)
        seek.extend(deep)

    # first dig up the IDs for all the tags. If any are invalid, this will
    # raise a NoSuchTag exception
    found = bulk_load_tags(session, seek)
    results.update(t['id'] for t in itervalues(found))

    if deep:
        inh = bulk_load(session, session.getFullInheritance, deep)
        for parents in itervalues(inh):
            results.update(t['parent_id'] for t in parents)

    return results


#
# The end.
