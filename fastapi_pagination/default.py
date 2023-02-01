from __future__ import annotations

__all__ = [
    "Params",
    "Page",
]

from typing import Any, Generic, Optional, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel
from math import ceil

from .bases import AbstractParams, BasePage, RawParams
from .types import GreaterEqualOne, GreaterEqualZero

T = TypeVar("T")


class Params(BaseModel, AbstractParams):
    page: int = Query(1, ge=1, description="Page number")
    size: int = Query(50, ge=1, le=100, description="Page size")

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size,
            offset=self.size * (self.page - 1),
        )


class Page(BasePage[T], Generic[T]):
    page: GreaterEqualOne
    size: GreaterEqualOne
    pages: Optional[GreaterEqualZero] = None

    __params_type__ = Params

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: AbstractParams,
        *,
        total: Optional[int] = None,
        **kwargs: Any,
    ) -> Page[T]:
        if not isinstance(params, Params):
            raise ValueError("Page should be used with Params")

        pages = ceil(total / params.size) if total is not None else None

        return cls(
            total=total,
            items=items,
            page=params.page,
            size=params.size,
            pages=pages,
            **kwargs,
        )
