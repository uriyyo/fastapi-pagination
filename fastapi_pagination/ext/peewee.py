from __future__ import annotations

__all__ = [
    "apaginate",
    "create_count_query",
    "create_paginate_query",
    "paginate",
]

from collections.abc import Sequence
from functools import partial
from typing import TYPE_CHECKING, Any, TypeAlias, cast, overload

from peewee import Database, Model, Query

from fastapi_pagination.api import create_page
from fastapi_pagination.bases import AbstractParams, RawParams
from fastapi_pagination.config import Config
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

if TYPE_CHECKING:
    from playhouse.pwasyncio import AsyncDatabaseMixin

try:
    from playhouse.pwasyncio import AsyncDatabaseMixin
except ImportError:  # pragma: no cover
    AsyncDatabaseMixin: type | None = None

PEEWEE_ASYNC_AVAILABLE = AsyncDatabaseMixin is not None

RawSQL: TypeAlias = str


@overload
def paginate(
    query: Query | type[Model] | None,
    params: AbstractParams | None = None,
    *,
    subquery_count: bool = True,
    prefetch: tuple[Query, ...] | None = None,
    transformer: SyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    pass


@overload
def paginate(
    db: Database,
    query: RawSQL,
    params: AbstractParams | None = None,
    *,
    subquery_count: bool = True,
    prefetch: tuple[Query, ...] | None = None,
    transformer: SyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    pass


def _get_database(query: Query) -> Database:
    """Extract database from query."""
    return query.model._meta.database


def _is_async_db(conn: Any) -> bool:
    """Check if database is async (AsyncDatabaseMixin)."""
    if AsyncDatabaseMixin is None:
        return False
    return isinstance(conn, AsyncDatabaseMixin)


def _prepare_query(query: Query | None) -> Query | None:
    """Prepare a Peewee query for execution."""
    if query is None:
        return None
    if isinstance(query, type) and issubclass(query, Model):
        return query.select()
    return query


def _is_raw_sql(query: Any) -> bool:
    """Check if query is a raw SQL string."""
    return isinstance(query, str)


def create_paginate_query(query: Query, params: RawParams) -> Query:
    """Apply pagination parameters to a Peewee query."""
    if params.limit is not None:
        query = query.limit(params.limit)
    if params.offset is not None:
        query = query.offset(params.offset)
    return query


def create_count_query(query: Query | RawSQL, *, use_subquery: bool = True) -> Query | RawSQL:
    """Create a COUNT query from a Peewee query or raw SQL."""
    if _is_raw_sql(query):
        return f"SELECT count(*) FROM ({query}) AS __count_query__"  # noqa: S608

    count_query = query.clone()

    if hasattr(query, "model") and query.model is not None:
        from peewee import fn

        if hasattr(count_query, "limit"):
            count_query = count_query.limit(None)
        if hasattr(count_query, "offset"):
            count_query = count_query.offset(None)

        if use_subquery:
            return query.model.select(fn.COUNT(1)).from_(count_query)  # type: ignore[union-attr]

        return query.model.select(fn.COUNT(1))  # type: ignore[union-attr]

    return count_query


def _create_raw_sql_query(sql: str, params: RawParams) -> str:
    """Create paginated raw SQL query."""
    suffix = ""
    if params.limit is not None:
        suffix += f" LIMIT {params.limit}"
    if params.offset is not None:
        suffix += f" OFFSET {params.offset}"
    return f"{sql} {suffix}".strip()


@flow
def _total_flow(
    query: Query | RawSQL,
    db: Database | Any,
    count_query: Query | RawSQL | None,
    subquery_count: bool,
) -> TotalFlow:
    """Get total count for pagination."""
    if count_query is None:
        count_query = create_count_query(query, use_subquery=subquery_count)

    if _is_raw_sql(count_query):
        cursor = yield db.execute_sql(count_query)
        row = cursor.fetchone()
        total = row[0] if row else 0
    elif _is_async_db(db):
        total = yield db.count(count_query)  # type: ignore[union-attr]
    else:
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
    """Execute paginated query with limit/offset."""
    if _is_raw_sql(query):
        paginated_sql = _create_raw_sql_query(query, raw_params)
        cursor = yield db.execute_sql(paginated_sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        items = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    elif _is_async_db(db):
        query = create_paginate_query(query, raw_params)
        if prefetch:
            items = yield db.aprefetch(query, *prefetch)  # type: ignore[union-attr]
        else:
            items = yield db.list(query)  # type: ignore[union-attr]
    elif prefetch:
        from peewee import prefetch as peewee_prefetch

        query = create_paginate_query(query, raw_params)
        items = yield peewee_prefetch(query, *prefetch)
    else:
        query = create_paginate_query(query, raw_params)
        items = yield list(query)

    return items


@flow
def _peewee_flow(
    query: Query | RawSQL,
    db: Database | Any,
    params: AbstractParams | None = None,
    *,
    is_async: bool = False,
    subquery_count: bool = True,
    count_query: Query | RawSQL | None = None,
    prefetch: tuple[Query, ...] | None = None,
    transformer: ItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    """Main flow function for Peewee pagination."""
    create_page_factory = partial(create_page)

    page = yield from generic_flow(
        async_=is_async,
        total_flow=partial(_total_flow, query, db, count_query, subquery_count),
        limit_offset_flow=partial(_limit_offset_flow, query, db, prefetch=prefetch),
        params=params,
        inner_transformer=partial(_inner_transformer, query=query, unique=unique),
        transformer=transformer,
        additional_data=additional_data,
        config=config,
        create_page_factory=create_page_factory,
    )

    return page


def _inner_transformer(
    items: Sequence[Any],
    /,
    query: Query | None,
    unique: bool,
) -> Sequence[Any]:
    """Apply transformations to query results."""
    if hasattr(items, "__iter__") and not isinstance(items, (list, tuple)):
        items = list(items)

    if unique:
        seen = {}
        unique_items = []
        for item in items:
            item_id = id(item)
            if item_id not in seen:
                seen[item_id] = item
                unique_items.append(item)
        items = unique_items

    return items


def paginate(
    query: Query | type[Model] | RawSQL | None,
    params: AbstractParams | None = None,
    *,
    db: Database | None = None,
    subquery_count: bool = True,
    prefetch: tuple[Query, ...] | None = None,
    transformer: SyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    """Paginate a Peewee query or raw SQL.

    Args:
        query: Peewee query object, Model class, or raw SQL string
        params: Pagination parameters
        db: Database instance (required for raw SQL, optional otherwise - will be
            extracted from the query's model if not provided)
        subquery_count: Use subquery for count
        transformer: Optional transformer for results
        additional_data: Additional data to include in page
        unique: Return unique results only
        config: Pagination configuration

    Returns:
        Paginated results

    Example:
        # Regular query - db is extracted from query
        paginate(User.select(), params=PageParams(page=1, size=10))

        # Raw SQL query - db must be provided
        paginate("SELECT * FROM users WHERE age > 18", params=PageParams(page=1, size=10), db=db)
    """
    if query is None:
        raise ValueError("Query cannot be None")

    actual_query: Query | type[Model] | RawSQL | None
    actual_db: Database | Any

    if _is_raw_sql(query):
        if db is None:
            raise ValueError("Database is required for raw SQL queries")
        actual_query = query
        actual_db = db
    else:
        actual_query = _prepare_query(query)
        if actual_query is None:
            raise ValueError("Query cannot be None")
        actual_db = db if db is not None else _get_database(actual_query)

    return run_sync_flow(
        _peewee_flow(
            query=actual_query,
            db=actual_db,
            params=params,
            is_async=False,
            subquery_count=subquery_count,
            count_query=None,
            prefetch=prefetch,
            transformer=transformer,
            additional_data=additional_data,
            unique=unique,
            config=config,
        ),
    )


async def apaginate(
    query: Query | type[Model] | RawSQL | None,
    params: AbstractParams | None = None,
    *,
    db: Database | None = None,
    count_query: Query | RawSQL | None = None,
    subquery_count: bool = True,
    prefetch: tuple[Query, ...] | None = None,
    transformer: AsyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    """Async paginate a Peewee query or raw SQL using Peewee v4 async support.

    Args:
        query: Peewee query object, Model class, or raw SQL string
        params: Pagination parameters
        db: Database instance (required for raw SQL, optional otherwise - will be
            extracted from the query's model if not provided)
        count_query: Custom count query
        subquery_count: Use subquery for count
        transformer: Optional transformer for results
        additional_data: Additional data to include in page
        unique: Return unique results only
        config: Pagination configuration

    Returns:
        Paginated results

    Example:
        ```python
        async def get_users(page: int, page_size: int):
            return await apaginate(User.select(), params=PageParams(page, page_size))

        # Raw SQL
        async def get_active_users(page: int, page_size: int):
            return await apaginate("SELECT * FROM users WHERE active = 1",
                                  params=PageParams(page, page_size), db=db)
        ```
    """
    if not PEEWEE_ASYNC_AVAILABLE:
        raise TypeError(
            "apaginate requires peewee>=4.0.0 with playhouse.pwasyncio and greenlet. "
            "Install with: pip install fastapi-pagination[peewee] "
            "or use sync paginate()."
        )

    if query is None:
        raise ValueError("Query cannot be None")

    actual_query: Query | type[Model] | RawSQL | None
    actual_db: Database | Any

    if _is_raw_sql(query):
        if db is None:
            raise ValueError("Database is required for raw SQL queries")
        actual_query = query
        actual_db = db
    else:
        actual_query = _prepare_query(query)
        if actual_query is None:
            raise ValueError("Query cannot be None")
        actual_db = db if db is not None else _get_database(actual_query)

    return await run_async_flow(
        _peewee_flow(
            query=actual_query,
            db=actual_db,
            params=params,
            is_async=True,
            subquery_count=subquery_count,
            count_query=count_query,
            prefetch=prefetch,
            transformer=transformer,
            additional_data=additional_data,
            unique=unique,
            config=config,
        ),
    )
