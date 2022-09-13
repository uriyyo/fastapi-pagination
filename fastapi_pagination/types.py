from typing_extensions import Literal, TypeAlias

ParamsType: TypeAlias = Literal["cursor", "limit-offset"]
PaginationQueryType: TypeAlias = Literal["limit-offset", "row-number", None]

__all__ = [
    "ParamsType",
    "PaginationQueryType",
]
