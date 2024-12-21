from __future__ import annotations

__all__ = [
    "Selectable",
    "create_count_query",
    "create_count_query_from_text",
    "create_paginate_query",
    "create_paginate_query_from_text",
    "paginate",
    "paginate_query",
]

import warnings
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Optional, Sequence, Tuple, TypeVar, Union, overload

from sqlalchemy import func, select, text
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Query, Session, noload, scoped_session
from sqlalchemy.sql import CompoundSelect, Select
from sqlalchemy.sql.elements import TextClause
from typing_extensions import Literal, TypeAlias, deprecated

from ..api import apply_items_transformer, create_page
from ..bases import AbstractPage, AbstractParams, is_cursor
from ..types import AdditionalData, AsyncItemsTransformer, ItemsTransformer, SyncItemsTransformer
from ..utils import verify_params
from .utils import generic_query_apply_params, unwrap_scalars

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection
    from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession


try:
    from sqlalchemy.orm import FromStatement
except ImportError:

    class FromStatement:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError("sqlalchemy.orm.FromStatement is not available")


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


AsyncConn: TypeAlias = "Union[AsyncSession, AsyncConnection, async_scoped_session[Any]]"
SyncConn: TypeAlias = "Union[Session, Connection, scoped_session[Any]]"

UnwrapMode: TypeAlias = Literal[
    "auto",  # default, unwrap only if select is select(model)
    "legacy",  # legacy mode, unwrap only when there is one column in select
    "no-unwrap",  # never unwrap
    "unwrap",  # always unwrap
]

TupleAny: TypeAlias = "Tuple[Any, ...]"
Selectable: TypeAlias = "Union[Select[TupleAny], TextClause, FromStatement[TupleAny], CompoundSelect]"
SelectableOrQuery: TypeAlias = "Union[Selectable, Query[Any]]"

_selectable_classes = (Select, TextClause, FromStatement, CompoundSelect)


def _should_unwrap_scalars(query: Selectable) -> bool:
    if not isinstance(query, _selectable_classes):
        return False

    if isinstance(query, CompoundSelect):
        return False

    try:
        cols_desc = query.column_descriptions  # type: ignore[union-attr]
        all_cols = [*query._all_selected_columns]

        # we have select(a, b, c) no need to unwrap
        if len(cols_desc) != 1:
            return False

        # select one thing and it has more than one column, unwrap
        if len(all_cols) > 1:
            return True

        # select one thing and it has only one column, check if it actually is a select(model)
        if len(all_cols) == 1:
            (desc,) = cols_desc
            expr, entity = [desc.get(key) for key in ("expr", "entity")]

            return expr is not None and expr is entity
    except (AttributeError, NotImplementedError):
        return True

    return False


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
def paginate_query(query: Select[TupleAny], params: AbstractParams) -> Select[TupleAny]:
    return create_paginate_query(query, params)  # type: ignore[return-value]


def _paginate_from_statement(query: FromStatement[TupleAny], params: AbstractParams) -> FromStatement[TupleAny]:
    query = query._generate()
    query.element = create_paginate_query(query.element, params)  # type: ignore[arg-type]
    return query


def create_paginate_query(query: Selectable, params: AbstractParams) -> Selectable:
    if isinstance(query, TextClause):
        return text(create_paginate_query_from_text(query.text, params))
    if isinstance(query, FromStatement):
        return _paginate_from_statement(query, params)

    return generic_query_apply_params(query, params.to_raw_params().as_limit_offset())


