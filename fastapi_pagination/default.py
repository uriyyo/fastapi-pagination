from __future__ import annotations

from typing import Generic, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel, conint

from .bases import AbstractParams, BasePage, RawParams

T = TypeVar("T")


class Params(BaseModel, AbstractParams):
    page: int = Query(0, ge=0, description="Page number")
    size: int = Query(50, gt=0, le=100, description="Page size")

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size,
            offset=self.size * self.page,
        )


class Page(BasePage[T], Generic[T]):
    page: conint(ge=0)  # type: ignore
    size: conint(gt=0)  # type: ignore

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


__all__ = ["Params", "Page"]
