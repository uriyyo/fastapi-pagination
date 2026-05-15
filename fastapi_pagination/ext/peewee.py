from __future__ import annotations

from fastapi_pagination.ext.utils import generic_query_apply_params

__all__ = [
    "apaginate",
    "create_count_query",
    "create_paginate_query",
    "paginate",
]

from collections.abc import Iterable, Sequence
from functools import partial
from typing import Any, TypeAlias, cast, overload

from peewee import Database, ModelSelect, Query

from fastapi_pagination.bases import AbstractParams, RawParams
from fastapi_pagination.config import Config
from fastapi_pagination.ext.raw_sql import create_count_query_from_text, create_paginate_query_from_text
from fastapi_pagination.flow import flow, run_async_flow, run_sync_flow
from fastapi_pagination.flows import (
    LimitOffsetFlow,
    TotalFlow,
    generic_flow,
)
from fastapi_pagination.types import (
    AdditionalData,
    AsyncItemsTransformer,
    ItemsTransformer,
    SyncItemsTransformer,
)

try:
    from playhouse.pwasyncio import AsyncDatabaseMixin
except ImportError:  # pragma: no cover
    AsyncDatabaseMixin: type | None = None

PEEWEE_ASYNC_AVAILABLE = AsyncDatabaseMixin is not None

RawSQL: TypeAlias = str


def _get_database(query: ModelSelect) -> Database:
    return query.model._meta.database


def _is_async_db(conn: Any) -> bool:
    if AsyncDatabaseMixin is None:
        return False
    return isinstance(conn, AsyncDatabaseMixin)


def _is_raw_sql(query: Any) -> bool:
    return isinstance(query, str)


def _resolve_query_and_db(
    query: Query | RawSQL | None,
    db: Database | None,
) -> tuple[Query | RawSQL, Database | Any]:
    if query is None:
        raise ValueError("Query cannot be None")

    if _is_raw_sql(query):
        if db is None:
            raise ValueError("Database is required for raw SQL queries")
        return query, db

    return query, db if db is not None else _get_database(cast(ModelSelect, query))


def create_paginate_query(query: Query, params: RawParams) -> Query:
    return generic_query_apply_params(query, params)


def create_count_query(query: Query | RawSQL) -> Query | RawSQL:
    if _is_raw_sql(query):
        return create_count_query_from_text(cast(str, query))

    model = getattr(query, "model", None)

    if model is None:
        return query

    from peewee import fn

    query_clone = cast(Query, query)
    if hasattr(query_clone, "limit"):
        query_clone = query_clone.limit(None)
    if hasattr(query_clone, "offset"):
        query_clone = query_clone.offset(None)

    return model.select(fn.COUNT(1)).from_(query_clone)


@flow
def _total_flow(
    query: Query | RawSQL,
    db: Database | Any,
) -> TotalFlow:
    if _is_raw_sql(query):
        count_query = create_count_query(query)
        cursor = yield db.execute_sql(count_query)
        row = cursor.fetchone()
        total = row[0] if row else 0
    elif AsyncDatabaseMixin is not None and isinstance(db, AsyncDatabaseMixin):
        total = yield db.count(query)  # type: ignore[unresolved-attr]
    else:
        count_query = create_count_query(query)
        cursor = yield db.execute(count_query)
        row = cursor.fetchone()
        total = row[0] if row else 0

    return cast(int | None, total)


@flow
def _limit_offset_flow(
    query: Query | RawSQL,
    db: Database | Any,
    raw_params: RawParams,
    *,
    prefetch: tuple[Query, ...] | None = None,
) -> LimitOffsetFlow:
    if _is_raw_sql(query):
        paginated_sql = create_paginate_query_from_text(cast(RawSQL, query), raw_params)
        cursor = yield db.execute_sql(paginated_sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        items = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    else:
        query = create_paginate_query(cast(Query, query), raw_params)
        if _is_async_db(db):
            if prefetch:
                items = yield db.aprefetch(query, *prefetch)  # type: ignore[unresolved-attr]
            else:
                items = yield db.list(query)  # type: ignore[unresolved-attr]
        elif prefetch:
            from peewee import prefetch as peewee_prefetch

            items = yield peewee_prefetch(query, *prefetch)
        else:
            items = yield list(query)

    return items


@flow
def _peewee_flow(
    query: Query | RawSQL,
    db: Database | Any,
    params: AbstractParams | None = None,
    *,
    is_async: bool = False,
    prefetch: tuple[Query, ...] | None = None,
    transformer: ItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    config: Config | None = None,
) -> Any:
    page = yield from generic_flow(
        async_=is_async,
        total_flow=partial(_total_flow, query, db),
        limit_offset_flow=partial(_limit_offset_flow, query, db, prefetch=prefetch),
        params=params,
        inner_transformer=_inner_transformer,
        transformer=transformer,
        additional_data=additional_data,
        config=config,
    )

    return page


def _inner_transformer(
    items: Sequence[Any],
) -> Sequence[Any]:
    if isinstance(items, Iterable):
        items = list(items)

    return items


@overload
def paginate(
    query: Query,
    params: AbstractParams | None = None,
    *,
    db: Database | None = None,
    prefetch: tuple[Query, ...] | None = None,
    transformer: SyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    config: Config | None = None,
) -> Any:
    pass


@overload
def paginate(
    query: RawSQL,
    params: AbstractParams | None = None,
    *,
    db: Database,
    prefetch: tuple[Query, ...] | None = None,
    transformer: SyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    config: Config | None = None,
) -> Any:
    pass


def paginate(
    query: Query | RawSQL | None,
    params: AbstractParams | None = None,
    *,
    db: Database | None = None,
    prefetch: tuple[Query, ...] | None = None,
    transformer: SyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    config: Config | None = None,
) -> Any:
    actual_query, actual_db = _resolve_query_and_db(query, db)

    return run_sync_flow(
        _peewee_flow(
            query=actual_query,
            db=actual_db,
            params=params,
            is_async=False,
            prefetch=prefetch,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        ),
    )


async def apaginate(
    query: Query | RawSQL | None,
    params: AbstractParams | None = None,
    *,
    db: Database | None = None,
    prefetch: tuple[Query, ...] | None = None,
    transformer: AsyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    config: Config | None = None,
) -> Any:
    if not PEEWEE_ASYNC_AVAILABLE:
        raise TypeError(
            "apaginate requires peewee>=4.0.0 with playhouse.pwasyncio and greenlet. "
            "Install with: pip install fastapi-pagination[peewee] "
            "or use sync paginate()."
        )

    actual_query, actual_db = _resolve_query_and_db(query, db)

    return await run_async_flow(
        _peewee_flow(
            query=actual_query,
            db=actual_db,
            params=params,
            is_async=True,
            prefetch=prefetch,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        ),
    )
