#! /usr/bin/env python2


"""
Swaps inheritance between two parent tags in a brew tag.

If only the original tag is already present in the inheritance, it
will be switched for its replacement.

If both the original and the replacement are in the inheritance, they
will have their priorities swapped.

author: cobrien@redhat.com
"""


import sys

from itertools import izip
from koji import ClientSession, GenericError
from krbV import Krb5Error
from optparse import OptionParser


DEFAULT_BREW_HOST = "https://brewhub.engineering.redhat.com/brewhub"


class BadSwap(Exception): pass

class NoSuchTag(Exception): pass

class NoSuchInheritance(Exception): pass


class ManagedClientSession(ClientSession):

    """ A koji.ClientSession that can be used as via the 'with'
    keyword to provide a managed session that will handle login and
    logout """

    def __enter__(self):
        self.krb_login()
        return self

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        self.logout()
        return (exc_type is None)


def find_inheritance(inheritance, parent_id):
    for i in inheritance:
        if i["parent_id"] == parent_id:
            return i
    else:
        return None


def cli_swap(options, tagname, old_parent, new_parent):

    if tagname in (old_parent, new_parent) or old_parent == new_parent:
        raise BadSwap(tagname, old_parent, new_parent)

    with ManagedClientSession(options.server,
                              opts={'krbservice':'brewhub'}) as brewhub:

        original = brewhub.getInheritanceData(tagname)
        if original is None:
            raise NoSuchTag(tagname)

        old_p = brewhub.getTag(old_parent)
        if old_p is None:
            raise NoSuchTag(old_parent)

        new_p = brewhub.getTag(new_parent)
        if new_p is None:
            raise NoSuchTag(new_parent)

        # deep copy of original inheritance
        swapped = [dict(i) for i in original]

        found_old = find_inheritance(swapped, old_p["id"])
        found_new = find_inheritance(swapped, new_p["id"])

        if found_old is None:
            raise NoSuchInheritance(tagname, old_parent)
        else:
            found_old["name"] = new_p["name"]
            found_old["parent_id"] = new_p["id"]

        if found_new is not None:
            # perform the optional behavior if both new and old are
            # parents, and effectively swap their priorities.

            found_new["name"] = old_p["name"]
            found_new["parent_id"] = old_p["id"]

        #print original
        #print swapped

        if options.verbose:
            print "Swapping inheritance data for", tagname
            for left, right in izip(original, swapped):
                priority = left['priority']
                lp = left['name']
                rp = right['name']
                if lp != rp:
                    print " %3i: %s -> %s" % (priority, lp, rp)
                else:
                    print " %3i: %s" % (priority, lp)

        if options.test:
            print "Changes not committed in test mode."
        else:
            results = brewhub.setInheritanceData(tagname, swapped, clear=True)
            if options.verbose and results:
                print results


def cli_options():
    opts = OptionParser(usage="%prog [OPTIONS] TAG OLD_PARENT NEW_PARENT",
                        description="Swaps TAG's inheritance from OLD_PARENT"
                        " to NEW_PARENT, preserving priority. If NEW_PARENT"
                        " was already in the inheritance of TAG, OLD_PARENT"
                        " will be put in its place, effectively exchanging"
                        " the two parent priorities.")

    opts.add_option("--server", action="store", default=DEFAULT_BREW_HOST)

    opts.add_option("--verbose", "-v", action="store_true", default=False,
                    help="Print information about what's changing")

    opts.add_option("--test", "-t", action="store_true",  default=False,
                    help="Calculate the new inheritance, but don't commit"
                    " the changes. Use with --verbose to preview changes.")

    return opts


def main(args):
    parser = cli_options()
    options, args = parser.parse_args(args)

    if len(args) != 4:
        parser.error("You must specify a tag to modify, an existing"
                     " parent tag, and a replacement parent tag")

    try:
        cli_swap(options, *args[1:])

    except KeyboardInterrupt, ki:
        print
        return 130

    except GenericError, kge:
        print >> sys.stderr, kge.message
        return -1

    except Krb5Error, krbe:
        print >> sys.stderr, "Kerberos error:", krbe.args[1]
        return -2

    except NoSuchTag, nst:
        print >> sys.stderr, "No such tag:", nst
        return -3

    except NoSuchInheritance, nsi:
        print >> sys.stderr, "No such inheritance link:", nsi
        return -4

    except BadSwap, bs:
        print >> sys.stderr, "Insane inheritance swap suggested:", bs
        return -5

    else:
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))


# The end.
