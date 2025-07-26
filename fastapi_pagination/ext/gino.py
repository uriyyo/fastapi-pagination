from __future__ import annotations

__all__ = ["apaginate", "paginate"]

from typing import Any, Optional, Union

from gino.crud import CRUDModel
from sqlalchemy import func, literal_column
from sqlalchemy.sql import Select
from typing_extensions import deprecated

from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.config import Config
from fastapi_pagination.flow import flow_expr, run_async_flow
from fastapi_pagination.flows import generic_flow
from fastapi_pagination.types import AdditionalData, AsyncItemsTransformer

from .sqlalchemy import create_paginate_query


async def apaginate(
    query: Union[Select[tuple[Any, ...]], CRUDModel],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
) -> Any:
    if isinstance(query, type) and issubclass(query, CRUDModel):
        query = query.query  # type: ignore[attr-defined]

    return await run_async_flow(
        generic_flow(
            total_flow=flow_expr(
                lambda: func.count(literal_column("*"))
                .select()
                .select_from(
                    query.order_by(None).alias(),
                )
                .gino.scalar()  # type: ignore[attr-defined]
            ),
            limit_offset_flow=flow_expr(
                lambda raw_params: create_paginate_query(query, raw_params).gino.all()  # type: ignore[union-attr]
            ),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
            async_=True,
        )
    )


@deprecated("Use `apaginate` instead. This function will be removed in v0.15.0")
async def paginate(
    query: Union[Select[tuple[Any, ...]], CRUDModel],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
) -> Any:
    return await apaginate(
        query,
        params=params,
        transformer=transformer,
        additional_data=additional_data,
        config=config,
    )
