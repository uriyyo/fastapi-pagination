from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional, Union

from sqlalchemy.future import Connection, Engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from ..api import create_page
from ..bases import AbstractPage, AbstractParams
from ..utils import verify_params
from .sqlalchemy import (
    count_query,
    paginate_cursor_process_items,
    paginate_query,
    paginate_using_cursor,
)
from .utils import unwrap_scalars, wrap_scalars


def exec_pagination(
    query: Select,
    params: AbstractParams,
    db_exec: Callable[..., Any],
) -> AbstractPage[Any]:
    raw_params = params.to_raw_params()

    if raw_params.type == "limit-offset":
        (total,) = db_exec(count_query(query)).scalars()
        query = paginate_query(query, params)
        items = db_exec(query).unique().all()

        return create_page(unwrap_scalars(items), total, params)
    else:
        raw_params = raw_params.as_cursor()
        query, info = paginate_using_cursor(query, raw_params)

        items = wrap_scalars(db_exec(query).unique().all())
        items, previous, next_ = paginate_cursor_process_items(items, info, raw_params)

        return create_page(
            unwrap_scalars(items),
            params=params,
            previous=previous,
            next_=next_,
        )


async def async_exec_pagination(
    query: Select,
    params: AbstractParams,
    db_exec: Callable[..., Awaitable[Any]],
) -> AbstractPage[Any]:  # pragma: no cover
    raw_params = params.to_raw_params()

    if raw_params.type == "limit-offset":
        (total,) = (await db_exec(count_query(query))).scalars()
        items = (await db_exec(paginate_query(query, params))).unique().all()

        return create_page(unwrap_scalars(items), total, params)
    else:
        raw_params = raw_params.as_cursor()
        query, info = paginate_using_cursor(query, raw_params)

        items = wrap_scalars((await db_exec(query)).unique().all())
        items, previous, next_ = paginate_cursor_process_items(items, info, raw_params)

        return create_page(
            unwrap_scalars(items),
            params=params,
            previous=previous,
            next_=next_,
        )


def paginate(
    conn: Union[Connection, Engine, Session],
    query: Select,
    params: Optional[AbstractParams] = None,
) -> AbstractPage[Any]:
    params = verify_params(params, "limit-offset", "cursor")
    return exec_pagination(query, params, conn.execute)


__all__ = [
    "paginate",
    "exec_pagination",
    "async_exec_pagination",
]
