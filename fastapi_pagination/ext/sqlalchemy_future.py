from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional, Union

from sqlalchemy.future import Connection, Engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from ..api import create_page
from ..bases import AbstractPage, AbstractParams, is_cursor
from ..types import AdditionalData
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
    additional_data: AdditionalData = None,
) -> AbstractPage[Any]:
    raw_params = params.to_raw_params()

    if is_cursor(raw_params):
        query, info = paginate_using_cursor(query, raw_params)

        items = wrap_scalars(db_exec(query).unique().all())
        items, previous, next_ = paginate_cursor_process_items(items, info, raw_params)

        return create_page(
            unwrap_scalars(items),
            params=params,
            previous=previous,
            next_=next_,
            **(additional_data or {}),
        )
    else:
        (total,) = db_exec(count_query(query)).scalars()
        query = paginate_query(query, params)
        items = db_exec(query).unique().all()

        return create_page(unwrap_scalars(items), total, params, **(additional_data or {}))


async def async_exec_pagination(
    query: Select,
    params: AbstractParams,
    db_exec: Callable[..., Awaitable[Any]],
    additional_data: AdditionalData = None,
) -> AbstractPage[Any]:  # pragma: no cover
    raw_params = params.to_raw_params()

    if is_cursor(raw_params):
        query, info = paginate_using_cursor(query, raw_params)

        items = wrap_scalars((await db_exec(query)).unique().all())
        items, previous, next_ = paginate_cursor_process_items(items, info, raw_params)

        return create_page(
            unwrap_scalars(items),
            params=params,
            previous=previous,
            next_=next_,
            **(additional_data or {}),
        )
    else:
        (total,) = (await db_exec(count_query(query))).scalars()
        items = (await db_exec(paginate_query(query, params))).unique().all()

        return create_page(unwrap_scalars(items), total, params, **(additional_data or {}))


def paginate(
    conn: Union[Connection, Engine, Session],
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> AbstractPage[Any]:
    params, _ = verify_params(params, "limit-offset", "cursor")
    return exec_pagination(query, params, conn.execute, additional_data)


__all__ = [
    "paginate",
    "exec_pagination",
    "async_exec_pagination",
]
