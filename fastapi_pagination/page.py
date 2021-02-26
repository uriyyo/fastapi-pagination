from __future__ import annotations

from abc import ABC
from typing import Generic, Sequence, TypeVar

from pydantic import conint

from .bases import AbstractPage, AbstractParams
from .params import PaginationParams

T = TypeVar("T")
C = TypeVar("C")


class BasePage(AbstractPage[T], Generic[T], ABC):
    items: Sequence[T]
    total: conint(ge=0)  # type: ignore


class Page(BasePage[T], Generic[T]):
    page: conint(ge=0)  # type: ignore
    size: conint(gt=0)  # type: ignore

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
    limit: conint(gt=0)  # type: ignore
    offset: conint(ge=0)  # type: ignore

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
