from __future__ import annotations

__all__ = [
    "CursorPage",
    "CursorParams",
]

import binascii
from base64 import b64decode, b64encode
from functools import partial
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

from fastapi import HTTPException, Query, status
from pydantic import BaseModel, Field
from typing_extensions import Literal

from .bases import AbstractPage, AbstractParams, CursorRawParams
from .types import Cursor
from .utils import create_pydantic_model

T = TypeVar("T")


@overload
def decode_cursor(cursor: Optional[str], *, to_str: Literal[True] = True, quoted: bool = True) -> Optional[str]:
    pass


@overload
def decode_cursor(cursor: Optional[str], *, to_str: Literal[False], quoted: bool = True) -> Optional[bytes]:
    pass


@overload
def decode_cursor(cursor: Optional[str], *, to_str: bool, quoted: bool = True) -> Optional[Cursor]:
    pass


def decode_cursor(cursor: Optional[str], *, to_str: bool = True, quoted: bool = True) -> Optional[Cursor]:
    if cursor:
        try:
            cursor = unquote(cursor) if quoted else cursor
            res = b64decode(cursor.encode())
            return res.decode() if to_str else res
        except binascii.Error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor value",
            ) from None

    return None


def encode_cursor(cursor: Optional[Cursor], quoted: bool = True) -> Optional[str]:
    if cursor:
        cursor = cursor.encode() if isinstance(cursor, str) else cursor
        encoded = b64encode(cursor).decode()

        if quoted:
            encoded = quote(encoded)

        return encoded

    return None


class CursorParams(BaseModel, AbstractParams):
    cursor: Optional[str] = Query(None, description="Cursor for the next page")
    size: int = Query(50, ge=0, le=100, description="Page size")

    str_cursor: ClassVar[bool] = True
    quoted_cursor: ClassVar[bool] = True

    def to_raw_params(self) -> CursorRawParams:
        return CursorRawParams(
            cursor=decode_cursor(self.cursor, to_str=self.str_cursor, quoted=self.quoted_cursor),
            size=self.size,
        )


class CursorPage(AbstractPage[T], Generic[T]):
    items: Sequence[T]
    total: Optional[int] = Field(None, description="Total items")

    current_page: Optional[str] = Field(None, description="Cursor to refetch the current page")
    current_page_backwards: Optional[str] = Field(
        None,
        description="Cursor to refetch the current page starting from the last item",
    )
    previous_page: Optional[str] = Field(None, description="Cursor for the previous page")
    next_page: Optional[str] = Field(None, description="Cursor for the next page")

    __params_type__ = CursorParams

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: AbstractParams,
        *,
        current: Optional[Cursor] = None,
        current_backwards: Optional[Cursor] = None,
        next_: Optional[Cursor] = None,
        previous: Optional[Cursor] = None,
        **kwargs: Any,
    ) -> CursorPage[T]:
        if not isinstance(params, CursorParams):
            raise TypeError("CursorPage should be used with CursorParams")

        encoder = partial(encode_cursor, quoted=params.quoted_cursor)
        return create_pydantic_model(
            cls,
            items=items,
            current_page=encoder(current),
            current_page_backwards=encoder(current_backwards),
            next_page=encoder(next_),
            previous_page=encoder(previous),
            **kwargs,
        )
