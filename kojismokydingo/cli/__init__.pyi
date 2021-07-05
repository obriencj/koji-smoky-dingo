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


from abc import ABCMeta, abstractmethod
from argparse import Action, ArgumentParser
from io import TextIOBase
from koji import ClientSession
from typing import (
    Any, Callable, ContextManager,
    Iterable, List, Optional, Union, )


def pretty_json(
        data: Any,
        output: Optional[TextIOBase] = ...,
        **pretty: Any) -> None:
    ...


def find_action(
        parser: ArgumentParser,
        key: str) -> Optional[Action]:
    ...


def remove_action(
        parser: ArgumentParser,
        key: str) -> None:
    ...


def resplit(
        arglist: List[str],
        sep: str = ...) -> List[str]:
    ...


def open_output(
        filename: str = ...,
        append: Optional[bool] = ...) -> ContextManager:
    ...


def clean_lines(
        lines: Iterable[str],
        skip_comments: bool = ...) -> List[str]:
    ...


def read_clean_lines(
        filename: str = ...,
        skip_comments: bool = ...) -> List[str]:
    ...


def printerr(*values: Any,
             sep: str = ' ',
             end: str = '\n',
             flush: bool = False) -> None:
    ...


def tabulate(
        headings: Any,
        data: Any,
        key: Optional[Any] = ...,
        sorting: int = ...,
        quiet: Optional[Any] = ...,
        out: Optional[Any] = ...) -> None:
    ...


def space_normalize(txt: str) -> str:
    ...


def int_or_str(value: Any) -> Union[int, str]:
    ...


class SmokyDingo(metaclass=ABCMeta):
    group: str = ...
    description: str = ...
    permission: Optional[str] = ...
    name: str = ...
    exported_cli: bool = ...

    config: Any = ...
    goptions: Any = ...
    session: ClientSession = ...

    def __init__(
            self,
            name: Optional[str] = ...):
        ...

    def get_plugin_config(
            self,
            key: str,
            default: Optional[Any] = ...):
        ...

    def parser(
            self) -> ArgumentParser:
        ...

    def arguments(
            self,
            parser: ArgumentParser) -> Optional[ArgumentParser]:
        ...

    def validate(
            self,
            parser: ArgumentParser,
            options: Any) -> None:
        ...

    def pre_handle(
            self,
            options: Any) -> None:
        ...

    @abstractmethod
    def handle(
            self,
            options: Any) -> Any:
        ...

    def activate(
            self) -> None:
        ...

    def deactivate(
            self) -> None:
        ...

    def __call__(
            self,
            goptions: Any,
            session: ClientSession,
            args: List[str]) -> Optional[int]:
        ...


class AnonSmokyDingo(SmokyDingo, metaclass=ABCMeta):
    ...


class TagSmokyDingo(SmokyDingo, metaclass=ABCMeta):
    ...


class TargetSmokyDingo(SmokyDingo, metaclass=ABCMeta):
    ...


class HostSmokyDingo(SmokyDingo, metaclass=ABCMeta):
    ...


#
# The end.
