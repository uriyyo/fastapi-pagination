from __future__ import annotations

__all__ = [
    "create_paginate_query_from_text",
    "create_count_query_from_text",
    "create_paginate_query",
    "create_count_query",
    "paginate_query",
    "paginate",
    "Selectable",
]

import warnings
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Optional, Tuple, Union, overload

from sqlalchemy import func, select, text
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Query, Session, noload, scoped_session
from sqlalchemy.sql.elements import TextClause
from typing_extensions import TypeAlias, deprecated

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
    from sqlalchemy.ext.asyncio import async_scoped_session
except ImportError:  # pragma: no cover

    class async_scoped_session:  # type: ignore
        def __init__(self, *_: Any, **__: Any) -> None:
            raise ImportError("sqlalchemy.ext.asyncio is not available")


try:
    from sqlakeyset import paging
except ImportError:  # pragma: no cover
    paging = None  # type: ignore[assignment]


AsyncConn: TypeAlias = "Union[AsyncSession, AsyncConnection, async_scoped_session]"
SyncConn: TypeAlias = "Union[Session, Connection, scoped_session]"

Selectable: TypeAlias = "Union[Select, TextClause]"


def create_paginate_query_from_text(query: str, params: AbstractParams) -> str:
    raw_params = params.to_raw_params().as_limit_offset()

    suffix = ""
    if raw_params.limit is not None:
        suffix += f" LIMIT {raw_params.limit}"
    if raw_params.offset is not None:
        suffix += f" OFFSET {raw_params.offset}"

    return f"{query} {suffix}".strip()


def create_count_query_from_text(query: str) -> str:
    return f"SELECT count(*) FROM ({query}) AS __count_query__"  # noqa: S608


@deprecated(
    "fastapi_pagination.ext.sqlalchemy.paginate_query function is deprecated, "
    "please use fastapi_pagination.ext.sqlalchemy.create_paginate_query function instead"
    "This function will be removed in the next major release (0.13.0).",
)
def paginate_query(query: Select, params: AbstractParams) -> Select:
    return create_paginate_query(query, params)  # type: ignore[return-value]


def create_paginate_query(query: Selectable, params: AbstractParams) -> Selectable:
    if isinstance(query, TextClause):
        return text(create_paginate_query_from_text(query.text, params))

    return generic_query_apply_params(query, params.to_raw_params().as_limit_offset())


def create_count_query(query: Selectable, *, use_subquery: bool = True) -> Selectable:
    if isinstance(query, TextClause):
        return text(create_count_query_from_text(query.text))

    query = query.order_by(None).options(noload("*"))

    if use_subquery:
        return select(func.count()).select_from(query.subquery())

    return query.with_only_columns(  # type: ignore[call-arg] # noqa: PIE804
        func.count(),
        maintain_column_froms=True,
    )


class NonHashableRowsException(Exception):
    pass


def _maybe_unique(result: Any, unique: bool) -> Any:
    try:
        return (result.unique() if unique else result).all()
    except InvalidRequestError as e:  # pragma: no cover
        if "non-hashable" in str(e):
            raise NonHashableRowsException("The rows are not hashable, please use `unique=False`") from e

        raise


def exec_pagination(
    query: Selectable,
    count_query: Optional[Selectable],
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

    total = None
    if raw_params.include_total:
        count_query = count_query or create_count_query(query, use_subquery=subquery_count)
        total = conn.scalar(count_query)

    if is_cursor(raw_params):
        if paging is None:
            raise ImportError("sqlakeyset is not installed")
        if not getattr(query, "_order_by_clauses", True):
            raise ValueError("Cursor pagination requires ordering")

        page = paging.select_page(  # type: ignore
            conn,  # type: ignore[arg-type]
            selectable=query,  # type: ignore[arg-type]
            per_page=raw_params.size,
            page=raw_params.cursor,  # type: ignore[arg-type]
        )
        items = unwrap_scalars([*page])
        items = _apply_items_transformer(items, transformer)

        return create_page(
            items,
            params=params,
            current=page.paging.bookmark_current,
            current_backwards=page.paging.bookmark_current_backwards,
            previous=page.paging.bookmark_previous if page.paging.has_previous else None,
            next_=page.paging.bookmark_next if page.paging.has_next else None,
            total=total,
            **(additional_data or {}),
        )

    query = create_paginate_query(query, params)
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
    if isinstance(conn, async_scoped_session):
        conn = conn()

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
    query: Selectable,
    params: Optional[AbstractParams] = None,
    *,
    count_query: Optional[Selectable] = None,
    subquery_count: bool = True,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    pass


@overload
async def paginate(
    conn: AsyncConn,
    query: Selectable,
    params: Optional[AbstractParams] = None,
    *,
    count_query: Optional[Selectable] = None,
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
        query, count_query, conn, params, transformer, additional_data, unique, subquery_count = _old_paginate_sign(
            *args, **kwargs
        )
    except (TypeError, AssertionError):
        query, count_query, conn, params, transformer, additional_data, unique, subquery_count = _new_paginate_sign(
            *args, **kwargs
        )

    params, raw_params = verify_params(params, "limit-offset", "cursor")

    if isinstance(query, TextClause) and is_cursor(raw_params):
        raise ValueError("Cursor pagination cannot be used with raw SQL queries")

    with suppress(TypeError):
        sync_conn = _get_sync_conn_from_async(conn)
        return greenlet_spawn(
            exec_pagination,
            query,
            count_query,
            params,
            sync_conn,
            transformer,
            additional_data,
            subquery_count,
            unique,
            async_=True,
        )

    return exec_pagination(
        query,
        count_query,
        params,
        conn,
        transformer,
        additional_data,
        subquery_count,
        unique,
        async_=False,
    )


def _old_paginate_sign(
    query: Query[Any],
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Tuple[
    Select,
    Optional[Selectable],
    SyncConn,
    Optional[AbstractParams],
    Optional[ItemsTransformer],
    AdditionalData,
    bool,
    bool,
]:
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

    return query, None, session, params, transformer, additional_data, unique, subquery_count  # type: ignore


def _new_paginate_sign(
    conn: SyncConn,
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    count_query: Optional[Selectable] = None,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Tuple[
    Select,
    Optional[Selectable],
    SyncConn,
    Optional[AbstractParams],
    Optional[ItemsTransformer],
    AdditionalData,
    bool,
    bool,
]:
    return query, count_query, conn, params, transformer, additional_data, unique, subquery_count
