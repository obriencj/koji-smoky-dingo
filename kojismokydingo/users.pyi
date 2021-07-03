

from koji import ClientSession
from typing import List, Optional, Union

from .types import CGInfo, NamedCGInfo, UserInfo, UserSpec


def collect_userinfo(
        session: ClientSession,
        user: UserSpec) -> UserInfo:
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
        permission: Union[str, int]) -> dict:
    ...


#
# The end.
