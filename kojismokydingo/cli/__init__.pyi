

from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser
from koji import ClientSession
from typing import Any, Callable, Iterable, List, Optional, Union


def pretty_json(
        data: Any,
        output: Optional[Any] = ...,
        **pretty: Any) -> None:
    ...


def find_action(
        parser: Any,
        key: Any):
    ...


def remove_action(
        parser: Any,
        key: Any) -> None:
    ...


def resplit(
        arglist: Any,
        sep: str = ...) -> List[str]:
    ...


def open_output(
        filename: str = ...,
        append: Optional[Any] = ...) -> None:
    ...


def clean_lines(
        lines: Any,
        skip_comments: bool = ...) -> Iterable[str]:
    ...


def read_clean_lines(
        filename: str = ...,
        skip_comments: bool = ...) -> Iterable[str]:
    ...


printerr: Callable


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
