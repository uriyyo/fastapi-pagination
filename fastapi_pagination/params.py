from typing import Any, Union

from fastapi import Query, params
from pydantic.dataclasses import dataclass


def _get_value(val: Any) -> Any:
    if isinstance(val, params.Query):
        return val.default

    return val


@dataclass
class PaginationParams:
    page: int = Query(0, ge=0, description="Page number")
    size: int = Query(50, gt=0, le=100, description="Page size")

    def __post_init__(self) -> None:
        self.page = _get_value(self.page)
        self.size = _get_value(self.size)

    def to_limit_offset(self) -> "LimitOffsetPaginationParams":
        return LimitOffsetPaginationParams(
            limit=self.size,
            offset=self.size * self.page,
        )


@dataclass
class LimitOffsetPaginationParams:
    limit: int = Query(50, gt=0, le=100, description="Page size limit")
    offset: int = Query(0, ge=0, description="Page offset")

    def __post_init__(self) -> None:
        self.limit = _get_value(self.limit)
        self.offset = _get_value(self.offset)

    def to_limit_offset(self) -> "LimitOffsetPaginationParams":
        return self


PaginationParamsType = Union[PaginationParams, LimitOffsetPaginationParams]

__all__ = ["PaginationParamsType", "LimitOffsetPaginationParams", "PaginationParams"]
