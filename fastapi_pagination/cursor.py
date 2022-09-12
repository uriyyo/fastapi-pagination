from __future__ import annotations

from base64 import b64decode, b64encode
from typing import Any, Dict, Generic, Optional, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field, PrivateAttr

from .bases import AbstractPage, AbstractParams, RawParams

T = TypeVar("T")


class CursorParams(BaseModel, AbstractParams):
    cursor: Optional[str] = Query(None, description="Cursor for the next page")
    size: int = Query(50, ge=0, description="Page offset")

    _metadata: Dict[str, Any] = PrivateAttr(default_factory=dict)

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size,
            offset=0,
            need_total=False,
            metadata=self.metadata,
        )

    @property
    def metadata(self) -> Dict[str, Any]:
        if not self._metadata:
            self._metadata = {
                "type": "cursor",
                "cursor": decode_cursor(self.cursor),
            }

        return self._metadata


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
        total: Optional[int],
        params: AbstractParams,
    ) -> CursorPage[T]:
        return cls(
            items=items,
            next_page=encode_cursor(params.metadata.get("next")),
            previous_page=encode_cursor(params.metadata.get("previous")),
        )


__all__ = [
    "CursorPage",
    "CursorParams",
]
