from __future__ import annotations

from base64 import b64decode, b64encode
from typing import Any, Generic, Optional, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

from .bases import AbstractPage, AbstractParams, CursorRawParams

T = TypeVar("T")


class CursorParams(BaseModel, AbstractParams):
    cursor: Optional[str] = Query(None, description="Cursor for the next page")
    size: int = Query(50, ge=0, description="Page offset")

    def to_raw_params(self) -> CursorRawParams:
        return CursorRawParams(
            cursor=decode_cursor(self.cursor),
            size=self.size,
        )


def decode_cursor(cursor: Optional[str]) -> Optional[str]:
    if cursor:
        return b64decode(cursor.encode("utf-8")).decode("utf-8")

    return None


def encode_cursor(cursor: Optional[str]) -> Optional[str]:
    if cursor:
        return b64encode(cursor.encode("utf-8")).decode("utf-8")

    return None


class CursorPage(AbstractPage[T], Generic[T]):
    items: Sequence[T]

    previous_page: Optional[str] = Field(None, description="Cursor for the previous page")
    next_page: Optional[str] = Field(None, description="Cursor for the next page")

    __params_type__ = CursorParams

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: AbstractParams,
        *,
        next_: Optional[str] = None,
        previous: Optional[str] = None,
        **kwargs: Any,
    ) -> CursorPage[T]:
        return cls(
            items=items,
            next_page=encode_cursor(next_),
            previous_page=encode_cursor(previous),
            **kwargs,
        )


__all__ = [
    "CursorPage",
    "CursorParams",
]
