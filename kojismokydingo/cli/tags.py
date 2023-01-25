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
Koji Smoky Dingo - CLI Tag and Target Commands

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


import sys

from json import dumps
from koji import ClientSession
from koji_cli.lib import arg_filter
from operator import itemgetter
from typing import Any, Dict, List, Optional, Tuple, Union

from . import (
    AnonSmokyDingo, TagSmokyDingo,
    convert_history, int_or_str, printerr, pretty_json, print_history,
    read_clean_lines, tabulate, )
from .sift import TagSifting, output_sifted
from .. import (
    BadDingo, FeatureUnavailable, NoSuchTag,
    as_taginfo, bulk_load_tags, iter_bulk_load, version_require, )
from ..common import unique
from ..tags import (
    collect_tag_extras, find_inheritance_parent, gather_affected_targets,
    renum_inheritance, resolve_tag, tag_dedup, )
from ..sift import Sifter
from ..types import (
    HistoryEntry, TagInheritance, TagInheritanceEntry, TagSpec, )


SORT_BY_ID = "sort-by-id"
SORT_BY_NAME = "sort-by-name"


class BadSwap(BadDingo):
    complaint = "Wonky inheritance swap requested"


class NoSuchInheritance(BadDingo):
    complaint = "No such inheritance link"


class NoSuchTagExtra(BadDingo):
    complaint = "Extra setting is not defined at this tag"


class NoSuchMacro(NoSuchTagExtra):
    complaint = "Macro is not defined at this tag"


class NoSuchEnvVar(NoSuchTagExtra):
    complaint = "Environment variable is not defined at this tag"


def cli_affected_targets(
        session: ClientSession,
        tag_list: List[Union[int, str]],
        build_tags: bool = False,
        info: bool = False,
        quiet: bool = None):

    if quiet is None:
        quiet = not sys.stdout.isatty()

    targets = gather_affected_targets(session, tag_list)

    debug = printerr if not quiet else lambda *m: None

    if info:
        # convert the targets into info tuples
        infos = sorted((t['name'], t['build_tag_name'], t['dest_tag_name'])
                       for t in targets)
        output = [" ".join(t) for t in infos]

    else:
        # get a unique sorted list of either the target names or the
        # build tag names for the targets
        attr = 'build_tag_name' if build_tags else 'name'
        output = sorted(set(targ[attr] for targ in targets))  # type: ignore

    if build_tags:
        debug(f"Found {len(output)} affected build tags inheriting:")
    else:
        debug(f"Found {len(output)} affected targets inheriting:")

    # for debugging we re-print the tags we operated on
    for tag in sorted(set(tag_list)):
        debug(" ", tag)

    if output:
        debug('-' * 40)
        for o in output:
            print(o)


class AffectedTargets(AnonSmokyDingo):

    description = "Show targets impacted by changes to the given tag(s)"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tags", nargs="+", metavar="TAGNAME",
               help="Tag to check")

        addarg("-q", "--quiet", action="store_true", default=None,
               help="Don't print summary information")

        group = parser.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("-i", "--info", action="store_true", default=False,
               help="Print target name, build tag name, dest tag name")

        addarg("-b", "--build-tags", action="store_true", default=False,
               help="Print build tag names rather than target names")

        return parser


    def handle(self, options):
        return cli_affected_targets(self.session, options.tags,
                                    options.build_tags, options.info,
                                    options.quiet)


def cli_renum_tag(
        session: ClientSession,
        tagname: Union[int, str],
        begin: int = 10,
        step: int = 10,
        verbose: bool = False,
        test: bool = False):

    as_taginfo(session, tagname)

    original = session.getInheritanceData(tagname)
    renumbered = renum_inheritance(original, begin, step)

    if test or verbose:
        print("Renumbering inheritance priorities for", tagname)
        for left, right in zip(original, renumbered):
            name = left['name']
            lp = left['priority']
            rp = right['priority']
            print(f" {lp:>3} -> {rp:>3}  {name}")

    if test:
        print("Changes not committed in test mode.")

    else:
        session.setInheritanceData(tagname, renumbered)


