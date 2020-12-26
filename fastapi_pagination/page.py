from __future__ import annotations

from abc import ABC
from typing import Generic, Sequence, TypeVar

from pydantic import Field

from .bases import AbstractPage, AbstractParams
from .params import PaginationParams

T = TypeVar("T")
C = TypeVar("C")


class BasePage(AbstractPage[T], Generic[T], ABC):
    items: Sequence[T]
    total: int = Field(..., ge=0)


class Page(BasePage[T], Generic[T]):
    page: int = Field(..., ge=0)
    size: int = Field(..., gt=0)

    @classmethod
    def create(cls, items: Sequence[T], total: int, params: AbstractParams) -> Page[T]:
        if not isinstance(params, PaginationParams):
            raise ValueError("Page should be used with PaginationParams")

        return cls(
            total=total,
            items=items,
            page=params.page,
            size=params.size,
        )


class LimitOffsetPage(BasePage[T], Generic[T]):
    limit: int = Field(..., gt=0)
    offset: int = Field(..., ge=0)

    @classmethod
    def create(cls, items: Sequence[T], total: int, params: AbstractParams) -> LimitOffsetPage[T]:
        params = params.to_limit_offset()

        return cls(
            total=total,
            items=items,
            limit=params.limit,
            offset=params.offset,
        )


__all__ = ["BasePage", "Page", "LimitOffsetPage"]