def create_count_query(query: Selectable, *, use_subquery: bool = True) -> Selectable:
    if isinstance(query, TextClause):
        return text(create_count_query_from_text(query.text))
    if isinstance(query, FromStatement):
        return create_count_query(query.element)  # type: ignore[arg-type]

    query = query.order_by(None).options(noload("*"))

    if use_subquery:
        return select(func.count()).select_from(query.subquery())

    return query.with_only_columns(  # type: ignore[union-attr]
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
    unwrap_mode: Optional[UnwrapMode] = None,
) -> _TSeq:
    # for raw queries we will use legacy mode by default
    # because we can't determine if we should unwrap or not
    if isinstance(query, (TextClause, FromStatement)):  # noqa: SIM108
        unwrap_mode = unwrap_mode or "legacy"
    else:
        unwrap_mode = unwrap_mode or "auto"

    if unwrap_mode == "legacy":
        items = unwrap_scalars(items)  # type: ignore[assignment]
    elif unwrap_mode == "no-unwrap":
        pass
    elif unwrap_mode == "unwrap":
        items = unwrap_scalars(items, force_unwrap=True)  # type: ignore[assignment]
    elif unwrap_mode == "auto" and _should_unwrap_scalars(query):
        items = unwrap_scalars(items, force_unwrap=True)  # type: ignore[assignment]

    return items


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
    unwrap_mode: Optional[UnwrapMode] = None,
) -> AbstractPage[Any]:
    raw_params = params.to_raw_params()

    if async_:

        def _apply_items_transformer(*args: Any, **kwargs: Any) -> Any:
            return await_only(apply_items_transformer(*args, **kwargs, async_=True))

    else:
        _apply_items_transformer = apply_items_transformer

    total = None
    if raw_params.include_total:
        if count_query is None:
            count_query = create_count_query(query, use_subquery=subquery_count)
        total = conn.scalar(count_query)

    if is_cursor(raw_params):
        if paging is None:
            raise ImportError("sqlakeyset is not installed")
        if not getattr(query, "_order_by_clauses", True):
            raise ValueError("Cursor pagination requires ordering")

        page = paging.select_page(
            conn,  # type: ignore[arg-type]
            selectable=query,  # type: ignore[arg-type]
            per_page=raw_params.size,
            page=raw_params.cursor,  # type: ignore[arg-type]
        )
        items = [*page]
        items = _unwrap_items(items, query, unwrap_mode)
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
    items = _unwrap_items(items, query, unwrap_mode)
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
    unwrap_mode: Optional[UnwrapMode] = None,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    pass


@overload
def paginate(
    conn: SyncConn,
    query: SelectableOrQuery,
    params: Optional[AbstractParams] = None,
    *,
    count_query: Optional[SelectableOrQuery] = None,
    subquery_count: bool = True,
    unwrap_mode: Optional[UnwrapMode] = None,
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
    unwrap_mode: Optional[UnwrapMode] = None,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    pass


def paginate(*args: Any, **kwargs: Any) -> Any:
    try:
        assert args
        assert isinstance(args[0], Query)
        query, count_query, conn, params, transformer, additional_data, unique, subquery_count, unwrap_mode = (
            _old_paginate_sign(*args, **kwargs)
        )
    except (TypeError, AssertionError):
        query, count_query, conn, params, transformer, additional_data, unique, subquery_count, unwrap_mode = (
            _new_paginate_sign(*args, **kwargs)
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
            unwrap_mode=unwrap_mode,
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
        unwrap_mode=unwrap_mode,
        async_=False,
    )


def _old_paginate_sign(
    query: Query[Any],
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    unwrap_mode: Optional[UnwrapMode] = None,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Tuple[
    Select[TupleAny],
    Optional[Selectable],
    SyncConn,
    Optional[AbstractParams],
    Optional[ItemsTransformer],
    AdditionalData,
    bool,
    bool,
    Optional[UnwrapMode],
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
        query = query._statement_20()  # type: ignore[assignment]

    return query, None, session, params, transformer, additional_data, unique, subquery_count, unwrap_mode  # type: ignore


def _new_paginate_sign(
    conn: SyncConn,
    query: Select[TupleAny],
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    unwrap_mode: Optional[UnwrapMode] = None,
    count_query: Optional[Selectable] = None,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Tuple[
    Select[TupleAny],
    Optional[Selectable],
    SyncConn,
    Optional[AbstractParams],
    Optional[ItemsTransformer],
    AdditionalData,
    bool,
    bool,
    Optional[UnwrapMode],
]:
    with suppress(AttributeError):
        query = query._statement_20()  # type: ignore[attr-defined]

    return query, count_query, conn, params, transformer, additional_data, unique, subquery_count, unwrap_mode