class RenumTagInheritance(TagSmokyDingo):

    description = "Renumbers inheritance priorities of a tag," \
                  " preserving order"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Tag to renumber")

        addarg("--verbose", "-v", action="store_true", default=False,
               help="Print information about what's changing")

        addarg("--test", "-t", action="store_true", default=False,
               help="Calculate the new priorities, but don't commit"
               " the changes")

        addarg("--begin", "-b", action="store", type=int, default=10,
               help="New priority for first inheritance link"
               " (default: 10)")

        addarg("--step", "-s", action="store", type=int, default=10,
               help="Priority increment for each subsequent"
               " inheritance link after the first (default: 10)")

        return parser


    def validate(self, parser, options):
        begin = options.begin
        if begin < 0:
            parser.error("begin value must not be negative")

        elif begin >= 1000:
            parser.error("don't be ridiculous")

        step = options.step
        if step < 1:
            parser.error("priority increment must be positive"
                         " (no reversing)")

        elif step > 100:
            parser.error("don't be ridiculous")


    def handle(self, options):
        return cli_renum_tag(self.session, options.tag,
                             options.begin, options.step,
                             options.verbose, options.test)


def cli_swap_inheritance(
        session: ClientSession,
        tagname: Union[int, str],
        old_parent: TagSpec,
        new_parent: TagSpec,
        verbose: bool = False,
        test: bool = False):

    if tagname in (old_parent, new_parent) or old_parent == new_parent:
        raise BadSwap(tagname, old_parent, new_parent)

    original = session.getInheritanceData(tagname)
    if original is None:
        raise NoSuchTag(tagname)

    old_p = as_taginfo(session, old_parent)
    new_p = as_taginfo(session, new_parent)

    # deep copy of original inheritance
    swapped: TagInheritance = [TagInheritanceEntry.copy(i) for i in original]

    found_old = find_inheritance_parent(swapped, old_p["id"])
    found_new = find_inheritance_parent(swapped, new_p["id"])

    if found_old is None:
        raise NoSuchInheritance(tagname, old_parent)

    # this looks convoluted, because we're doing two things at
    # once. First, we're duplicating the whole inheritance structure
    # so we can show what's changed. Second, we're collecting the
    # changes as either two edits, or a delete and an addition.

    changes: TagInheritance

    if found_new is None:
        # the new inheritance isn't in the current inheritance
        # structure, therefore duplicate the old inheritance link and
        # mark it as a deletion, and then modify the old inheritance
        # link later.
        changed_old = TagInheritanceEntry.copy(found_old)
        changed_old['delete link'] = True  # type: ignore
        changes = [changed_old, found_old]

    else:
        # the new inheritance link is also within the current
        # inheritance structure, therefore this is an action to make
        # two edits. Mix in the updated new inheritance data now, and
        # the old inheritance link will be updated at the end.
        changes = [found_old, found_new]
        found_new["name"] = old_p["name"]
        found_new["parent_id"] = old_p["id"]

    # we do this last so that we'll have a chance to duplicate the
    # original if needed
    found_old["name"] = new_p["name"]
    found_old["parent_id"] = new_p["id"]

    # at this point the swapped list represents the fully modified
    # inheritance structure we'd like to see, and changes represents
    # just the two edits we're making.

    if test or verbose:
        print("Swapping inheritance data for", tagname)
        for left, right in zip(original, swapped):
            priority = left['priority']
            lp = left['name']
            rp = right['name']
            if lp != rp:
                print(f" {priority:>3}: {lp} -> {rp}")
            else:
                print(f" {priority:>3}: {lp}")

    if test:
        print("Changes not committed in test mode.")
    else:
        session.setInheritanceData(tagname, changes)


class SwapTagInheritance(TagSmokyDingo):

    description = "Swap a tag's inheritance"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Name of tag to modify")

        addarg("old_parent", action="store", metavar="OLD_PARENT_TAG",
               help="Old parent tag's name")

        addarg("new_parent", action="store", metavar="NEW_PARENT_TAG",
               help="New parent tag's name")

        addarg("--verbose", "-v", action="store_true", default=False,
               help="Print information about what's changing")

        addarg("--test", "-t", action="store_true", default=False,
               help="Calculate the new inheritance, but don't commit"
               " the changes.")

        return parser


    def handle(self, options):
        return cli_swap_inheritance(self.session, options.tag,
                                    options.old_parent, options.new_parent,
                                    options.verbose, options.test)


