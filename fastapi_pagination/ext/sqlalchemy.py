from __future__ import annotations

__all__ = [
    "Selectable",
    "apaginate",
    "create_count_query",
    "create_count_query_from_text",
    "create_paginate_query",
    "create_paginate_query_from_text",
    "paginate",
]

import warnings
from collections.abc import Sequence
from contextlib import suppress
from functools import partial
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeAlias, TypeVar, cast, overload

from sqlalchemy import func, select, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Query, Session, aliased, noload, scoped_session
from sqlalchemy.sql import CompoundSelect, Select
from sqlalchemy.sql.elements import ColumnElement, TextClause
from sqlalchemy.sql.util import ColumnAdapter
from typing_extensions import TypeVarTuple, Unpack, deprecated

from fastapi_pagination.api import create_page
from fastapi_pagination.bases import AbstractParams, CursorRawParams, RawParams
from fastapi_pagination.config import Config
from fastapi_pagination.flow import flow, run_async_flow, run_sync_flow
from fastapi_pagination.flows import (
    CursorFlow,
    LimitOffsetFlow,
    TotalFlow,
    additional_data_flow,
    create_page_flow,
    generic_flow,
)
from fastapi_pagination.types import (
    AdditionalData,
    AsyncItemsTransformer,
    ItemsTransformer,
    SyncAdditionalData,
    SyncItemsTransformer,
)
from fastapi_pagination.utils import verify_params

from .raw_sql import create_count_query_from_text as _create_count_query_from_text
from .raw_sql import create_paginate_query_from_text as _create_paginate_query_from_text
from .utils import generic_query_apply_params, unwrap_scalars

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

if TYPE_CHECKING:
    from sqlalchemy.orm import FromStatement
else:
    try:
        from sqlalchemy.orm import FromStatement
    except ImportError:  # pragma: no cover
        _Ts = TypeVarTuple("_Ts")

        class FromStatement(Generic[Unpack[_Ts]]):
            element: Any

            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ImportError("sqlalchemy.orm.FromStatement is not available")


try:
    from sqlalchemy.util import await_only, greenlet_spawn
except ImportError:  # pragma: no cover

    async def greenlet_spawn(*_: Any, **__: Any) -> Any:
        raise ImportError("sqlalchemy.util.greenlet_spawn is not available")

    def await_only(*_: Any, **__: Any) -> Any:
        raise ImportError("sqlalchemy.util.await_only is not available")


try:
    from sqlalchemy.ext.asyncio import async_scoped_session
except ImportError:  # pragma: no cover

    class async_scoped_session:  # noqa: N801
        def __init__(self, *_: Any, **__: Any) -> None:
            raise ImportError("sqlalchemy.ext.asyncio is not available")


try:
    from sqlakeyset import asyncio as apaging
    from sqlakeyset import paging
except ImportError:  # pragma: no cover
    paging = None  # type: ignore[ty:invalid-assignment]
    apaging = None  # type: ignore[ty:invalid-assignment]


_INLINE_COUNT_LABEL = "__pagination_inline_count__"

AsyncConn: TypeAlias = "AsyncSession | AsyncConnection | async_scoped_session[Any]"
SyncConn: TypeAlias = "Session | Connection | scoped_session[Any]"
AnyConn: TypeAlias = "AsyncConn | SyncConn"

UnwrapMode: TypeAlias = Literal[
    "auto",  # default, unwrap only if select is select(model)
    "legacy",  # legacy mode, unwrap only when there is one column in select
    "no-unwrap",  # never unwrap
    "unwrap",  # always unwrap
]

Selectable: TypeAlias = (
    "Select[tuple[Any, ...]] | TextClause | FromStatement[tuple[Any, ...]] | CompoundSelect[tuple[Any, ...]]"
)
SelectableOrQuery: TypeAlias = "Selectable | Query[Any]"


@overload
def _prepare_query(query: None) -> None:
    pass


@overload
def _prepare_query(query: SelectableOrQuery) -> Selectable:
    pass


def _prepare_query(query: SelectableOrQuery | None) -> Selectable | None:
    if query is None:
        return None

    with suppress(AttributeError):
        query = query._statement_20()  # type: ignore[ty:unresolved-attribute]

    return cast("Selectable", query)


