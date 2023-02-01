from __future__ import annotations

__all__ = [
    "paginate",
    "exec_pagination",
    "async_exec_pagination",
]

from typing import Any, Awaitable, Callable, Optional, Union

from sqlalchemy.future import Connection, Engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from .sqlalchemy import (
    count_query,
    paginate_cursor_process_items,
    paginate_query,
    paginate_using_cursor,
)
from .utils import unwrap_scalars, wrap_scalars
from ..api import create_page
from ..bases import AbstractPage, AbstractParams, is_cursor
from ..types import AdditionalData
from ..utils import verify_params


def _maybe_unique(result: Any, unique: bool) -> Any:
    return (result.unique() if unique else result).all()


def exec_pagination(
    query: Select,
    params: AbstractParams,
    db_exec: Callable[..., Any],
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> AbstractPage[Any]:
    raw_params = params.to_raw_params()

    if is_cursor(raw_params):
        query, info = paginate_using_cursor(query, raw_params)

        items = wrap_scalars(_maybe_unique(db_exec(query), unique))
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
        items = _maybe_unique(db_exec(query), unique)

        return create_page(unwrap_scalars(items), total, params, **(additional_data or {}))


async def async_exec_pagination(
    query: Select,
    params: AbstractParams,
    db_exec: Callable[..., Awaitable[Any]],
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> AbstractPage[Any]:  # pragma: no cover
    raw_params = params.to_raw_params()

    if is_cursor(raw_params):
        query, info = paginate_using_cursor(query, raw_params)

        items = wrap_scalars(_maybe_unique(await db_exec(query), unique))
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
        items = _maybe_unique(await db_exec(paginate_query(query, params)), unique)

        return create_page(unwrap_scalars(items), total, params, **(additional_data or {}))


def paginate(
    conn: Union[Connection, Engine, Session],
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    params, _ = verify_params(params, "limit-offset", "cursor")
    return exec_pagination(query, params, conn.execute, additional_data, unique)
