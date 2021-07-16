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


from configparser import ConfigParser
from datetime import datetime
from typing import (
    Any, Callable, Dict, Iterable, Iterator, List,
    Optional, Tuple, )


def chunkseq(
        seq: Iterable,
        chunksize: int) -> Iterator[Iterable]:
    ...


def escapable_replace(
        orig: str,
        character: str,
        replacement: str) -> str:
    ...


def fnmatches(
        value: str,
        patterns: Iterable[str],
        ignore_case: bool = ...) -> bool:
    ...


def update_extend(
        dict_orig: Dict[Any, list],
        *dict_additions: Dict[Any, list]) -> Dict[Any, list]:
    ...



def merge_extend(
        *dict_additions: Dict[Any, list]) -> Dict[Any, list]:
    ...


def globfilter(
        seq: Iterable,
        patterns: Iterable[str],
        key: Optional[Callable[[Any], str]] = ...,
        invert: bool = ...,
        ignore_case: bool = ...) -> Iterable:
    ...


def unique(
        sequence: Iterable[Any],
        key: Optional[Callable[[Any], str]] = ...) -> List[Any]:
    ...


def parse_datetime(
        src: str,
        strict: bool = ...) -> Optional[datetime]:
    ...


def find_config_dirs() -> Tuple[str, str]:
    ...


def find_config_files(
        dirs: Optional[Iterable[str]] = ...) -> List[str]:
    ...


def load_full_config(
        config_files: Optional[Iterable[str]] = ...) -> ConfigParser:
    ...


def get_plugin_config(
        conf: ConfigParser,
        plugin: str,
        profile: Optional[str] = ...) -> Dict[str, Any]:
    ...


def load_plugin_config(
        plugin: str,
        profile: Optional[str] = ...) -> Dict[str, Any]:
    ...


#
# The end.
