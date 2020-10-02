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


from __future__ import print_function

import sys

from json import dumps
from koji_cli.lib import arg_filter
from operator import itemgetter
from six import iteritems, itervalues
from six.moves import zip

from . import (
    AnonSmokyDingo, TagSmokyDingo,
    printerr, pretty_json, tabulate)
from .. import BadDingo, FeatureUnavailable, NoSuchTag, version_require
from ..tags import (
    collect_tag_extras, find_inheritance_parent, get_affected_targets,
    renum_inheritance, resolve_tag)


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


def cli_affected_targets(session, tag_list,
                         build_tags=False, info=False,
                         quiet=None):

    if quiet is None:
        quiet = not sys.stdout.isatty()

    targets = get_affected_targets(session, tag_list)

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
        output = sorted(set(targ[attr] for targ in targets))

    if build_tags:
        debug("Found %i affected build tags inheriting:" % len(output))
    else:
        debug("Found %i affected targets inheriting:" % len(output))

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


def cli_renum_tag(session, tagname, begin=10, step=10,
                  verbose=False, test=False):

    if not session.getTag(tagname):
        raise NoSuchTag(tagname)

    original = session.getInheritanceData(tagname)
    renumbered = renum_inheritance(original, begin, step)

    if test or verbose:
        print("Renumbering inheritance priorities for", tagname)
        for left, right in zip(original, renumbered):
            name = left['name']
            lp = left['priority']
            rp = right['priority']
            print(" %3i -> %3i  %s" % (lp, rp, name))

    if test:
        print("Changes not committed in test mode.")

    else:
        results = session.setInheritanceData(tagname, renumbered)
        if verbose and results:
            print(results)


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


def cli_swap_inheritance(session, tagname, old_parent, new_parent,
                         verbose=False, test=False):

    if tagname in (old_parent, new_parent) or old_parent == new_parent:
        raise BadSwap(tagname, old_parent, new_parent)

    original = session.getInheritanceData(tagname)
    if original is None:
        raise NoSuchTag(tagname)

    old_p = session.getTag(old_parent)
    if old_p is None:
        raise NoSuchTag(old_parent)

    new_p = session.getTag(new_parent)
    if new_p is None:
        raise NoSuchTag(new_parent)

    # deep copy of original inheritance
    swapped = [dict(i) for i in original]

    found_old = find_inheritance_parent(swapped, old_p["id"])
    found_new = find_inheritance_parent(swapped, new_p["id"])

    if found_old is None:
        raise NoSuchInheritance(tagname, old_parent)

    # this looks convoluted, because we're doing two things at
    # once. First, we're duplicating the whole inheritance structure
    # so we can show what's changed. Second, we're collecting the
    # changes as either two edits, or a delete and an addition.

    if found_new is None:
        # the new inheritance isn't in the current inheritance
        # structure, therefore duplicate the old inheritance link and
        # mark it as a deletion, and then modify the old inheritance
        # link later.
        changed_old = dict(found_old)
        changed_old['delete link'] = True
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
                print(" %3i: %s -> %s" % (priority, lp, rp))
            else:
                print(" %3i: %s" % (priority, lp))

    if test:
        print("Changes not committed in test mode.")
    else:
        results = session.setInheritanceData(tagname, changes)
        if verbose and results:
            print(results)


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


def cli_list_rpm_macros(session, tagname, target=False,
                        quiet=None, defn=False, json=False):

    taginfo = resolve_tag(session, tagname, target)

    extras = collect_tag_extras(session, taginfo, prefix="rpm.macro.")
    for name, extra in iteritems(extras):
        extra["macro"] = name[10:]

    if json:
        pretty_json(extras)
        return

    if defn:
        # macro definition mode
        fmt = "%{macro} {value}"

        for extra in itervalues(extras):
            print(fmt.format(**extra))

    else:
        tabulate(("Macro", "Value", "Tag"),
                 itervalues(extras),
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


def cli_set_rpm_macro(session, tagname, macro,
                      value=None, remove=False, block=False,
                      target=False):

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


def cli_set_env_var(session, tagname, var,
                    value=None, remove=False, block=False,
                    target=False):
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


def cli_list_env_vars(session, tagname, target=False,
                      quiet=None, defn=False, json=False):

    taginfo = resolve_tag(session, tagname, target)

    extras = collect_tag_extras(session, taginfo, prefix="rpm.env.")
    for name, extra in iteritems(extras):
        extra["var"] = name[8:]

    if json:
        pretty_json(extras)
        return

    else:
        # we're going to want to add some escaping safety nets. Let's
        # have json.dumps do that work for us.
        for extra in itervalues(extras):
            extra["value"] = dumps(extra["value"])

    if defn:
        # macro definition mode
        fmt = "{var!s}={value!s}"

        for extra in itervalues(extras):
            print(fmt.format(**extra))

    else:
        tabulate(("Variable", "Value", "Tag"),
                 itervalues(extras),
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


def cli_list_tag_extras(session, tagname, target=False,
                        blocked=False,
                        quiet=None, json=False):

    taginfo = resolve_tag(session, tagname, target)
    extras = collect_tag_extras(session, taginfo)

    if json:
        pretty_json(extras)
        return

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
             itervalues(extras),
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


#
# The end.
