from __future__ import annotations

__all__ = [
    "paginate_query",
    "count_query",
    "paginate",
]

import warnings
from typing import Any, Optional, Union, overload, Tuple, TYPE_CHECKING

from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Query, noload, Session
from typing_extensions import TypeAlias

from .utils import generic_query_apply_params, unwrap_scalars
from ..api import create_page
from ..bases import AbstractParams, AbstractPage, is_cursor
from ..types import AdditionalData
from ..utils import verify_params


if TYPE_CHECKING:
    from sqlalchemy.sql import Select
    from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection
    from sqlalchemy.engine import Connection


try:
    from sqlalchemy.util import greenlet_spawn
except ImportError:  # pragma: no cover

    async def greenlet_spawn(*_: Any, **__: Any) -> Any:  # type: ignore
        raise ImportError("greenlet is not installed")


try:
    from sqlakeyset import paging
except ImportError:  # pragma: no cover
    paging = None


AsyncConn: TypeAlias = Union[AsyncSession, AsyncConnection]
SyncConn: TypeAlias = Union[Session, Connection]


def paginate_query(query: Select, params: AbstractParams) -> Select:
    return generic_query_apply_params(query, params.to_raw_params().as_limit_offset())


def count_query(query: Select) -> Select:
    count_subquery = query.order_by(None).options(noload("*")).subquery()
    return select(func.count(literal_column("*"))).select_from(count_subquery)


def _maybe_unique(result: Any, unique: bool) -> Any:
    return (result.unique() if unique else result).all()


def exec_pagination(
    query: Select,
    params: AbstractParams,
    conn: SyncConn,
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
            previous=page.paging.bookmark_previous if page.paging.has_previous else None,
            next_=page.paging.bookmark_next if page.paging.has_next else None,
            **(additional_data or {}),
        )
    else:
        total = conn.scalar(count_query(query))
        query = paginate_query(query, params)
        items = _maybe_unique(conn.execute(query), unique)

        return create_page(unwrap_scalars(items), total, params, **(additional_data or {}))


def _get_sync_conn_from_async(conn: Any) -> SyncConn:  # pragma: no cover
    try:
        return conn.sync_session  # type: ignore
    except AttributeError:
        pass

    try:
        return conn.sync_connection  # type: ignore
    except AttributeError:
        pass

    raise TypeError("conn must be an AsyncConnection or AsyncSession")


# old deprecated paginate function that use sqlalchemy.orm.Query
@overload
def paginate(
    query: Query[Any],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> Any:
    pass


@overload
def paginate(
    conn: SyncConn,
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    pass


@overload
async def paginate(
    conn: AsyncConn,
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    pass


def paginate(*args: Any, **kwargs: Any) -> Any:
    try:
        query, conn, params, additional_data, unique = _old_paginate_sign(*args, **kwargs)
    except TypeError:
        query, conn, params, additional_data, unique = _new_paginate_sign(*args, **kwargs)

    params, _ = verify_params(params, "limit-offset", "cursor")

    try:
        sync_conn = _get_sync_conn_from_async(conn)
        return greenlet_spawn(exec_pagination, query, params, sync_conn, additional_data, unique)
    except TypeError:
        pass

    return exec_pagination(query, params, conn, additional_data, unique)


def _old_paginate_sign(
    query: Query[Any],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> Tuple[Select, SyncConn, Optional[AbstractParams], AdditionalData, bool]:
    if query.session is None:
        raise ValueError("query.session is None")

    warnings.warn(
        "sqlalchemy.orm.Query is deprecated, use sqlalchemy.sql.Select instead",
        DeprecationWarning,
        stacklevel=3,
    )

    return query, query.session, params, additional_data, True  # type: ignore


def _new_paginate_sign(
    conn: SyncConn,
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Tuple[Select, SyncConn, Optional[AbstractParams], AdditionalData, bool]:
    return query, conn, params, additional_data, unique
