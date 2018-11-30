#!/usr/bin/env python2


"""

Given a tag (or tags) display all of the targets that will be affected
if the tag changes.

In other words, look through the reversed inheritance of the tag, and
collect any targets on each child.

author: cobrien@redhat.com

"""


import sys

from itertools import chain
from optparse import OptionParser
from socket import gaierror
from xmlrpclib import Fault, MultiCall, ServerProxy


class NoSuchTag(Exception): pass


BREW_SERVICE="https://brewhub.engineering.redhat.com/brewhub"


def _debug_on(msg):
    print >> sys.stderr, msg


def _debug_off(msg):
    pass


def cli(options, tag_list):

    brewhub = ServerProxy(options.brewhub)

    debug = _debug_off if options.quiet else _debug_on

    tags = list()
    for tname in tag_list:
        tag = brewhub.getTag(tname)
        if not tag:
            raise NoSuchTag(tname)
        else:
            tags.append(tag)

    multicall = MultiCall(brewhub)
    for tag in tags:
        multicall.getFullInheritance(tag['id'],
                                     {"__starstar": True, "reverse": True})

    parents = multicall()

    multicall = MultiCall(brewhub)
    for ti in parents:
        for child in ti:
            multicall.getBuildTargets({"__starstar": True,
                                       "buildTagID": child['tag_id']})

    targets = chain(*multicall())

    if options.info:
        targets = ((t['name'],t['build_tag_name'],t['dest_tag_name'])
                   for t in targets)
        output = [" ".join(t) for t in sorted(targets)]

    else:
        attr = 'build_tag_name' if options.build_tags else 'name'
        output = sorted(set(targ[attr] for targ in targets))

    message = ("Found %i affected build tags inheriting:\n %s" if
               options.build_tags else
               "Found %i affected targets inheriting:\n %s")

    sources = "\n ".join(sorted(set(tag['name'] for tag in tags)))

    debug(message % (len(output), sources))

    if len(output):
        debug("--" * 20)

    for o in output:
        print o


def create_optparser():
    parse = OptionParser("%prog [OPTIONS] TAG [TAG...]",
                         description="Find targets which are inheriting"
                         " the given tags")

    parse.add_option("--brewhub", action="store", default=BREW_SERVICE,
                     help="URI for the brewhub service")

    parse.add_option("--quiet", action="store_true", default=False,
                     help="Don't print summary information")

    parse.add_option("--build-tags", action="store_true", default=False,
                     help="Print build tag names rather than target names")

    parse.add_option("--info", action="store_true", default=False,
                     help="Print target name, build tag name, dest tag name")

    return parse


def main(args):
    parser = create_optparser()
    options, args = parser.parse_args(args)

    if len(args) < 2:
        parser.error("Please specify at least one tag")

    if options.info and options.build_tags:
        parser.error("Options --build-tags and --info cannot be combined")

    try:
        cli(options, args[1:])

    except KeyboardInterrupt, ki:
        return 130

    except Fault, xmlf:
        print >> sys.stderr, xmlf.faultString
        return -1

    except gaierror, dns:
        print >> sys.stderr, dns.message
        print >> sys.stderr, "Try using --brewhub with an IP address"
        return -2

    except NoSuchTag, nst:
        print >> sys.stderr, "No such tag:", nst.message
        return -3

    else:
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))


#
# The end.
