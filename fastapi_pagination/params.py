from typing import Union

from attr import dataclass
from fastapi import Query


@dataclass
class PaginationParams:
    page: int = Query(0, ge=0, description="Page number")
    size: int = Query(50, gt=0, description="Page size")

    def to_limit_offset(self) -> "LimitOffsetPaginationParams":
        return LimitOffsetPaginationParams(
            limit=self.size,
            offset=self.size * self.page,
        )


@dataclass
class LimitOffsetPaginationParams:
    limit: int = Query(50, description="Page size limit")
    offset: int = Query(0, description="Page offset")

    def to_limit_offset(self) -> "LimitOffsetPaginationParams":
        return self


PaginationParamsType = Union[PaginationParams, LimitOffsetPaginationParams]

__all__ = ["PaginationParamsType", "LimitOffsetPaginationParams", "PaginationParams"]
