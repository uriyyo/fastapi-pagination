from typing import Union

from typing_extensions import Literal, TypeAlias

Cursor = Union[str, bytes]
ParamsType: TypeAlias = Literal["cursor", "limit-offset"]
PaginationQueryType: TypeAlias = Literal["limit-offset", "row-number", None]

__all__ = [
    "Cursor",
    "ParamsType",
    "PaginationQueryType",
]
