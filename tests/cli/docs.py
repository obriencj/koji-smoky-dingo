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
from nose.tools import assert_equal, assert_raises, assert_true
from pkg_resources import EntryPoint
from six import iteritems
from six.moves import StringIO

from . import ENTRY_POINTS, GOptions


def load_rst(filename):
    # use the docutils option parser to get defaults for our efforts
    opts = OptionParser(components=(Parser,))
    defaults = opts.get_default_values()

    # shut up the warnings
    defaults.warning_stream = StringIO()

    doc = new_document(filename, defaults)
    with open(filename) as f:
        Parser().parse(f.read(), doc)

    return doc


class UsageFinder(GenericNodeVisitor):

    def __init__(self, doc):
        GenericNodeVisitor.__init__(self, doc)
        self.found_usage = []

    def visit_literal_block(self, node):
        txt = node.astext()
        if txt.startswith("usage: "):
            self.found_usage.append(txt)

    def default_visit(self, node):
        pass


def find_usage(filename):
    """
    Loads a reST doc from filename and finds literal blocks that start
    with the words "usage: koji"

    :rtype: str or None
    """

    doc = load_rst(filename)
    finder = UsageFinder(doc)
    doc.walk(finder)
    found = finder.found_usage

    return found[0] if found else None


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

    # a fake goptions based on a copy of the koji defaults
    goptions = GOptions()

    # launch the loaded command with the --help option, and collect
    # its output. Also ensures that it causes the expected SystemExit
    with patch('sys.stdout', new=StringIO()) as out:
        with patch('sys.argv', new=["koji", name, "--help"]):
            assert_raises(SystemExit,
                          command, goptions, None, ("--help",))
        outhelp = out.getvalue()

    # now we'll load the expected help output from the first literal
    # block from the reST doc sources
    usage = find_usage("docs/commands/%s.rst" % name)
    assert_true(usage is not None)

    # Then we can compare what we got from the command with what was
    # in the docs
    expected = usage.strip()
    found = outhelp.strip()
    assert_equal(expected, found)


def test_command_help():
    # verify the expected entry points resolve and can be initialized,
    # and that when invoked with --help they produce output that
    # matches our documentation

    for name in ENTRY_POINTS:
        yield check_command_help, name


# The end.
