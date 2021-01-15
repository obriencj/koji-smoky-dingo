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
Koji Smoky Dingo - client plugin configuration

This module provides a re-usable per-plugin (and optionally
per-profile) configuration mechanism.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GPL v3
"""


from glob import glob
from os.path import expanduser, isdir, join
from six.moves.configparser import ConfigParser


try:
    import appdirs
except ImportError:
    appdirs = None


__all__ = (
    "find_config_dirs",
    "find_config_files",
    "get_plugin_config",
    "load_full_config",
    "load_plugin_config",
)


def find_config_dirs():
    """
    The site and user configuration dirs, as a tuple. Attempts to use
    the ``appdirs`` package if it is available.

    :rtype: tuple[str]
    """

    if appdirs is None:
        site_conf_dir = "/etc/xdg/ksd/"
        user_conf_dir = expanduser("~/.config/ksd/")
    else:
        site_conf_dir = appdirs.site_config_dir("ksd")
        user_conf_dir = appdirs.user_config_dir("ksd")

    return (site_conf_dir, user_conf_dir)


def find_config_files(dirs=None):
    """
    The ordered list of configuration files to be loaded.

    If `dirs` is specified, it must be a sequence of directory names,
    from which conf files will be loaded in order. If unspecified,
    defaults to the result of `find_config_dirs`

    :param dirs: list of directories to look for config files within
    :type dirs: list[str], optional

    :rtype: list[str]
    """

    if dirs is None:
        dirs = find_config_dirs()

    found = []

    for confdir in dirs:
        if isdir(confdir):
            wanted = join(confdir, "*.conf")
            found.extend(sorted(glob(wanted)))

    return found


def load_full_config(config_files=None):
    """
    Configuration object representing the full merged view of config
    files.

    If `config_files` is None, use the results of `find_config_files`.
    Otherwise, `config_files` must be a sequence of filenames.

    :rtype: ConfigParser
    """

    if config_files is None:
        config_files = find_config_files()

    conf = ConfigParser()
    conf.read(config_files)

    return conf


def get_plugin_config(conf, plugin, profile=None):
    """
    Given a loaded configuration, return the section specific to the
    given plugin, and optionally profile

    :param conf: Full configuration
    :type conf: ConfigParser

    :param plugin: Plugin name
    :type plugin: str

    :param profile: Profile name
    :type profile: str, optional

    :rtype: dict[str,object]
    """

    plugin_conf = {}

    if conf.has_section(plugin):
        plugin_conf.update(conf.items(plugin))

    if profile is not None:
        profile = ":".join((plugin, profile))
        if conf.has_section(profile):
            plugin_conf.update(conf.items(profile))

    return plugin_conf


def load_plugin_config(plugin, profile=None):
    """
    Configuration specific to a given plugin, and optionally profile

    :param plugin: Plugin name
    :type plugin: str

    :param profile: Profile name
    :type profile: str, optional

    :rtype: dict[str,object]
    """

    conf = load_full_config()
    return get_plugin_config(conf, plugin, profile)


#
# The end.