def _prepare_query_for_cursor(query: Selectable) -> Selectable:
    if isinstance(query, CompoundSelect):
        ordering = query._order_by_clauses or ()
        query = query.order_by(None)  # reset ordering, it will be applied later

        subquery = query.subquery("__cursor_subquery__")
        return select(subquery).order_by(*ordering)

    return query


_selectable_classes = (Select, TextClause, FromStatement, CompoundSelect)


def _get_orm_entity(query: Select[Any]) -> type[Any] | None:
    """Return the mapped ORM entity class for a bare ``select(Model)`` query, else ``None``.

    Returns ``None`` for multi-entity selects, column-level selects
    (``select(Model.col)``), and aliased-entity selects.
    """
    cols_desc = query.column_descriptions
    if len(cols_desc) != 1:
        return None
    desc = cols_desc[0]
    entity = desc.get("entity")
    if entity is None or desc.get("aliased"):
        return None
    expr = desc.get("expr")
    return entity if (expr is not None and expr is entity) else None


def _should_unwrap_scalars_for_query(query: Selectable) -> bool:
    cols_desc = query.column_descriptions  # type: ignore[ty:unresolved-attribute]
    all_cols = [*query._all_selected_columns]

    # select(a, b, c) — multiple entities/columns, no unwrap needed
    if len(cols_desc) != 1:
        return False

    # select(Model) where Model expands to multiple columns — unwrap to get the entity instance
    if len(all_cols) > 1:
        return True

    # select(Model) where Model has a single column — only unwrap for bare entity selects
    return isinstance(query, Select) and _get_orm_entity(query) is not None


def _should_unwrap_scalars(query: Selectable) -> bool:
    if not isinstance(query, _selectable_classes):
        return False

    if isinstance(query, CompoundSelect):
        return False

    try:
        return _should_unwrap_scalars_for_query(query)
    except (AttributeError, NotImplementedError):
        return True

    return False


AnyParams: TypeAlias = AbstractParams | RawParams


def _unwrap_params(params: AnyParams) -> RawParams:
    if isinstance(params, RawParams):
        return params

    return params.to_raw_params().as_limit_offset()


@deprecated("Use fastapi_pagination.ext.raw_sql.create_paginate_query_from_text instead.")
def create_paginate_query_from_text(query: str, params: AnyParams) -> str:
    return _create_paginate_query_from_text(query, _unwrap_params(params))


@deprecated("Use fastapi_pagination.ext.raw_sql.create_count_query_from_text instead.")
def create_count_query_from_text(query: str) -> str:
    return _create_count_query_from_text(query)


def _paginate_from_statement(
    query: FromStatement[Any],
    params: AnyParams,
) -> FromStatement[Any]:
    query = query._generate()
    query.element = create_paginate_query(cast("Selectable", query.element), params)
    return query


def create_paginate_query(query: Selectable, params: AnyParams) -> Selectable:
    if isinstance(query, TextClause):
        return text(_create_paginate_query_from_text(query.text, params))
    if isinstance(query, FromStatement):
        return _paginate_from_statement(query, params)

    return generic_query_apply_params(query, _unwrap_params(params))


