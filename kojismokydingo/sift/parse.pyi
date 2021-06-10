from .. import BadDingo
from abc import ABCMeta
from io import StringIO
from typing import Any, Optional

class ParserError(BadDingo):
    complaint: str = ...

class RegexError(ParserError):
    complaint: str = ...

class Matcher(metaclass=ABCMeta): ...

class Null(Matcher):
    def __eq__(self, val: Any) -> Any: ...

class Symbol(str, Matcher): ...

class SymbolGroup(Matcher):
    src: Any = ...
    groups: Any = ...
    def __init__(self, src: Any, groups: Any) -> None: ...
    def __iter__(self) -> Any: ...
    def __eq__(self, val: Any) -> Any: ...

class FormattedSeries:
    def __init__(self, fmt: Any, seq: Any) -> None: ...
    def __iter__(self) -> Any: ...
    def __len__(self): ...

class Number(int, Matcher):
    def __eq__(self, val: Any) -> Any: ...

class Regex(Matcher):
    def __init__(self, src: Any, flags: Optional[Any] = ...) -> None: ...
    def __eq__(self, val: Any) -> Any: ...

class Glob(Matcher):
    def __init__(self, src: Any, ignorecase: bool = ...) -> None: ...
    def __eq__(self, val: Any) -> Any: ...

class Item:
    key: Any = ...
    def __init__(self, key: Any) -> None: ...
    def get(self, d: Any) -> None: ...

class ItemMatch(Item):
    def get(self, d: Any) -> None: ...

class AllItems(Item):
    def __init__(self) -> None: ...
    def get(self, d: Any): ...

class ItemPath:
    paths: Any = ...
    def __init__(self, *paths: Any) -> None: ...
    def get(self, data: Any): ...

class Reader(StringIO):
    def __init__(self, source: Any) -> None: ...
    def peek(self, count: int = ...): ...

def parse_exprs(reader: Any, start: Optional[Any] = ..., stop: Optional[Any] = ...) -> None: ...
def convert_escapes(val: Any): ...
def convert_token(val: Any): ...
