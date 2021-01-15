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


from mock import MagicMock, patch
from pkg_resources import resource_filename
from six.moves.configparser import ConfigParser
from unittest import TestCase

from kojismokydingo.conf import (
    find_config_dirs,
    find_config_files,
    load_full_config,
    load_plugin_config,
    get_plugin_config,
)


def test_dirs():
    return (resource_filename(__name__, "data/system"),
            resource_filename(__name__, "data/user"))


def faux_appdir():
    fakes = test_dirs()

    obj = MagicMock()

    site_config_dir = obj.site_config_dir
    site_config_dir.side_effect = [fakes[0]]

    user_config_dir = obj.user_config_dir
    user_config_dir.side_effect = [fakes[1]]

    return obj


class TestConfig(TestCase):


    def test_find_dirs(self):
        with patch('kojismokydingo.conf.appdirs', new=None):
            dirs = find_config_dirs()

        self.assertEqual(len(dirs), 2)
        self.assertEqual(dirs[0], "/etc/xdg/ksd/")
        self.assertTrue(dirs[1].endswith(".config/ksd/"))

        meh = faux_appdir()
        with patch('kojismokydingo.conf.appdirs', new=meh):
            dirs = find_config_dirs()

        self.assertEqual(len(dirs), 2)
        self.assertEqual(dirs, test_dirs())
        self.assertEqual(meh.site_config_dir.call_count, 1)
        self.assertEqual(meh.user_config_dir.call_count, 1)


    def test_find_files(self):

        with patch('kojismokydingo.conf.appdirs', new=faux_appdir()) as meh:
            found = find_config_files()

        self.assertEqual(len(found), 3)
        self.assertEqual(meh.site_config_dir.call_count, 1)
        self.assertEqual(meh.user_config_dir.call_count, 1)


    def test_load_full_config(self):
        with patch('kojismokydingo.conf.appdirs', new=faux_appdir()) as meh:
            conf = load_full_config()

        self.assertTrue(isinstance(conf, ConfigParser))
        self.assertTrue(conf.has_section("example_1"))
        self.assertTrue(conf.has_section("example_2"))
        self.assertTrue(conf.has_section("example_2:test"))
        self.assertTrue(conf.has_section("example_3"))
        self.assertTrue(conf.has_section("example_3:test"))
        self.assertTrue(conf.has_section("example_3:foo"))


    def test_load_plugin_config(self):
        with patch('kojismokydingo.conf.appdirs', new=faux_appdir()):
            conf = load_plugin_config("example_1")
            self.assertTrue(conf)
            self.assertEqual(type(conf), dict)
            self.assertEqual(conf["data"], '111')
            self.assertEqual(conf["flavor"], 'tasty')

        with patch('kojismokydingo.conf.appdirs', new=faux_appdir()):
            conf = load_plugin_config("example_2")
            self.assertTrue(conf)
            self.assertEqual(type(conf), dict)
            self.assertEqual(conf["data"], '244')
            self.assertEqual(conf["flavor"], 'meh')

        with patch('kojismokydingo.conf.appdirs', new=faux_appdir()):
            conf = load_plugin_config("example_2", "test")
            self.assertTrue(conf)
            self.assertEqual(type(conf), dict)
            self.assertEqual(conf["data"], '220')
            self.assertEqual(conf["flavor"], 'meh')

        with patch('kojismokydingo.conf.appdirs', new=faux_appdir()):
            conf = load_plugin_config("example_3")
            self.assertTrue(conf)
            self.assertEqual(type(conf), dict)
            self.assertEqual(conf["data"], '300')


    def test_merge(self):
        dirs = test_dirs()
        files = find_config_files(dirs)
        full_conf = load_full_config(files)

        conf = get_plugin_config(full_conf, "example_1")
        self.assertTrue(conf)
        self.assertEqual(type(conf), dict)
        self.assertEqual(conf["data"], '111')
        self.assertEqual(conf["flavor"], 'tasty')

        conf = get_plugin_config(full_conf, "example_2")
        self.assertTrue(conf)
        self.assertEqual(type(conf), dict)
        self.assertEqual(conf["data"], '244')
        self.assertEqual(conf["flavor"], 'meh')

        conf = get_plugin_config(full_conf, "example_2", "test")
        self.assertTrue(conf)
        self.assertEqual(type(conf), dict)
        self.assertEqual(conf["data"], '220')
        self.assertEqual(conf["flavor"], 'meh')

        conf = get_plugin_config(full_conf, "example_3")
        self.assertTrue(conf)
        self.assertEqual(type(conf), dict)
        self.assertEqual(conf["data"], '300')


#
# The end.
