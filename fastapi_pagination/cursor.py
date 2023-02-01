from __future__ import annotations

__all__ = [
    "CursorPage",
    "CursorParams",
]

from base64 import b64decode, b64encode
from typing import (
    Any,
    ClassVar,
    Generic,
    Optional,
    Sequence,
    TypeVar,
    overload,
)
from urllib.parse import quote, unquote

from fastapi import Query
from pydantic import BaseModel, Field
from typing_extensions import Literal

from .bases import AbstractPage, AbstractParams, CursorRawParams
from .types import Cursor

T = TypeVar("T")


@overload
def decode_cursor(cursor: Optional[str], *, to_str: Literal[True] = True) -> Optional[str]:
    pass


@overload
def decode_cursor(cursor: Optional[str], *, to_str: Literal[False]) -> Optional[bytes]:
    pass


@overload
def decode_cursor(cursor: Optional[str], *, to_str: bool) -> Optional[Cursor]:
    pass


def decode_cursor(cursor: Optional[str], *, to_str: bool = True) -> Optional[Cursor]:
    if cursor:
        res = b64decode(unquote(cursor).encode())
        return res.decode() if to_str else res

    return None


def encode_cursor(cursor: Optional[Cursor]) -> Optional[str]:
    if cursor:
        cursor = cursor.encode() if isinstance(cursor, str) else cursor
        return quote(b64encode(cursor).decode())

    return None


class CursorParams(BaseModel, AbstractParams):
    cursor: Optional[str] = Query(None, description="Cursor for the next page")
    size: int = Query(50, ge=0, description="Page offset")

    str_cursor: ClassVar[bool] = True

    def to_raw_params(self) -> CursorRawParams:
        return CursorRawParams(
            cursor=decode_cursor(self.cursor, to_str=self.str_cursor),
            size=self.size,
        )


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
        next_: Optional[Cursor] = None,
        previous: Optional[Cursor] = None,
        **kwargs: Any,
    ) -> CursorPage[T]:
        return cls(
            items=items,
            next_page=encode_cursor(next_),
            previous_page=encode_cursor(previous),
            **kwargs,
        )
