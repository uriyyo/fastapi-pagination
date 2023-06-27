from __future__ import annotations

__all__ = [
    "paginate_query",
    "count_query",
    "paginate",
]

import warnings
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Optional, Tuple, Union, overload

from sqlalchemy import func, select
from sqlalchemy.orm import Query, Session, noload
from typing_extensions import TypeAlias

from ..api import apply_items_transformer, create_page
from ..bases import AbstractPage, AbstractParams, is_cursor
from ..types import AdditionalData, AsyncItemsTransformer, ItemsTransformer, SyncItemsTransformer
from ..utils import verify_params
from .utils import generic_query_apply_params, unwrap_scalars

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection
    from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
    from sqlalchemy.sql import Select


try:
    from sqlalchemy.util import await_only, greenlet_spawn
except ImportError:  # pragma: no cover

    async def greenlet_spawn(*_: Any, **__: Any) -> Any:  # type: ignore
        raise ImportError("sqlalchemy.util.greenlet_spawn is not available")

    def await_only(*_: Any, **__: Any) -> Any:  # type: ignore
        raise ImportError("sqlalchemy.util.await_only is not available")


try:
    from sqlakeyset import paging
except ImportError:  # pragma: no cover
    paging = None


AsyncConn: TypeAlias = "Union[AsyncSession, AsyncConnection]"
SyncConn: TypeAlias = "Union[Session, Connection]"


def paginate_query(query: Select, params: AbstractParams) -> Select:
    return generic_query_apply_params(query, params.to_raw_params().as_limit_offset())


def count_query(query: Select, *, use_subquery: bool = True) -> Select:
    query = query.order_by(None).options(noload("*"))

    if use_subquery:
        return select(func.count()).select_from(query.subquery())

    return query.with_only_columns(  # noqa: PIE804
        func.count(),
        **{"maintain_column_froms": True},
    )


def _maybe_unique(result: Any, unique: bool) -> Any:
    return (result.unique() if unique else result).all()


def exec_pagination(
    query: Select,
    params: AbstractParams,
    conn: SyncConn,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    subquery_count: bool = True,
    unique: bool = True,
    async_: bool = False,
) -> AbstractPage[Any]:
    raw_params = params.to_raw_params()

    if async_:

        def _apply_items_transformer(*args: Any, **kwargs: Any) -> Any:
            return await_only(apply_items_transformer(*args, **kwargs, async_=True))

    else:
        _apply_items_transformer = apply_items_transformer

    if is_cursor(raw_params):
        if paging is None:
            raise ImportError("sqlakeyset is not installed")
        if not getattr(query, "_order_by_clauses", True):
            raise ValueError("Cursor pagination requires ordering")

        page = paging.select_page(
            conn,
            selectable=query,
            per_page=raw_params.size,
            page=raw_params.cursor,
        )
        items = unwrap_scalars([*page])
        items = _apply_items_transformer(items, transformer)

        return create_page(
            items,
            params=params,
            previous=page.paging.bookmark_previous if page.paging.has_previous else None,
            next_=page.paging.bookmark_next if page.paging.has_next else None,
            **(additional_data or {}),
        )

    total = conn.scalar(count_query(query, use_subquery=subquery_count))
    query = paginate_query(query, params)
    items = _maybe_unique(conn.execute(query), unique)
    items = unwrap_scalars(items)
    items = _apply_items_transformer(items, transformer)

    return create_page(
        items,
        total=total,
        params=params,
        **(additional_data or {}),
    )


def _get_sync_conn_from_async(conn: Any) -> SyncConn:  # pragma: no cover
    with suppress(AttributeError):
        return conn.sync_session  # type: ignore

    with suppress(AttributeError):
        return conn.sync_connection  # type: ignore

    raise TypeError("conn must be an AsyncConnection or AsyncSession")


# old deprecated paginate function that use sqlalchemy.orm.Query
@overload
def paginate(
    query: Query[Any],
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    pass


@overload
def paginate(
    conn: SyncConn,
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    pass


@overload
async def paginate(
    conn: AsyncConn,
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    pass


def paginate(*args: Any, **kwargs: Any) -> Any:
    try:
        assert args
        assert isinstance(args[0], Query)
        query, conn, params, transformer, additional_data, unique, subquery_count = _old_paginate_sign(*args, **kwargs)
    except (TypeError, AssertionError):
        query, conn, params, transformer, additional_data, unique, subquery_count = _new_paginate_sign(*args, **kwargs)

    params, _ = verify_params(params, "limit-offset", "cursor")

    with suppress(TypeError):
        sync_conn = _get_sync_conn_from_async(conn)
        return greenlet_spawn(
            exec_pagination,
            query,
            params,
            sync_conn,
            transformer,
            additional_data,
            subquery_count,
            unique,
            async_=True,
        )

    return exec_pagination(query, params, conn, transformer, additional_data, subquery_count, unique, async_=False)


def _old_paginate_sign(
    query: Query[Any],
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Tuple[Select, SyncConn, Optional[AbstractParams], Optional[ItemsTransformer], AdditionalData, bool, bool]:
    if query.session is None:
        raise ValueError("query.session is None")

    warnings.warn(
        "sqlalchemy.orm.Query is deprecated, use sqlalchemy.sql.Select instead "
        "sqlalchemy.orm.Query support will be removed in the next major release (0.13.0).",
        DeprecationWarning,
        stacklevel=3,
    )

    session = query.session

    with suppress(AttributeError):
        query = query._statement_20()  # type: ignore[attr-defined]

    return query, session, params, transformer, additional_data, unique, subquery_count  # type: ignore


def _new_paginate_sign(
    conn: SyncConn,
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Tuple[Select, SyncConn, Optional[AbstractParams], Optional[ItemsTransformer], AdditionalData, bool, bool]:
    return query, conn, params, transformer, additional_data, unique, subquery_count
