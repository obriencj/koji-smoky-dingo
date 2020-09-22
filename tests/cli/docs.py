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


from docutils.frontend import OptionParser
from docutils.nodes import GenericNodeVisitor
from docutils.parsers.rst import Parser
from docutils.utils import new_document
from mock import patch
from nose.tools import assert_equal, assert_raises
from pkg_resources import EntryPoint
from six import iteritems
from six.moves import StringIO

from . import ENTRY_POINTS, default_koji_goptions


def default_document(name):
    opts = OptionParser(components=(Parser,))
    defaults = opts.get_default_values()

    # shut up the warnings
    defaults.warning_stream = StringIO()

    return new_document(name, defaults)


def load_rst(filename):
    with open(filename) as f:
        doc = default_document(filename)
        Parser().parse(f.read(), doc)
    return doc


class UsageFinder(GenericNodeVisitor):
    def __init__(self, doc):
        GenericNodeVisitor.__init__(self, doc)
        self.found_usage = []

    def visit_literal_block(self, node):
        txt = node.astext()
        if txt.startswith("usage: koji "):
            self.found_usage.append(txt)

    def default_visit(self, node):
        pass


def find_usage(filename):
    doc = load_rst(filename)
    finder = UsageFinder(doc)
    doc.walk(finder)
    return finder.found_usage


def check_command_help(cmdname):
    ref = ENTRY_POINTS[cmdname]

    ep = EntryPoint.parse("=".join([cmdname, ref]))
    name = ep.name

    if hasattr(ep, "resolve"):
        #new environments
        cmd_cls = ep.resolve()
    else:
        # old environments
        cmd_cls = ep.load(require=False)

    command = cmd_cls(name)

    goptions = default_koji_goptions()

    with patch('sys.stdout', new=StringIO()) as out:
        with patch('sys.argv', new=["koji", name, "--help"]):
            assert_raises(SystemExit,
                          command, goptions, None, ("--help",))
        outhelp = out.getvalue()

    usage = find_usage("docs/commands/%s.rst" % name)
    assert_equal(len(usage), 1)

    expected = usage[0].strip()
    found = outhelp.strip()
    assert_equal(expected, found)


def test_command_help():
    # verify the expected entry points resolve and can be
    # initialized
    for name in ENTRY_POINTS:
        yield check_command_help, name


# The end.
