from __future__ import annotations

__all__ = ["apaginate", "paginate"]

from collections.abc import Sequence
from typing import Any, Optional

from databases import Database
from sqlalchemy.sql import Select
from typing_extensions import deprecated

from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.config import Config
from fastapi_pagination.flow import flow_expr, run_async_flow
from fastapi_pagination.flows import generic_flow
from fastapi_pagination.types import AdditionalData, AsyncItemsTransformer

from .sqlalchemy import create_count_query, create_paginate_query


def _to_mappings(items: Sequence[Any]) -> Sequence[Any]:
    return [{**item._mapping} for item in items]


async def apaginate(
    db: Database,
    query: Select[tuple[Any, ...]],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    convert_to_mapping: bool = True,
    use_subquery: bool = True,
    config: Optional[Config] = None,
) -> Any:
    inner_transformer = None
    if convert_to_mapping:
        inner_transformer = _to_mappings

    return await run_async_flow(
        generic_flow(
            async_=True,
            total_flow=flow_expr(lambda: db.fetch_val(create_count_query(query, use_subquery=use_subquery))),
            limit_offset_flow=flow_expr(lambda raw_params: db.fetch_all(create_paginate_query(query, raw_params))),
            params=params,
            inner_transformer=inner_transformer,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )


@deprecated("Use `apaginate` instead. This function will be removed in v0.15.0")
async def paginate(
    db: Database,
    query: Select[tuple[Any, ...]],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    convert_to_mapping: bool = True,
    use_subquery: bool = True,
    config: Optional[Config] = None,
) -> Any:
    return await apaginate(
        db,
        query,
        params=params,
        transformer=transformer,
        additional_data=additional_data,
        convert_to_mapping=convert_to_mapping,
        use_subquery=use_subquery,
        config=config,
    )
