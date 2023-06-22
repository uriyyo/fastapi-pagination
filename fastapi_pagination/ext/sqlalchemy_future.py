from __future__ import annotations

__all__ = [
    "paginate",
]

import warnings
from typing import Any, Optional, Union

from sqlalchemy.future import Connection
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from ..bases import AbstractParams
from ..types import AdditionalData, SyncItemsTransformer
from .sqlalchemy import paginate as _paginate


def paginate(
    conn: Union[Connection, Session],
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    warnings.warn(
        "fastapi_pagination.ext.sqlalchemy_future module is deprecated, "
        "please use fastapi_pagination.ext.sqlalchemy module instead"
        "This module will be removed in the next major release (0.13.0).",
        DeprecationWarning,
        stacklevel=2,
    )

    return _paginate(
        conn,
        query,
        params,
        transformer=transformer,
        additional_data=additional_data,
        unique=unique,
    )
