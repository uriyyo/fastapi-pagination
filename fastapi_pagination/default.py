from __future__ import annotations

__all__ = [
    "OptionalParams",
    "Page",
    "Params",
]

from math import ceil
from typing import Any, Generic, Optional, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel
from typing_extensions import deprecated

from .bases import AbstractParams, BasePage, RawParams
from .types import GreaterEqualOne, GreaterEqualZero
from .utils import create_pydantic_model

T = TypeVar("T")


class Params(BaseModel, AbstractParams):
    page: int = Query(1, ge=1, description="Page number")
    size: int = Query(50, ge=1, le=100, description="Page size")

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size if self.size is not None else None,
            offset=self.size * (self.page - 1) if self.page is not None and self.size is not None else None,
        )


@deprecated(
    "`OptionalParams` class is deprecated, please use "
    "`CustomizePage[Page, UseOptionalParams()]` instead. "
    "This class will be removed in the next major release (0.13.0)."
)
class OptionalParams(Params):
    page: Optional[int] = Query(None, ge=1, description="Page number")  # type: ignore[assignment]
    size: Optional[int] = Query(None, ge=1, le=100, description="Page size")  # type: ignore[assignment]


class Page(BasePage[T], Generic[T]):
    page: Optional[GreaterEqualOne]
    size: Optional[GreaterEqualOne]
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
            raise TypeError("Page should be used with Params")

        size = params.size if params.size is not None else (total or None)
        page = params.page if params.page is not None else 1

        if size in {0, None}:
            pages = 0
        elif total is not None:
            pages = ceil(total / size)
        else:
            pages = None

        return create_pydantic_model(
            cls,
            total=total,
            items=items,
            page=page,
            size=size,
            pages=pages,
            **kwargs,
        )
