__all__ = ["apaginate", "paginate"]

from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial
from typing import Any, TypeAlias, cast

from psycopg import AsyncConnection, AsyncCursor, Connection, Cursor
from psycopg.rows import AsyncRowFactory, RowFactory, tuple_row
from psycopg.sql import SQL, Composed
from typing_extensions import LiteralString

from fastapi_pagination.bases import AbstractParams, RawParams
from fastapi_pagination.config import Config
from fastapi_pagination.flow import flow, run_async_flow, run_sync_flow
from fastapi_pagination.flows import generic_flow
from fastapi_pagination.types import AdditionalData, AsyncItemsTransformer, ItemsTransformer

from .sqlalchemy import create_count_query_from_text, create_paginate_query_from_text

_SyncConn: TypeAlias = Connection[Any] | Cursor[Any]
_AsyncConn: TypeAlias = AsyncConnection[Any] | AsyncCursor[Any]
_AnyConn: TypeAlias = _SyncConn | _AsyncConn

_InputQuery: TypeAlias = str | LiteralString | SQL | Composed
_AnyFactory: TypeAlias = RowFactory[Any] | AsyncRowFactory[Any]


@contextmanager
def _switch_factory(conn: _AnyConn, factory: _AnyFactory) -> Iterator[None]:
    original_factory, conn.row_factory = conn.row_factory, factory  # type: ignore[invalid-assignment]
    try:
        yield
    finally:
        conn.row_factory = original_factory  # type: ignore[invalid-assignment]


def _compile_query(query: _InputQuery, conn: _AnyConn) -> LiteralString:
    if isinstance(query, SQL | Composed):
        query = query.as_string(conn)

    return cast(LiteralString, query)


@flow
def _psycopg_limit_offset_flow(
    conn: _AnyConn,
    query: _InputQuery,
    args: tuple[Any, ...],
    raw_params: RawParams,
) -> Any:
    query = _compile_query(query, conn)
    cursor = yield conn.execute(cast(LiteralString, create_paginate_query_from_text(query, raw_params)), args)
    items = yield cursor.fetchall()

    return [*items]


@flow
def _psycopg_total_flow(
    conn: _AnyConn,
    query: _InputQuery,
    args: tuple[Any, ...],
) -> Any:
    query = _compile_query(query, conn)

    with _switch_factory(conn, tuple_row):
        cursor = yield conn.execute(cast(LiteralString, create_count_query_from_text(query)), args)
        row = yield cursor.fetchone()

        if row:
            (value,) = row
            return value

        return None  # pragma: no cover


async def apaginate(
    conn: _AsyncConn,
    query: _InputQuery,
    *args: Any,
    transformer: AsyncItemsTransformer | None = None,
    params: AbstractParams | None = None,
    additional_data: AdditionalData | None = None,
    config: Config | None = None,
) -> Any:
    return await run_async_flow(
        generic_flow(
            async_=True,
            limit_offset_flow=partial(_psycopg_limit_offset_flow, conn, query, args),
            total_flow=partial(_psycopg_total_flow, conn, query, args),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )


def paginate(
    conn: _SyncConn,
    query: _InputQuery,
    *args: Any,
    transformer: ItemsTransformer | None = None,
    params: AbstractParams | None = None,
    additional_data: AdditionalData | None = None,
    config: Config | None = None,
) -> Any:
    return run_sync_flow(
        generic_flow(
            async_=False,
            limit_offset_flow=partial(_psycopg_limit_offset_flow, conn, query, args),
            total_flow=partial(_psycopg_total_flow, conn, query, args),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )
