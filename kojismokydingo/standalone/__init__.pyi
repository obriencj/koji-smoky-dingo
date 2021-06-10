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


import abc

from argparse import ArgumentParser
from typing import Any, Optional

from .. import ManagedClientSession
from ..cli import SmokyDingo


class LonelyDingo(SmokyDingo, metaclass=abc.ABCMeta):

    default_profile: Optional[str] = ...

    session: ManagedClientSession = ...

    @classmethod
    def main(
            cls,
            name: Optional[Any] = ...,
            args: Optional[Any] = ...) -> int:
        ...

    def create_session(
            self,
            options: Any) -> ManagedClientSession:
        ...

    def parser(self) -> ArgumentParser:
        ...

    def profile_arguments(
            self,
            parser: ArgumentParser) -> ArgumentParser:
        ...

    def __call__( # type: ignore
            self,
            args: Optional[list[str]] = ...) -> int:
        ...


class AnonLonelyDingo(LonelyDingo, metaclass=abc.ABCMeta):

    def create_session(
            self,
            options: Any) -> ManagedClientSession:
        ...


#
# The end.
