from abc import ABC, abstractmethod
from contextvars import ContextVar
from typing import Generic, Sequence, Type, TypeVar

from pydantic import Field
from pydantic.generics import GenericModel

from .params import LimitOffsetPaginationParams, PaginationParamsType

T = TypeVar("T")
C = TypeVar("C")


class BasePage(GenericModel, Generic[T], ABC):
    items: Sequence[T]
    total: int = Field(..., ge=0)

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    @abstractmethod
    def create(cls: Type[C], items: Sequence[T], total: int, params: PaginationParamsType) -> C:
        pass


class Page(BasePage[T], Generic[T]):
    page: int = Field(..., ge=0)
    size: int = Field(..., gt=0)

    @classmethod
    def create(cls, items: Sequence[T], total: int, params: PaginationParamsType) -> "Page[T]":
        if isinstance(params, LimitOffsetPaginationParams):
            raise ValueError("Page can't be used with limit offset params")

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
    def create(cls, items: Sequence[T], total: int, params: PaginationParamsType) -> "LimitOffsetPage[T]":
        params = params.to_limit_offset()

        return cls(
            total=total,
            items=items,
            limit=params.limit,
            offset=params.offset,
        )


PageType: ContextVar[Type[BasePage]] = ContextVar("PageCls", default=Page)


def create_page(items: Sequence[T], total: int, params: PaginationParamsType) -> BasePage[T]:
    return PageType.get().create(items, total, params)


__all__ = ["BasePage", "PageType", "Page", "LimitOffsetPage", "create_page"]
