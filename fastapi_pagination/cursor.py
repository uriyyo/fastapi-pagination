from __future__ import annotations

__all__ = [
    "CursorDecoder",
    "CursorEncoder",
    "CursorPage",
    "CursorParams",
]

import binascii
from base64 import b64decode, b64encode
from collections.abc import Sequence
from typing import (
    Any,
    Callable,
    ClassVar,
    Generic,
    Optional,
    overload,
)
from urllib.parse import quote, unquote

from fastapi import HTTPException, Query, status
from pydantic import BaseModel, Field
from typing_extensions import Literal, TypeAlias, TypeVar

from .bases import AbstractParams, BasePage, CursorRawParams
from .types import Cursor
from .utils import create_pydantic_model

TAny = TypeVar("TAny", default=Any)

CursorEncoder: TypeAlias = "Callable[[CursorParams, Optional[Cursor]], Optional[str]]"
CursorDecoder: TypeAlias = "Callable[[CursorParams, Optional[str]], Optional[Cursor]]"


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
        except (binascii.Error, UnicodeDecodeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor value",
            ) from None

    return None


def default_encoder(cursor: bytes) -> str:
    return b64encode(cursor).decode()


def encode_cursor(
    cursor: Optional[Cursor],
    *,
    quoted: bool = True,
    encoder: Callable[[bytes], str] = default_encoder,
) -> Optional[str]:
    if cursor:
        cursor = cursor.encode() if isinstance(cursor, str) else cursor
        encoded = encoder(cursor)

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
            cursor=self.decode_cursor(self.cursor),
            size=self.size,
        )

    def encode_cursor(self, cursor: Optional[Cursor]) -> Optional[str]:
        return encode_cursor(cursor, quoted=self.quoted_cursor)

    def decode_cursor(self, cursor: Optional[str]) -> Optional[Cursor]:
        return decode_cursor(cursor, to_str=self.str_cursor, quoted=self.quoted_cursor)


class CursorPage(BasePage[TAny], Generic[TAny]):
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
        items: Sequence[TAny],
        params: AbstractParams,
        *,
        current: Optional[Cursor] = None,
        current_backwards: Optional[Cursor] = None,
        next_: Optional[Cursor] = None,
        previous: Optional[Cursor] = None,
        **kwargs: Any,
    ) -> CursorPage[TAny]:
        if not isinstance(params, CursorParams):
            raise TypeError("CursorPage should be used with CursorParams")

        return create_pydantic_model(
            cls,
            items=items,
            current_page=params.encode_cursor(current),
            current_page_backwards=params.encode_cursor(current_backwards),
            next_page=params.encode_cursor(next_),
            previous_page=params.encode_cursor(previous),
            **kwargs,
        )