def cli_list_rpm_macros(
        session: ClientSession,
        tagname: Union[int, str],
        target: bool = False,
        quiet: Optional[bool] = None,
        defn: bool = False,
        json: bool = False):

    taginfo = resolve_tag(session, tagname, target)

    extras = collect_tag_extras(session, taginfo, prefix="rpm.macro.")
    for name, extra in extras.items():
        extra["macro"] = name[10:]  # type: ignore

    if json:
        pretty_json(extras)
        return

    if defn:
        # macro definition mode
        fmt = "%{macro} {value}"

        for extra in extras.values():
            print(fmt.format(**extra))

    else:
        tabulate(("Macro", "Value", "Tag"),
                 extras.values(),
                 key=itemgetter("macro", "value", "tag_name"),
                 sorting=1,
                 quiet=quiet)


class ListRPMMacros(AnonSmokyDingo):

    description = "Show RPM Macros for a tag"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Name of tag")

        addarg("--target", action="store_true", default=False,
               help="Specify by target rather than a tag")

        group = parser.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--quiet", "-q", action="store_true", default=None,
               help="Omit headings")

        addarg("--macro-definition", "-d", action="store_true",
               dest="defn", default=False,
               help="Output as RPM macro definitions")

        addarg("--json", action="store_true", default=False,
               help="Output as JSON")

        return parser


    def handle(self, options):
        return cli_list_rpm_macros(self.session, options.tag,
                                   target=options.target,
                                   quiet=options.quiet,
                                   defn=options.defn,
                                   json=options.json)


def cli_set_rpm_macro(
        session: ClientSession,
        tagname: Union[int, str],
        macro: str,
        value: Optional[str] = None,
        remove: bool = False,
        block: bool = False,
        target: bool = False):

    """
    If remove is True, value and block are ignored. The setting will
    be removed from the tag's extra settings.

    If block is True, value is ignored. A block entry will be added to
    the tag's extra settings.

    If remove and block are both False, then the value will be
    assigned to the tag's extra settings.

    If target is True, then tagname is actually the name of a target.
    That target's build tag will be the tag that is therefore
    modified.
    """

    taginfo = resolve_tag(session, tagname, target)

    if macro.startswith("rpm.macro."):
        key = macro
        macro = macro[10:]
    elif macro.startswith("%"):
        macro = macro.lstrip("%")
        key = "rpm.macro." + macro
    else:
        key = "rpm.macro." + macro

    if remove:
        if key not in taginfo["extra"]:
            raise NoSuchMacro(macro)

        session.editTag2(taginfo["id"], remove_extra=[key])

    elif block:
        version_require(session, (1, 23), "block tag extra values")
        session.editTag2(taginfo["id"], block_extra=[key])

    else:
        # converts to numbers, True, False, and None as applicable
        value = arg_filter(value)

        # an empty string breaks mock and RPM, make it %nil instead.  RPM
        # macros are not allowed to have an empty body. None is treated as
        # the string "None" so we leave that alone.
        if value == '':
            value = "%nil"

        session.editTag2(taginfo["id"], extra={key: value})


class SetRPMMacro(TagSmokyDingo):

    description = "Set an RPM Macro on a tag"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Name of tag")

        addarg("macro", action="store",
               help="Name of the macro")

        grp = parser.add_mutually_exclusive_group()
        addarg = grp.add_argument

        addarg("value", action="store", nargs="?", default="%nil",
               help="Value of the macro. Default: %%nil")

        addarg("--remove", action="store_true", default=False,
               help="Remove the macro definition from the tag")

        addarg("--block", action="store_true", default=False,
               help="Block the macro definition from the tag")

        addarg = parser.add_argument

        addarg("--target", action="store_true", default=False,
               help="Specify by target rather than a tag")

        return parser


    def handle(self, options):
        return cli_set_rpm_macro(self.session, options.tag,
                                 options.macro,
                                 value=options.value,
                                 remove=options.remove,
                                 block=options.block,
                                 target=options.target)


class RemoveRPMMacro(TagSmokyDingo):

    description = "Remove an RPM Macro from a tag"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Name of tag")

        addarg("macro", action="store",
               help="Name of the macro to remove")

        addarg("--target", action="store_true", default=False,
               help="Specify by target rather than a tag")

        return parser


    def handle(self, options):
        return cli_set_rpm_macro(self.session, options.tag,
                                 options.macro,
                                 value=None,
                                 remove=True,
                                 block=False,
                                 target=options.target)


