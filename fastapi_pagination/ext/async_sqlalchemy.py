from __future__ import annotations

__all__ = ["paginate"]

import warnings
from typing import Any, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection
from sqlalchemy.sql import Select

from ..bases import AbstractParams
from ..types import AdditionalData
from .sqlalchemy import paginate as _paginate


async def paginate(
    conn: Union[AsyncSession, AsyncConnection],
    query: Select[Any],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    warnings.warn(
        "fastapi_pagination.ext.async_sqlalchemy module is deprecated, "
        "please use fastapi_pagination.ext.sqlalchemy module instead",
        DeprecationWarning,
        stacklevel=2,
    )

    return await _paginate(conn, query, params, additional_data=additional_data, unique=unique)