def create_count_query(query: Selectable, *, use_subquery: bool = True) -> Selectable:
    if isinstance(query, TextClause):
        return text(_create_count_query_from_text(query.text))
    if isinstance(query, FromStatement):
        return create_count_query(cast("Selectable", query.element))

    query = query.order_by(None).options(noload("*"))

    if use_subquery:
        return select(func.count()).select_from(query.subquery())

    return query.with_only_columns(  # type: ignore[ty:unresolved-attribute]
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


_TSeq = TypeVar("_TSeq", bound=Sequence[Any])


def _unwrap_items(
    items: _TSeq,
    query: Selectable,
    unwrap_mode: UnwrapMode | None = None,
) -> _TSeq:
    # for raw queries we will use legacy mode by default
    # because we can't determine if we should unwrap or not
    if isinstance(query, (TextClause, FromStatement)):  # noqa: SIM108
        unwrap_mode = unwrap_mode or "legacy"
    else:
        unwrap_mode = unwrap_mode or "auto"

    if unwrap_mode == "legacy":
        items = unwrap_scalars(items)  # type: ignore[ty:invalid-assignment]
    elif unwrap_mode == "no-unwrap":
        pass
    elif unwrap_mode == "unwrap":
        items = unwrap_scalars(items, force_unwrap=True)  # type: ignore[ty:invalid-assignment]
    elif unwrap_mode == "auto" and _should_unwrap_scalars(query):
        items = unwrap_scalars(items, force_unwrap=True)  # type: ignore[ty:invalid-assignment]

    return items


@flow
def _total_flow(
    query: Selectable,
    conn: AnyConn,
    count_query: Selectable | None,
    subquery_count: bool,
) -> TotalFlow:
    if count_query is None:
        count_query = create_count_query(query, use_subquery=subquery_count)

    total = yield conn.scalar(count_query)
    return cast(int | None, total)


@flow
def _limit_offset_flow(query: Selectable, conn: AnyConn, raw_params: RawParams) -> LimitOffsetFlow:
    query = create_paginate_query(query, raw_params)
    items = yield conn.execute(query)

    return items


def _apply_inline_count(query: Select[Any], inline_count: ColumnElement[int]) -> Select[Any]:
    """Return *query* with *inline_count* embedded as an extra labeled column.

    For DISTINCT queries, SQL window functions execute before deduplication, so
    ``COUNT(*) OVER()`` would return the pre-DISTINCT row count (wrong). We wrap
    the DISTINCT query in a subquery first, so the window function runs on the
    already-deduplicated rows.

    When the query is a bare ``select(Model)``, we use
    ``aliased(entity, subq, flat=True)`` so result rows still carry proper ORM
    instances rather than plain column tuples.

    Note: ``query._distinct`` and ``query._order_by_clauses`` are private
    SQLAlchemy attributes — there is no public API for detecting
    ``SELECT DISTINCT`` or reading ORDER BY clauses on a ``Select`` object
    in SQLAlchemy 2.0.  ``ColumnAdapter`` (``sqlalchemy.sql.util``) is used
    to remap column references from the original table to the derived subquery.
    """
    if getattr(query, "_distinct", False):
        subq = query.order_by(None).subquery()
        entity = _get_orm_entity(query)
        outer = select(aliased(entity, subq, flat=True)) if entity is not None else select(subq)
        if query._order_by_clauses:
            adapter = ColumnAdapter(subq)
            outer = outer.order_by(*[adapter.traverse(clause) for clause in query._order_by_clauses])
        return outer.add_columns(inline_count.label(_INLINE_COUNT_LABEL))

    return query.add_columns(inline_count.label(_INLINE_COUNT_LABEL))


def _extract_inline_count_total(items: Sequence[Any]) -> int:
    """Extract the window-function total from the first result row.

    Returns 0 when *items* is empty — callers must decide whether that means
    the query matched no rows or the page offset is past the end.
    """
    try:
        return int(items[0]._mapping[_INLINE_COUNT_LABEL])
    except (AttributeError, KeyError):  # pragma: no cover
        return 0


@flow
def _sqlalchemy_inline_count_flow(
    is_async: bool,
    conn: AnyConn,
    query: Select[Any],
    params: AbstractParams | None,
    inline_count: ColumnElement[int],
    *,
    count_query: Selectable | None,
    subquery_count: bool,
    unwrap_mode: UnwrapMode | None,
    transformer: ItemsTransformer | None,
    additional_data: AdditionalData | None,
    unique: bool,
    config: Config | None,
    create_page_factory: Any,
) -> Any:
    """Dedicated flow for inline_count pagination — runs a single query."""

    params_obj, raw_params = verify_params(params, "limit-offset")

    enriched_query = _apply_inline_count(query, inline_count) if raw_params.include_total else query

    paginated_query = create_paginate_query(enriched_query, raw_params)
    result = yield conn.execute(paginated_query)

    with suppress(AttributeError):
        result = _maybe_unique(result, unique)

    total: int | None = None
    if raw_params.include_total:
        if result:
            total = _extract_inline_count_total(result)
        else:
            # No rows returned: the offset is likely past the end of the result set.
            # The inline count cannot be extracted, so fall back to a separate query.
            total = yield from _total_flow(query, conn, count_query, subquery_count)

    items = _unwrap_items(result, query, unwrap_mode)

    resolved_additional_data = yield from additional_data_flow(result, additional_data)

    page = yield from create_page_flow(
        items,
        params_obj,
        total=total,
        transformer=transformer,
        additional_data=resolved_additional_data,
        config=config,
        async_=is_async,
        create_page_factory=create_page_factory,
    )

    return page


@flow
def _cursor_flow(
    query: Selectable,
    conn: AnyConn,
    unique: bool,
    is_async: bool,
    raw_params: CursorRawParams,
) -> CursorFlow:
    query = _prepare_query_for_cursor(query)

    if isinstance(query, TextClause):
        raise ValueError("Cursor pagination cannot be used with raw SQL queries")  # noqa: TRY004
    if isinstance(query, FromStatement):
        raise ValueError("Cursor pagination cannot be used with FromStatement queries")  # noqa: TRY004
    if paging is None:  # pragma: no cover
        raise ImportError("sqlakeyset is not installed")
    if not getattr(query, "_order_by_clauses", True):
        raise ValueError("Cursor pagination requires ordering")

    _select_page = apaging.select_page if is_async else paging.select_page

    page = yield _select_page(
        conn,  # type: ignore[ty:invalid-argument-type]
        selectable=query,  # type: ignore[ty:invalid-argument-type]
        unique=unique,
        per_page=raw_params.size,
        page=raw_params.cursor,  # type: ignore[ty:invalid-argument-type]
    )
    items = [*page]

    data = {
        "current": page.paging.bookmark_current,
        "current_backwards": page.paging.bookmark_current_backwards,
        "previous": page.paging.bookmark_previous if page.paging.has_previous else None,
        "next_": page.paging.bookmark_next if page.paging.has_next else None,
    }

    return items, data


@flow
def _sqlalchemy_flow(
    is_async: bool,
    conn: SyncConn | AsyncConn,
    query: Selectable,
    params: AbstractParams | None = None,
    *,
    subquery_count: bool = True,
    unwrap_mode: UnwrapMode | None = None,
    count_query: Selectable | None = None,
    inline_count: ColumnElement[int] | None = None,
    transformer: ItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    create_page_factory = create_page
    if is_async:
        create_page_factory = partial(greenlet_spawn, create_page_factory)

    if inline_count is not None and isinstance(query, Select):
        page = yield from _sqlalchemy_inline_count_flow(
            is_async,
            conn,
            query,
            params,
            inline_count,
            count_query=count_query,
            subquery_count=subquery_count,
            unwrap_mode=unwrap_mode,
            transformer=transformer,
            additional_data=additional_data,
            unique=unique,
            config=config,
            create_page_factory=create_page_factory,
        )
        return page

    page = yield from generic_flow(
        async_=is_async,
        total_flow=partial(_total_flow, query, conn, count_query, subquery_count),
        limit_offset_flow=partial(_limit_offset_flow, query, conn),
        cursor_flow=partial(_cursor_flow, query, conn, unique, is_async),
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
    query: Selectable,
    unwrap_mode: UnwrapMode | None,
    unique: bool,
) -> Sequence[Any]:
    with suppress(AttributeError):
        items = _maybe_unique(items, unique)

    return _unwrap_items(items, query, unwrap_mode)


def _get_sync_conn_from_async(conn: Any) -> SyncConn:  # pragma: no cover
    if isinstance(conn, async_scoped_session):
        conn = conn()

    with suppress(AttributeError):
        return cast(Session, conn.sync_session)

    with suppress(AttributeError):
        return cast(Connection, conn.sync_connection)

    raise TypeError("conn must be an AsyncConnection or AsyncSession")


# old deprecated paginate function that use sqlalchemy.orm.Query
@overload
def paginate(
    query: Query[Any],
    params: AbstractParams | None = None,
    *,
    subquery_count: bool = True,
    unwrap_mode: UnwrapMode | None = None,
    transformer: SyncItemsTransformer | None = None,
    additional_data: SyncAdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    pass


@overload
def paginate(
    conn: SyncConn,
    query: SelectableOrQuery,
    params: AbstractParams | None = None,
    *,
    count_query: SelectableOrQuery | None = None,
    inline_count: ColumnElement[int] | None = None,
    subquery_count: bool = True,
    unwrap_mode: UnwrapMode | None = None,
    transformer: SyncItemsTransformer | None = None,
    additional_data: SyncAdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    pass


@overload
async def paginate(
    conn: AsyncConn,
    query: Selectable,
    params: AbstractParams | None = None,
    *,
    count_query: Selectable | None = None,
    inline_count: ColumnElement[int] | None = None,
    subquery_count: bool = True,
    unwrap_mode: UnwrapMode | None = None,
    transformer: AsyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    pass


def paginate(*args: Any, **kwargs: Any) -> Any:
    # Guard must run before _prepare_query converts Query → Select, which would
    # make isinstance(query, Query) always False after arg parsing.
    if kwargs.get("inline_count") is not None:
        raw_query = args[0] if args else None
        if not isinstance(raw_query, Query):
            raw_query = args[1] if len(args) >= 2 else kwargs.get("query")
        if isinstance(raw_query, Query):
            raise TypeError(
                "inline_count is not supported with the legacy SQLAlchemy Query API; use a Select-based query instead"
            )

    try:
        assert args
        assert isinstance(args[0], Query)
        (
            query,
            count_query,
            inline_count,
            conn,
            params,
            transformer,
            additional_data,
            unique,
            subquery_count,
            unwrap_mode,
            config,
        ) = _old_paginate_sign(*args, **kwargs)
    except (TypeError, AssertionError):
        (
            query,
            count_query,
            inline_count,
            conn,
            params,
            transformer,
            additional_data,
            unique,
            subquery_count,
            unwrap_mode,
            config,
        ) = _new_paginate_sign(*args, **kwargs)

    try:
        _get_sync_conn_from_async(conn)
    except TypeError:
        pass
    else:
        warnings.warn(
            "Use `apaginate` instead. This function overload will be removed in v0.16.0",
            DeprecationWarning,
            stacklevel=2,
        )

        return apaginate(
            conn=conn,
            query=query,
            params=params,
            count_query=count_query,
            inline_count=inline_count,
            subquery_count=subquery_count,
            unwrap_mode=unwrap_mode,
            transformer=transformer,
            additional_data=additional_data,
            unique=unique,
            config=config,
        )

    return run_sync_flow(
        _sqlalchemy_flow(
            is_async=False,
            conn=conn,
            query=query,
            params=params,
            subquery_count=subquery_count,
            unwrap_mode=unwrap_mode,
            count_query=count_query,
            inline_count=inline_count,
            transformer=transformer,
            additional_data=additional_data,
            unique=unique,
            config=config,
        ),
    )


def _old_paginate_sign(
    query: Query[Any],
    params: AbstractParams | None = None,
    *,
    subquery_count: bool = True,
    unwrap_mode: UnwrapMode | None = None,
    transformer: ItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> tuple[
    Selectable,
    Selectable | None,
    ColumnElement[int] | None,
    SyncConn,
    AbstractParams | None,
    ItemsTransformer | None,
    AdditionalData | None,
    bool,
    bool,
    UnwrapMode | None,
    Config | None,
]:
    if query.session is None:
        raise ValueError("query.session is None")

    session = query.session
    stmt = _prepare_query(query)

    return stmt, None, None, session, params, transformer, additional_data, unique, subquery_count, unwrap_mode, config


def _new_paginate_sign(
    conn: SyncConn,
    query: Selectable,
    params: AbstractParams | None = None,
    *,
    subquery_count: bool = True,
    unwrap_mode: UnwrapMode | None = None,
    count_query: Selectable | None = None,
    inline_count: ColumnElement[int] | None = None,
    transformer: ItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> tuple[
    Selectable,
    Selectable | None,
    ColumnElement[int] | None,
    SyncConn,
    AbstractParams | None,
    ItemsTransformer | None,
    AdditionalData | None,
    bool,
    bool,
    UnwrapMode | None,
    Config | None,
]:
    query = _prepare_query(query)
    count_query = _prepare_query(count_query)

    return (
        query,
        count_query,
        inline_count,
        conn,
        params,
        transformer,
        additional_data,
        unique,
        subquery_count,
        unwrap_mode,
        config,
    )


async def apaginate(
    conn: AsyncConn,
    query: Selectable,
    params: AbstractParams | None = None,
    *,
    count_query: Selectable | None = None,
    inline_count: ColumnElement[int] | None = None,
    subquery_count: bool = True,
    unwrap_mode: UnwrapMode | None = None,
    transformer: AsyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    query = _prepare_query(query)
    count_query = _prepare_query(count_query)

    return await run_async_flow(
        _sqlalchemy_flow(
            is_async=True,
            conn=conn,
            query=query,
            params=params,
            subquery_count=subquery_count,
            unwrap_mode=unwrap_mode,
            count_query=count_query,
            inline_count=inline_count,
            transformer=transformer,
            additional_data=additional_data,
            unique=unique,
            config=config,
        ),
    )