class BlockRPMMacro(TagSmokyDingo):

    description = "Block an RPM Macro from a tag"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Name of tag")

        addarg("macro", action="store",
               help="Name of the macro to block")

        addarg("--target", action="store_true", default=False,
               help="Specify by target rather than a tag")

        return parser


    def handle(self, options):
        return cli_set_rpm_macro(self.session, options.tag,
                                 options.macro,
                                 value=None,
                                 remove=False,
                                 block=True,
                                 target=options.target)


def cli_set_env_var(
        session: ClientSession,
        tagname: Union[int, str],
        var: str,
        value: Optional[str] = None,
        remove: bool = False,
        block: bool = False,
        target: bool = False):
    """
    If remove is True, value and block are ignored. The setting will
    be removed from the tag's extra settings.

    If block is True, value is ignored. A block entry will be added to
    the tag's extra settings.

    If remove and block are both False, then the value will be
    assigned to the tag's extra settings.

    If target is True, then tagname is actually the name of a target.
    That target's build tag will be the tag that is therefore
    modified.
    """

    taginfo = resolve_tag(session, tagname, target)

    if var.startswith("rpm.env."):
        key = var
        var = var[8:]
    else:
        key = "rpm.env." + var

    if remove:
        if key not in taginfo["extra"]:
            raise NoSuchEnvVar(var)

        session.editTag2(taginfo["id"], remove_extra=[key])

    elif block:
        version_require(session, (1, 23), "block tag extra values")
        session.editTag2(taginfo["id"], block_extra=[key])

    else:
        session.editTag2(taginfo["id"], extra={key: value})


class SetEnvVar(TagSmokyDingo):

    description = "Set a mock environment variable on a tag"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Name of tag")

        addarg("var", action="store",
               help="Name of the environment variable")

        grp = parser.add_mutually_exclusive_group()
        addarg = grp.add_argument

        addarg("value", action="store", nargs="?", default="",
               help="Value of the environment var. Default: ''")

        addarg("--remove", action="store_true", default=False,
               help="Remove the environment var from the tag")

        addarg("--block", action="store_true", default=False,
               help="Block the environment var from the tag")

        addarg = parser.add_argument

        addarg("--target", action="store_true", default=False,
               help="Specify by target rather than a tag")

        return parser


    def validate(self, parser, options):
        val = options.value

        if val and val.startswith(r"\-"):
            # fight against option parsing
            options.value = val[1:]

        elif not (val or options.remove or options.block):
            # support KEY=VAL definitions
            if "=" in options.var:
                var, val = options.var.split("=", 1)
                options.var = var
                options.value = val


    def handle(self, options):
        return cli_set_env_var(self.session, options.tag,
                               options.var,
                               value=options.value,
                               remove=options.remove,
                               block=options.block,
                               target=options.target)


class RemoveEnvVar(TagSmokyDingo):

    description = "Remove a mock environment variable from a tag"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Name of tag")

        addarg("var", action="store",
               help="Name of the environment variable")

        addarg("--target", action="store_true", default=False,
               help="Specify by target rather than a tag")

        return parser


    def handle(self, options):
        return cli_set_env_var(self.session, options.tag,
                               options.var,
                               value=None,
                               remove=True,
                               block=False,
                               target=options.target)


class BlockEnvVar(TagSmokyDingo):

    description = "Block a mock environment variable from a tag"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Name of tag")

        addarg("var", action="store",
               help="Name of the environment variable")

        addarg("--target", action="store_true", default=False,
               help="Specify by target rather than a tag")

        return parser


    def handle(self, options):
        return cli_set_env_var(self.session, options.tag,
                               options.var,
                               value=None,
                               remove=False,
                               block=True,
                               target=options.target)


def cli_list_env_vars(
        session: ClientSession,
        tagname: Union[int, str],
        target: bool = False,
        quiet: bool = None,
        defn: bool = False,
        json: bool = False):

    taginfo = resolve_tag(session, tagname, target)

    extras = collect_tag_extras(session, taginfo, prefix="rpm.env.")
    for name, extra in extras.items():
        extra["var"] = name[8:]  # type: ignore

    if json:
        pretty_json(extras)
        return

    else:
        # we're going to want to add some escaping safety nets. Let's
        # have json.dumps do that work for us.
        for extra in extras.values():
            extra["value"] = dumps(extra["value"])

    if defn:
        # macro definition mode
        fmt = "{var!s}={value!s}"

        for extra in extras.values():
            print(fmt.format(**extra))

    else:
        tabulate(("Variable", "Value", "Tag"),
                 extras.values(),
                 key=itemgetter("var", "value", "tag_name"),
                 sorting=1,
                 quiet=quiet)


