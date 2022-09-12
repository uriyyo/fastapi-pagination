from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional, Union

from sqlalchemy.future import Connection, Engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams
from ..types import PaginationQueryType
from .sqlalchemy import count_query, paginate_query
from .utils import unwrap_scalars


def exec_pagination(
    query: Select,
    params: AbstractParams,
    db_exec: Callable[..., Any],
    query_type: PaginationQueryType = None,
    unwrap: bool = True,
) -> AbstractPage[Any]:
    raw_params = params.to_raw_params()

    if raw_params.need_total:
        (total,) = db_exec(count_query(query)).scalars()
    else:
        total = None

    query, process_items = paginate_query(query, params, query_type)
    items = db_exec(query)
    items = process_items(items.unique().all(), params)

    return create_page(unwrap_scalars(items) if unwrap else items, total, params)


async def async_exec_pagination(
    query: Select,
    params: AbstractParams,
    db_exec: Callable[..., Awaitable[Any]],
    query_type: PaginationQueryType = None,
    unwrap: bool = True,
) -> AbstractPage[Any]:
    raw_params = params.to_raw_params()

    if raw_params.need_total:
        (total,) = (await db_exec(count_query(query))).scalars()
    else:
        total = None

    query, process_items = paginate_query(query, params, query_type)
    res = await db_exec(query)
    items = process_items(res.unique().all(), params)

    return create_page(unwrap_scalars(items) if unwrap else items, total, params)


def paginate(
    conn: Union[Connection, Engine, Session],
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    query_type: PaginationQueryType = None,
) -> AbstractPage[Any]:
    params = resolve_params(params)
    return exec_pagination(query, params, conn.execute, query_type)


__all__ = [
    "paginate",
    "exec_pagination",
    "async_exec_pagination",
]
