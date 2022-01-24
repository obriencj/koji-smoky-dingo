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


from io import StringIO
from nose.tools import assert_equal, assert_raises, assert_true
from pkg_resources import EntryPoint
from unittest.mock import patch

from . import ENTRY_POINTS
from ..cli.docs import usage_normalize, find_usage


def check_standalone_help(cmdname):
    ref = ENTRY_POINTS[cmdname]

    ep = EntryPoint.parse("=".join([cmdname, ref]))
    name = ep.name

    if hasattr(ep, "resolve"):
        #new environments
        command = ep.resolve()
    else:
        # old environments
        command = ep.load(require=False)

    # launch the loaded command with the --help option, and collect
    # its output. Also ensures that it causes the expected SystemExit
    with patch('sys.stdout', new=StringIO()) as out:
        with patch('sys.argv', new=[name, "--help"]):
            assert_raises(SystemExit, command)
        outhelp = out.getvalue()

    # now we'll load the expected help output from the first literal
    # block from the reST doc sources
    usage = find_usage("docs/standalone/%s.rst" % name)
    assert_true(usage is not None)

    # Then we can compare what we got from the command with what was
    # in the docs
    expected = usage_normalize(usage)
    found = usage_normalize(outhelp)

    assert_equal(expected, found)


def test_standalone_help():
    # verify the expected entry points resolve and can be initialized,
    # and that when invoked with --help they produce output that
    # matches our documentation

    for name in ENTRY_POINTS:
        yield check_standalone_help, name


#
# The end.