class ListEnvVars(AnonSmokyDingo):

    description = "Show mock environment variables for a tag"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Name of tag")

        addarg("--target", action="store_true", default=False,
               help="Specify by target rather than a tag")

        group = parser.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--quiet", "-q", action="store_true", default=None,
               help="Omit headings")

        addarg("--sh-declaration", "-d", action="store_true",
               dest="defn", default=False,
               help="Output as sh variable declarations")

        addarg("--json", action="store_true", default=False,
               help="Output as JSON")

        return parser


    def handle(self, options):
        return cli_list_env_vars(self.session, options.tag,
                                 target=options.target,
                                 quiet=options.quiet,
                                 defn=options.defn,
                                 json=options.json)


def cli_list_tag_extras(
        session: ClientSession,
        tagname: Union[int, str],
        target: bool = False,
        blocked: bool = False,
        quiet: Optional[bool] = None,
        json: bool = False):

    taginfo = resolve_tag(session, tagname, target)
    extras = collect_tag_extras(session, taginfo)

    if json:
        pretty_json(extras)
        return

    headings: Tuple[str, ...]

    if blocked:
        headings = ("Setting", "Value", "Tag", "Block")
        _fields = itemgetter("name", "value", "tag_name", "blocked")

        def fields(v):
            vals = list(_fields(v))
            vals[3] = "[BLOCK]" if vals[3] else ""
            return vals

    else:
        headings = ("Setting", "Value", "Tag")
        fields = itemgetter("name", "value", "tag_name")

    tabulate(headings,
             extras.values(),
             key=fields,
             sorting=1,
             quiet=quiet)


class ListTagExtras(AnonSmokyDingo):

    description = "Show extra settings for a tag"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Name of tag")

        addarg("--target", action="store_true", default=False,
               help="Specify by target rather than a tag")

        addarg("--blocked", action="store_true", default=False,
               help="Show blocked extras")

        group = parser.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--quiet", "-q", action="store_true", default=None,
               help="Omit headings")

        addarg("--json", action="store_true", default=False,
               help="Output as JSON")

        return parser


    def handle(self, options):
        return cli_list_tag_extras(self.session, options.tag,
                                   target=options.target,
                                   blocked=options.blocked,
                                   quiet=options.quiet,
                                   json=options.json)


def cli_filter_tags(
        session: ClientSession,
        tag_list: List[Union[int, str]],
        search: Optional[str] = None,
        regex: Optional[str] = None,
        tag_sifter: Optional[Sifter] = None,
        sorting: Optional[str] = None,
        outputs: Optional[dict] = None,
        strict: bool = False):

    if search:
        tag_list.extend(t["id"] for t in
                        session.search(search, "tag", "glob") if t)

    if regex:
        tag_list.extend(t["id"] for t in
                        session.search(regex, "tag", "regex") if t)

    tag_list = unique(map(int_or_str, tag_list))
    loaded = bulk_load_tags(session, tag_list, err=strict)
    tags = tag_dedup(loaded.values())

    if tag_sifter:
        results = tag_sifter(session, tags)
    else:
        results = {"default": list(tags)}

    if sorting == SORT_BY_NAME:
        sortkey = "name"
    elif sorting == SORT_BY_ID:
        sortkey = "id"
    else:
        sortkey = None

    # unsure why
    output_sifted(results, "name", outputs, sort=sortkey)  # type: ignore


