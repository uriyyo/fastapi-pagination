from __future__ import annotations

__all__ = [
    "apaginate",
    "create_count_query",
    "create_paginate_query",
    "paginate",
]

from collections.abc import Sequence
from functools import partial
from typing import TYPE_CHECKING, Any, Literal, TypeAlias, TypeVar, cast, overload

from peewee import Database, Model, Query, Select

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

from .utils import unwrap_scalars

if TYPE_CHECKING:
    from playhouse.pwasyncio import AsyncDatabaseMixin

try:
    from playhouse.pwasyncio import AsyncDatabaseMixin
except ImportError:  # pragma: no cover
    AsyncDatabaseMixin: type | None = None

PEEWEE_ASYNC_AVAILABLE = AsyncDatabaseMixin is not None

UnwrapMode: TypeAlias = Literal[
    "auto",
    "legacy",
    "no-unwrap",
    "unwrap",
]

_TSeq = TypeVar("_TSeq", bound=Sequence[Any])


def _get_database(query: Query) -> Database:
    """Extract database from query."""
    if hasattr(query, "database"):
        db = query.database
        if db is not None:
            return db  # type: ignore[return-value]
    raise ValueError("Query has no associated database")


def _is_async_db(conn: Any) -> bool:
    """Check if database is async (AsyncDatabaseMixin)."""
    if AsyncDatabaseMixin is None:
        return False
    return isinstance(conn, AsyncDatabaseMixin)


def _get_db_from_conn(conn: Database | Any) -> Database:
    """Extract database from connection or transaction."""
    if hasattr(conn, "db") and isinstance(conn.db, Database):
        return conn.db  # type: ignore[return-value]
    return conn  # type: ignore[return-value]


def _prepare_query(query: Query | None) -> Query | None:
    """Prepare a Peewee query for execution."""
    if query is None:
        return None
    if isinstance(query, type) and issubclass(query, Model):
        return query.select()
    return query


def _should_unwrap_scalars(query: Query) -> bool:
    """Determine if query results need unwrapping."""
    if not isinstance(query, Select):
        return False

    select_expr = getattr(query, "_select", None)
    if select_expr is None:
        return False

    models = getattr(select_expr, "_models", None)
    if models is None:
        return False

    return len(models) == 1


def _unwrap_items(
    items: _TSeq,
    query: Query | None = None,
    unwrap_mode: UnwrapMode | None = None,
) -> _TSeq:
    """Unwrap query results based on unwrap mode."""
    # For raw queries we will use legacy mode by default
    # because we can't determine if we should unwrap or not
    if unwrap_mode == "legacy":
        items = unwrap_scalars(items)  # type: ignore[assignment]
    elif unwrap_mode == "no-unwrap":
        pass
    elif unwrap_mode == "unwrap":
        items = unwrap_scalars(items, force_unwrap=True)  # type: ignore[assignment]
    elif unwrap_mode == "auto" and query is not None and _should_unwrap_scalars(query):
        items = unwrap_scalars(items, force_unwrap=True)  # type: ignore[assignment]

    return items


def create_paginate_query(query: Query, params: RawParams) -> Query:
    """Apply pagination parameters to a Peewee query."""
    if params.limit is not None:
        query = query.limit(params.limit)
    if params.offset is not None:
        query = query.offset(params.offset)
    return query


def create_count_query(query: Query, *, use_subquery: bool = True) -> Query:
    """Create a COUNT query from a Peewee query."""
    # Clone query to avoid modifying original
    count_query = query.clone()

    # Remove limit/offset for accurate count
    count_query = count_query.limit(None).offset(None)

    from peewee import fn

    if use_subquery:
        return count_query.model.select(fn.COUNT(1)).from_(count_query)  # type: ignore[union-attr]

    return count_query.model.select(fn.COUNT(1))  # type: ignore[union-attr]


@flow
def _total_flow(
    query: Query,
    conn: Database | Any,
    count_query: Query | None,
    subquery_count: bool,
) -> TotalFlow:
    """Get total count for pagination."""
    if count_query is None:
        count_query = create_count_query(query, use_subquery=subquery_count)

    db = _get_db_from_conn(conn)

    if _is_async_db(db):
        total = yield db.count(count_query)  # type: ignore[union-attr]
    else:
        # Execute count query on database and extract count from cursor
        cursor = yield db.execute(count_query)
        row = cursor.fetchone()
        total = row[0] if row else 0

    return cast(int | None, total)


@flow
def _limit_offset_flow(
    query: Query,
    conn: Database | Any,
    raw_params: RawParams,
    *,
    prefetch: tuple[Query, ...] | None = None,
) -> LimitOffsetFlow:
    """Execute paginated query with limit/offset."""
    query = create_paginate_query(query, raw_params)

    db = _get_db_from_conn(conn)

    if _is_async_db(db):
        if prefetch:
            items = yield db.aprefetch(query, *prefetch)  # type: ignore[union-attr]
        else:
            items = yield db.list(query)  # type: ignore[union-attr]
    elif prefetch:
        from peewee import prefetch as peewee_prefetch

        items = yield peewee_prefetch(query, *prefetch)
    else:
        items = yield list(query)

    return items


