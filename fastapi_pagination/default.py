from __future__ import annotations

from typing import Generic, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel, conint, Field

from .bases import AbstractParams, BasePage, RawParams

T = TypeVar("T")


class Params(BaseModel, AbstractParams):
    page: int = Field(Query(1, ge=1, description="Page number"))
    size: int = Field(Query(50, ge=1, le=100, description="Page size"))

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=int(self.size),
            offset=int(self.size) * (int(self.page) - 1),
        )


class Page(BasePage[T], Generic[T]):
    page: conint(ge=1)  # type: ignore
    size: conint(ge=1)  # type: ignore

    __params_type__ = Params

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        total: int,
        params: AbstractParams,
    ) -> Page[T]:
        if not isinstance(params, Params):
            raise ValueError("Page should be used with Params")

        return cls(
            total=total,
            items=items,
            page=params.page,
            size=params.size,
        )


__all__ = [
    "Params",
    "Page",
]
