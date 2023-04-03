from __future__ import annotations

__all__ = [
    "paginate",
    "exec_pagination",
    "async_exec_pagination",
]

from typing import Any, Optional, Union

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.future import Connection, Engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select
from sqlalchemy.util import greenlet_spawn

from .sqlalchemy import (
    count_query,
    paginate_query,
)
from .utils import unwrap_scalars
from ..api import create_page
from ..bases import AbstractPage, AbstractParams, is_cursor
from ..types import AdditionalData
from ..utils import verify_params

try:
    from sqlakeyset import paging
except ImportError:
    paging = None


def _maybe_unique(result: Any, unique: bool) -> Any:
    return (result.unique() if unique else result).all()


def exec_pagination(
    query: Select,
    params: AbstractParams,
    conn: Union[Engine, Connection, Session],
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> AbstractPage[Any]:
    raw_params = params.to_raw_params()

    if is_cursor(raw_params):
        if paging is None:
            raise ImportError("sqlakeyset is not installed")

        page = paging.select_page(
            conn,
            selectable=query,
            per_page=raw_params.size,
            page=raw_params.cursor,
        )

        return create_page(
            unwrap_scalars([*page]),
            params=params,
            previous=page.paging.bookmark_previous,
            next_=page.paging.bookmark_next,
            **(additional_data or {}),
        )
    else:
        (total,) = conn.execute(count_query(query)).scalars()
        query = paginate_query(query, params)
        items = _maybe_unique(conn.execute(query), unique)

        return create_page(unwrap_scalars(items), total, params, **(additional_data or {}))


def _get_sync_conn_from_async(
    conn: Union[AsyncConnection, AsyncSession]
) -> Union[Session, Connection]:  # pragma: no cover
    try:
        return conn.sync_session  # type: ignore
    except AttributeError:
        pass

    try:
        return conn.sync_connection  # type: ignore
    except AttributeError:
        pass

    raise TypeError("conn must be an AsyncConnection or AsyncSession")


async def async_exec_pagination(
    query: Select,
    params: AbstractParams,
    conn: Union[AsyncConnection, AsyncSession],
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> AbstractPage[Any]:  # pragma: no cover
    return await greenlet_spawn(
        exec_pagination,
        query=query,
        params=params,
        conn=_get_sync_conn_from_async(conn),
        additional_data=additional_data,
        unique=unique,
    )


def paginate(
    conn: Union[Connection, Engine, Session],
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    params, _ = verify_params(params, "limit-offset", "cursor")
    return exec_pagination(query, params, conn, additional_data, unique)
