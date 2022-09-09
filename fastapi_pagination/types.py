from typing_extensions import Literal, TypeAlias

PaginationQueryType: TypeAlias = Literal["limit-offset", "row-number", None]

__all__ = [
    "PaginationQueryType",
]
