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


from koji import ClientSession
from typing import List, Optional, Union

from .types import (
    CGInfo, DecoratedUserInfo, NamedCGInfo,
    PermInfo, PermSpec, UserInfo, UserSpec, )


def collect_userinfo(
        session: ClientSession,
        user: UserSpec) -> DecoratedUserInfo:
    ...


def collect_cg_access(
        session: ClientSession,
        user: UserSpec) -> List[NamedCGInfo]:
    ...


def collect_cgs(
        session: ClientSession,
        name: Optional[str] = ...) -> List[NamedCGInfo]:
    ...


def collect_perminfo(
        session: ClientSession,
        permission: PermSpec) -> PermInfo:
    ...


#
# The end.
