from __future__ import annotations

from typing import Any, Generic, Optional, Sequence, TypeVar
from math import ceil
from fastapi import Query
from pydantic import BaseModel

from .bases import AbstractParams, BasePage, RawParams
from .types import GreaterEqualOne

T = TypeVar("T")


class CustomPageParams(BaseModel, AbstractParams):
    page: int = Query(1, ge=1, description="Page number")
    size: int = Query(50, ge=1, le=100, description="Page size")

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size,
            offset=self.size * (self.page - 1),
        )


class CustomPage(BasePage[T], Generic[T]):
    page: GreaterEqualOne
    size: GreaterEqualOne

    __params_type__ = CustomPageParams

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: AbstractParams,
        *,
        total: Optional[int] = None,
        **kwargs: Any,
    ) -> CustomPage[T]:
        if not isinstance(params, CustomPageParams):
            raise ValueError("Page should be used with Params")

        pages = ceil(total / params.size)
        return cls(
            total=total,
            items=items,
            page=params.page,
            size=params.size,
            pages=pages,
            next_page=params.page + 1 if params.page < pages else None,
            previous_page=params.page - 1 if params.page > 1 else None,            
            **kwargs,
        )


__all__ = [
    "CustomPageParams",
    "CustomPage",
]
