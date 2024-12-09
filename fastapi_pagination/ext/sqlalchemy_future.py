from __future__ import annotations

__all__ = [
    "paginate",
]

from typing import Any, Optional, Tuple, Union

from sqlalchemy.future import Connection
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select
from typing_extensions import deprecated

from ..bases import AbstractParams
from ..types import AdditionalData, SyncItemsTransformer
from .sqlalchemy import paginate as _paginate


@deprecated(
    "fastapi_pagination.ext.sqlalchemy_future module is deprecated, "
    "please use fastapi_pagination.ext.sqlalchemy module instead"
    "This module will be removed in the next major release (0.13.0).",
)
def paginate(
    conn: Union[Connection, Session],
    query: Select[Tuple[Any, ...]],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    return _paginate(
        conn,
        query,
        params,
        transformer=transformer,
        additional_data=additional_data,
        unique=unique,
    )
