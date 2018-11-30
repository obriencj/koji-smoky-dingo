#! /usr/bin/env python2


"""

Remember RENUM from BASIC? It's like that, but for brew tag
inheritance priority.

author: cobrien@redhat.com

"""


import sys

from itertools import izip
from koji import ClientSession, GenericError
from krbV import Krb5Error
from optparse import OptionParser


DEFAULT_BREW_HOST = "https://brewhub.engineering.redhat.com/brewhub"


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


def renum_inheritance(inheritance, begin, step):

    """ a new copy of the tag inheritance data, renumbered """

    renumbered = list()

    for index, inher in enumerate(inheritance):
        data = dict(inher)
        data['priority'] = begin + (index * step)
        renumbered.append(data)

    return renumbered


def cli_renum(options, tagname):

    with ManagedClientSession(options.server,
                              opts={'krbservice':'brewhub'}) as brewhub:

        original = brewhub.getInheritanceData(tagname)
        renumbered = renum_inheritance(original, options.begin, options.step)

        if options.verbose:
            print "Renumbering inheritance priorities for", tagname
            for left, right in izip(original, renumbered):
                name = left['name']
                lp = left['priority']
                rp = right['priority']
                print " %3i -> %3i  %s" % (lp, rp, name)

        if options.test:
            print "Changes not committed in test mode."
        else:
            results = brewhub.setInheritanceData(tagname, renumbered)
            if options.verbose and results:
                print results


def cli_options():
    opts = OptionParser(usage="%prog [OPTIONS] TAG",
                        description="Renumbers inheritance priorities of a"
                        " brew tag, preserving order.")

    opts.add_option("--server", action="store", default=DEFAULT_BREW_HOST)

    opts.add_option("--verbose", action="store_true", default=False,
                    help="Print information about what's changing")

    opts.add_option("--test", action="store_true",  default=False,
                    help="Calculate the new priorities, but don't commit"
                    " the changes")

    opts.add_option("--begin", action="store", type="int", default=10,
                    help="New priority for first inheritance link")

    opts.add_option("--step", action="store", type="int", default=10,
                    help="Priority increment for each subsequent"
                    " inheritance link after the first")

    return opts


def main(args):
    parser = cli_options()
    options, args = parser.parse_args(args)

    if len(args) < 2:
        parser.error("You must specify a tag to renumber")
    elif len(args) > 2:
        parser.error("You may only specify one tag at a time")
    elif options.begin < 0:
        parser.error("Inheritance priorities must be positive")
    elif options.begin > 1000:
        parser.error("Sensibilities offended. Use a lower begin priority")
    elif options.step < 1:
        parser.error("Inheritance steps must be 1 or greater (no reversing)")
    elif options.step > 100:
        parser.error("Chill out with the big numbers. Seriously. Relax.")

    try:
        cli_renum(options, args[1])

    except KeyboardInterrupt, ki:
        return 130

    except GenericError, kge:
        print >> sys.stderr, kge.message
        return -1

    except Krb5Error, krbe:
        print >> sys.stderr, "Kerberos error:", krbe.args[1]
        return -1

    else:
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))


# The end.
