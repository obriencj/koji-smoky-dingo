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


import re

from argparse import HelpFormatter
from docutils.frontend import OptionParser
from docutils.nodes import GenericNodeVisitor
from docutils.parsers.rst import Parser
from docutils.utils import new_document
from functools import partial
from io import StringIO
from nose.tools import assert_equal, assert_raises, assert_true
from unittest.mock import patch

from kojismokydingo.cli import SmokyDingo, space_normalize

from . import ENTRY_POINTS, GOptions, get_entry_point, entry_point_load


_varargs = re.compile(r'\[(\w*) \[\1 \.\.\.\]\]')
_options = re.compile(r'^optional arguments:', flags=re.M)


def usage_normalize(text):

    # some versions of argparse print the options header as "options:"
    # and others as "optional arguments:" so we'll convert to the
    # short version.
    text = _options.sub("options:", text)

    text = text.replace("|", " ][ ")
    text = space_normalize(text)

    # some versions of argparse present varargs as [ARG [ARG ...]] and
    # others present them as just [ARG ...]. This regex converts the
    # former to the latter
    text = _varargs.sub(lambda m: f"[{m[1]} ...]", text)

    return text


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

    ep = get_entry_point(cmdname)
    name = ep.name

    cmd_cls = entry_point_load(ep)
    command = cmd_cls(name)

    # this ugly little dance needs to happen because the default
    # formatter checks console width and will word-wrap on hyphens in
    # some cases. So we will force it to work with a width of 80 chars
    orig_parser = command.parser
    def wrap_parser():
        argp = orig_parser()
        argp.formatter_class = partial(HelpFormatter, width=80)
        return argp
    command.parser = wrap_parser

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
    expected = usage_normalize(usage)
    found = usage_normalize(outhelp)

    assert_equal(expected, found)


def test_command_help():
    # verify the expected entry points resolve and can be initialized,
    # and that when invoked with --help they produce output that
    # matches our documentation

    for name in ENTRY_POINTS:
        yield check_command_help, name


#
# The end.