@flow
def _peewee_flow(
    conn: Database | Any,
    query: Query,
    params: AbstractParams | None = None,
    *,
    is_async: bool = False,
    subquery_count: bool = True,
    unwrap_mode: UnwrapMode | None = None,
    count_query: Query | None = None,
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
        total_flow=partial(_total_flow, query, conn, count_query, subquery_count),
        limit_offset_flow=partial(_limit_offset_flow, query, conn, prefetch=prefetch),
        params=params,
        inner_transformer=partial(_inner_transformer, query=query, unwrap_mode=unwrap_mode, unique=unique),
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
    unwrap_mode: UnwrapMode | None,
    unique: bool,
) -> Sequence[Any]:
    """Apply transformations to query results."""
    # Ensure items are actual data, not query objects
    # Convert ModelSelect to list if needed
    if hasattr(items, "__iter__") and not isinstance(items, (list, tuple)):
        items = list(items)

    if unique:
        # Preserve order while removing duplicates
        # Use id() to avoid issues with Model __eq__ implementations
        seen = {}
        unique_items = []
        for item in items:
            item_id = id(item)
            if item_id not in seen:
                seen[item_id] = item
                unique_items.append(item)
        items = unique_items

    return _unwrap_items(items, query, unwrap_mode)


# Sync paginate function
@overload
def paginate(
    query: Query,
    params: AbstractParams | None = None,
    *,
    db: Database | None = None,
    subquery_count: bool = True,
    unwrap_mode: UnwrapMode | None = None,
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
    query: Query,
    params: AbstractParams | None = None,
    *,
    subquery_count: bool = True,
    unwrap_mode: UnwrapMode | None = None,
    prefetch: tuple[Query, ...] | None = None,
    transformer: SyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    pass


def paginate(
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Paginate a Peewee query.

    Args:
        query: Peewee query object
        params: Pagination parameters
        db: Database instance (optional if query has database attached)
        subquery_count: Use subquery for count
        unwrap_mode: How to unwrap results
        transformer: Optional transformer for results
        additional_data: Additional data to include in page
        unique: Return unique results only
        config: Pagination configuration

    Returns:
        Paginated results
    """
    if len(args) >= 2:
        db, query = args[:2]
        params = kwargs.get("params") or (args[2] if len(args) > 2 else None)
    elif len(args) == 1:
        query = args[0]
        db = kwargs.get("db")
        params = kwargs.get("params")
    else:
        raise ValueError("paginate requires at least a query or (db, query) pair")

    # Get database from query if not provided
    if db is None:
        db = _get_database(query)

    # Prepare query to handle Model classes
    query = _prepare_query(query)  # type: ignore[assignment]

    if query is None:
        raise ValueError("Query cannot be None")

    return run_sync_flow(
        _peewee_flow(
            conn=db,
            query=query,
            params=params,
            is_async=False,
            subquery_count=kwargs.get("subquery_count", True),
            unwrap_mode=kwargs.get("unwrap_mode"),
            count_query=kwargs.get("count_query"),
            prefetch=kwargs.get("prefetch"),
            transformer=kwargs.get("transformer"),
            additional_data=kwargs.get("additional_data"),
            unique=kwargs.get("unique", True),
            config=kwargs.get("config"),
        ),
    )


async def apaginate(
    db: Any,
    query: Query,
    params: AbstractParams | None = None,
    *,
    count_query: Query | None = None,
    subquery_count: bool = True,
    unwrap_mode: UnwrapMode | None = None,
    prefetch: tuple[Query, ...] | None = None,
    transformer: AsyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    """Async paginate a Peewee query using Peewee v4 async support.

    Args:
        db: Async database instance (AsyncSqliteDatabase, AsyncPostgresqlDatabase, etc.)
        query: Peewee query object
        params: Pagination parameters
        count_query: Custom count query
        subquery_count: Use subquery for count
        unwrap_mode: How to unwrap results
        transformer: Optional transformer for results
        additional_data: Additional data to include in page
        unique: Return unique results only
        config: Pagination configuration

    Returns:
        Paginated results

    Example:
        ```python
        async def get_users(db: AsyncPostgresqlDatabase, page: int, page_size: int):
            query = User.select().order_by(User.id)
            return await apaginate(
                db,
                query,
                params=PageParams(page, page_size),
            )
        ```
    """
    if not PEEWEE_ASYNC_AVAILABLE:
        raise TypeError(
            "apaginate requires peewee>=4.0.0 with playhouse.pwasyncio and greenlet. "
            "Install with: pip install fastapi-pagination[peewee] "
            "or use sync paginate()."
        )

    query = _prepare_query(query)  # type: ignore[assignment]

    if query is None:
        raise ValueError("Query cannot be None")

    return await run_async_flow(
        _peewee_flow(
            conn=db,
            query=query,
            params=params,
            is_async=True,
            subquery_count=subquery_count,
            unwrap_mode=unwrap_mode,
            count_query=count_query,
            prefetch=prefetch,
            transformer=transformer,
            additional_data=additional_data,
            unique=unique,
            config=config,
        ),
    )
