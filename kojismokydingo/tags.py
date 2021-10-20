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

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from functools import partial
from itertools import chain
from koji import ClientSession, GenericError
from typing import Dict, Iterable, List, Optional, Set, Union

from . import (
    NoSuchTag,
    as_taginfo, as_targetinfo,
    bulk_load, bulk_load_tags, )
from .common import unique
from .types import (
    DecoratedTagExtras,
    TagInfo, TagInfos, TagInheritance, TagInheritanceEntry,
    TagSpec, TargetInfo, )


__all__ = (
    "collect_tag_extras",
    "convert_tag_extras",
    "ensure_tag",
    "find_inheritance_parent",
    "gather_affected_targets",
    "gather_tag_ids",
    "renum_inheritance",
    "resolve_tag",
    "tag_dedup",
)


def tag_dedup(
        tag_infos: TagInfos) -> TagInfos:
    """
    Given a sequence of tag info dictionaries, return a de-duplicated
    list of same, with order preserved.

    All None infos will be dropped.

    :param tag_infos: tag infos to be de-duplicated.

    :since: 1.0
    """

    return unique(filter(None, tag_infos), key="id")


def ensure_tag(
        session: ClientSession,
        name: str) -> TagInfo:
    """
    Given a name, resolve it to a tag info dict. If there is no such
    tag, then create it and return its newly created tag info.

    :param session: active koji session

    :param name: tag name

    :since: 1.0
    """

    try:
        session.createTag(name)
    except GenericError:
        pass

    return as_taginfo(session, name)


def resolve_tag(
        session: ClientSession,
        name: Union[int, str],
        target: bool = False) -> TagInfo:
    """
    Given a name, resolve it to a taginfo.

    If target is False, name is treated as a tag's name.

    If target is True, name is treated as a target's name, and the
    resulting taginfo will be from that target's build tag.

    :param session: active koji session

    :param name: Tag or Target name

    :param target: if True then name specifies a target rather than a
      tag, so fetch the build tag name from the target and look up
      that. Default False; name specifies a tag.

    :raises NoSuchTag: if the tag could not be resolved

    :raises NoSuchTarget: if ``target`` is True and name cannot be
      resolved as a target

    :since: 1.0
    """

    if target:
        tinfo = as_targetinfo(session, name)
        name = tinfo["build_tag_name"]

    return as_taginfo(session, name)


def gather_affected_targets(
        session: ClientSession,
        tagnames: Iterable[TagSpec]) -> List[TargetInfo]:
    """
    Returns the list of target info dicts representing the targets
    which inherit any of the given named tags. That is to say, the
    targets whose build tags are children of the named tags.

    This list allows us to gauge what build configurations would be
    impacted by changes to the given tags.

    :param tagnames: List of tag names

    :raises NoSuchTag: if any of the names do not resolve to a tag
      info

    :since: 1.0
    """

    tags = [as_taginfo(session, t) for t in set(tagnames)]

    ifn = lambda tag: session.getFullInheritance(tag['id'], reverse=True)
    loaded = bulk_load(session, ifn, tags)
    parents = filter(None, loaded.values())

    tagids = set(chain(*((ch['tag_id'] for ch in ti) for ti in parents)))
    tagids.update(tag['id'] for tag in tags)

    tfn = lambda ti: session.getBuildTargets(buildTagID=ti)
    loaded = bulk_load(session, tfn, tagids)
    targets = chain(*filter(None, loaded.values()))

    return list(targets)


def renum_inheritance(
        inheritance: TagInheritance,
        begin: int = 0,
        step: int = 10) -> TagInheritance:
    """
    Create a new copy of the tag inheritance data with the priority
    values renumbered. Ordering is preserved.

    :param inheritance: Inheritance structure data

    :param begin: Starting point for renumbering priority
      values. Default, 0

    :param step: Priority value increment for each priority after the
      first. Default, 10

    :since: 1.0
    """

    renumbered: TagInheritance = []

    for index, inher in enumerate(inheritance):
        data: TagInheritanceEntry = inher.copy()
        data['priority'] = begin + (index * step)
        renumbered.append(data)

    return renumbered


def find_inheritance_parent(
        inheritance: TagInheritance,
        parent_id: int) -> TagInheritanceEntry:
    """
    Find the parent link in the inheritance list with the given tag ID.

    :param inheritance: the output of a ``getFullInheritance`` call

    :param parent_id: the ID of a parent tag to look for in the
        inheritance data.

    :returns: matching inheritance link data, or None if none are
        found with the given parent_id

    :since: 1.0
    """

    for parent in inheritance:
        if parent["parent_id"] == parent_id:
            return parent
    else:
        return None


def convert_tag_extras(
        taginfo: TagInfo,
        into: Optional[dict] = None,
        prefix: Optional[str] = None) -> DecoratedTagExtras:
    """
    Provides a merged view of the tag extra settings for a tag. The
    extras are decorated with additional keys:

      * name - str, the name of the setting
      * blocked - bool, whether the setting is blocked
      * tag_name - str, the name of the tag that provided this setting
      * tag_id - int, the ID of the tag that provided this setting

    When into is not None, then only settings which are not already
    present in that dict will be set. This behavior is used by
    `collect_tag_extras` to merge the extra settings across a tag and
    all its parents into a single dict.

    :param taginfo: A koji tag info dict

    :param into: Existing dict to collect extras into. Default, create
        a new dict.

    :param prefix: Only gather and convert extras with keys having
        this prefix. Default, gather all keys not already found.

    :since: 1.0
    """

    found = {} if into is None else into

    extra = taginfo["extra"]
    if not extra:
        return found

    for key, val in extra.items():

        # check whether the taginfo was gathered with blocks included.
        # See https://pagure.io/koji/pull-request/2495#_4__40
        if isinstance(val, (tuple, list)):
            blocked = val[0]
            val = val[1]
        else:
            blocked = False

        if prefix and not key.startswith(prefix):
            continue

        if key not in found:
            found[key] = {
                "name": key,
                "value": val,
                "blocked": blocked,
                "tag_name": taginfo["name"],
                "tag_id": taginfo["id"],
            }

    return found


def collect_tag_extras(
        session: ClientSession,
        tag: TagSpec,
        prefix: Optional[str] = None) -> DecoratedTagExtras:
    """
    Similar to session.getBuildConfig but with additional information
    recording which tag in the inheritance supplied the setting.

    Returns an dict of tag extra settings, keyed by the name of the
    setting. Each setting is represented as its own dict composed of
    the following keys:

    * name - the extra setting key
    * value - the extra setting value
    * blocked - whether the setting represents a block
    * tag_name - the name of the tag this setting came from
    * tag_id - the ID of the tag this setting came from

    :param session: an active koji client session

    :param tag: koji tag info dict, or tag name

    :param prefix: Extra name prefix to select for. If set, only tag
      extra fields whose key starts with the prefix string will be
      collected. Default, collect all.

    :since: 1.0
    """

    # this borrows heavily from the hub implementation of
    # getBuildConfig, but gives us a chance to record what tag in the
    # inheritance that the setting is coming from

    taginfo = as_taginfo(session, tag)
    found = convert_tag_extras(taginfo, prefix=prefix)

    inher = session.getFullInheritance(taginfo["id"])
    tids = (tag["parent_id"] for tag in inher if not tag["noconfig"])
    parents = bulk_load_tags(session, tids)

    for ptag in parents.values():
        # mix the extras into existing found results. note: we're not
        # checking for faults, because we got this list of tag IDs
        # straight from koji itself, but there could be some kind of
        # race condition from this.
        convert_tag_extras(ptag, into=found, prefix=prefix)

    return found


def gather_tag_ids(
        session: ClientSession,
        shallow: Optional[Iterable[Union[int, str]]] = None,
        deep: Optional[Iterable[Union[int, str]]] = None,
        results: Optional[set] = None) -> Set[int]:
    """
    Load IDs from shallow tags, and load IDs from deep tags and all
    their parents. Returns a set of all IDs found.

    If results is specified, it must be a set instance into which the
    disovered tag IDs will be added. Otherwise a new set will be
    allocated and returned.

    :param session: an active koji client session

    :param shallow: list of tag names to resolve IDs for

    :param deep: list of tag names to resolve IDs and parent IDs for

    :param results: storage for resolved IDs. Default, create a new set

    :since: 1.0
    """

    results = set() if results is None else results

    if not (shallow or deep):
        return results

    seek = list(shallow) if shallow else []

    deep = list(deep) if deep else []
    seek.extend(deep)

    # first dig up the IDs for all the tags. If any are invalid, this will
    # raise a NoSuchTag exception
    found = bulk_load_tags(session, seek)
    results.update(t['id'] for t in found.values())

    if deep:
        inh = bulk_load(session, session.getFullInheritance, deep)
        for parents in inh.values():
            results.update(t['parent_id'] for t in parents)

    return results


#
# The end.