class FilterTags(AnonSmokyDingo, TagSifting):

    description = "Filter a list of tags"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tags", nargs="*", type=int_or_str, metavar="TAGNNAME",
               help="Tag names to filter through")

        addarg("-f", "--file", action="store", default=None,
               dest="tag_file", metavar="TAG_FILE",
               help="Read list of tags from file, one name per line."
               " Specify - to read from stdin.")

        addarg("--strict", action="store_true", default=False,
               help="Erorr if any of the tag names to not resolve into a"
               " real tag. Otherwise, missing tags are ignored.")

        grp = parser.add_argument_group("Searching for tags")
        grp = grp.add_mutually_exclusive_group()
        addarg = grp.add_argument

        addarg("--search", action="store", default=None, metavar="GLOB",
               help="Filter the results of a search for tags with"
               " the given name pattern")

        addarg("--regex", action="store", default=None, metavar="REGEX",
               help="Filter the results of a search for tags with"
               " the given regex name pattern")

        grp = parser.add_argument_group("Sorting of tags")
        grp = grp.add_mutually_exclusive_group()
        addarg = grp.add_argument

        addarg("--nvr-sort", action="store_const",
               dest="sorting", const=SORT_BY_NAME, default=None,
               help="Sort output by Name in ascending order")

        addarg("--id-sort", action="store_const",
               dest="sorting", const=SORT_BY_ID, default=None,
               help="Sort output by Tag ID in ascending order")

        return self.sifter_arguments(parser)


    def handle(self, options):
        tags = list(options.tags)

        if not (tags or sys.stdin.isatty()):
            if not options.tag_file:
                options.tag_file = "-"

        if options.tag_file:
            tags.extend(read_clean_lines(options.tag_file))

        ts = self.get_sifter(options)
        outputs = self.get_outputs(options)

        return cli_filter_tags(self.session, tags,
                               search=options.search,
                               regex=options.regex,
                               tag_sifter=ts,
                               sorting=options.sorting,
                               outputs=outputs,
                               strict=options.strict)


REPO_CHECK_TABLES = [
    "build_target_config", "group_config", "group_package_listing",
    "group_req_listing", "tag_config", "tag_external_repos", "tag_extra",
    "tag_inheritance", "tag_listing", "tag_packages",
]


def cli_check_repo(
        session: ClientSession,
        tagname: Union[int, str],
        target: bool = False,
        quiet: bool = False,
        verbose: bool = False,
        show_events: bool = False,
        utc: bool = False) -> int:

    tag = resolve_tag(session, tagname, target)
    tagname = tag['name']
    tagid = tag['id']

    repo = session.getRepo(tagid)
    if not repo:
        if not quiet:
            print(f"Tag {tagname} has no repo")
        return 1

    create_event = repo['create_event']
    # print("repo: ", repo)

    # tagChangedSinceEvent doesn't follow inheritance on its own,
    # instead we must collect the relevant inheritance links and
    # check the whole set of tags
    inher = session.getFullInheritance(tagid)
    tag_ids = [tagid]
    tag_ids.extend(t['parent_id'] for t in inher)

    changed = session.tagChangedSinceEvent(create_event, tag_ids)
    if changed:
        if not quiet:
            print(f"Tag {tagname} has a stale repo")
        if not verbose:
            return 1
    else:
        if not quiet:
            print(f"Tag {tagname} has an up-to-date repo")
        return 0

    print(f"History since repo creation event {create_event}:")

    # if we got this far then there's been tag changes since the
    # repo's creation event, and we've been asked to display those
    # changes. So let's create a timeline from the history of all
    # the tags, searching for events that happened after the
    # creation event
    timeline: List[HistoryEntry] = []

    def query(tag_id):
        return session.queryHistory(tables=REPO_CHECK_TABLES,
                                    tag=tag_id,
                                    afterEvent=create_event)

    # merge and linearize the events of tag and its parents
    updates: Dict[str, List[Dict[str, Any]]]
    for _tid, updates in iter_bulk_load(session, query, tag_ids):
        timeline.extend(convert_history(updates))

    timeline.sort(key=itemgetter(0, 1, 2))

    print_history(timeline, utc=utc, show_events=show_events)

    return 1


class CheckRepo(AnonSmokyDingo):

    description = "Check the freshness of a tag's repo"


    def arguments(self, parser):
        addarg = parser.add_argument

        addarg("tag", action="store", metavar="TAGNAME",
               help="Name of tag")

        addarg("--target", action="store_true", default=False,
               help="Specify by target rather than a tag")

        group = parser.add_mutually_exclusive_group()
        addarg = group.add_argument

        addarg("--quiet", "-q", action="store_true", default=False,
               help="Suppress output")

        addarg("--verbose", "-v", action="store_true", default=False,
               help="Show history modifications since repo creation")

        group = parser.add_argument_group("verbose output settings")
        addarg = group.add_argument

        addarg("--utc", action="store_true", default=False,
               help="Display timestamps in UTC rather than local time."
               " Requires koji >= 1.27")

        addarg("--events", "-e", action="store_true", default=False,
               help="Display event IDs")

        return parser


    def handle(self, options):
        return cli_check_repo(self.session, options.tag,
                              target=options.target,
                              verbose=options.verbose,
                              quiet=options.quiet,
                              show_events=options.events,
                              utc=options.utc)


#
# The end.
