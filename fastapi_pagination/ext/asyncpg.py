__all__ = ["apaginate", "paginate"]

from functools import partial
from typing import Any, Optional

from asyncpg import Connection
from typing_extensions import deprecated

from fastapi_pagination.bases import AbstractParams, RawParams
from fastapi_pagination.config import Config
from fastapi_pagination.flow import flow, flow_expr, run_async_flow
from fastapi_pagination.flows import generic_flow
from fastapi_pagination.types import AdditionalData, AsyncItemsTransformer

from .sqlalchemy import create_count_query_from_text, create_paginate_query_from_text


@flow
def _asyncpg_limit_offset_flow(
    conn: Connection,
    query: str,
    args: tuple[Any, ...],
    raw_params: RawParams,
) -> Any:
    items = yield conn.fetch(create_paginate_query_from_text(query, raw_params), *args)

    return [{**r} for r in items]


# FIXME: find a way to parse raw sql queries
async def apaginate(
    conn: Connection,
    query: str,
    *args: Any,
    transformer: Optional[AsyncItemsTransformer] = None,
    params: Optional[AbstractParams] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
) -> Any:
    return await run_async_flow(
        generic_flow(
            async_=True,
            limit_offset_flow=partial(_asyncpg_limit_offset_flow, conn, query, args),
            total_flow=flow_expr(lambda: conn.fetchval(create_count_query_from_text(query), *args)),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )


@deprecated("Use `apaginate` instead. This function will be removed in v0.14.0")
async def paginate(
    conn: Connection,
    query: str,
    *args: Any,
    transformer: Optional[AsyncItemsTransformer] = None,
    params: Optional[AbstractParams] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
) -> Any:
    return await paginate(
        conn,
        query,
        *args,
        transformer=transformer,
        params=params,
        additional_data=additional_data,
        config=config,
    )
