from __future__ import annotations

__all__ = ["paginate"]

from typing import Any, Optional, Tuple, Union

from gino.crud import CRUDModel
from sqlalchemy import func, literal_column
from sqlalchemy.sql import Select

from ..api import apply_items_transformer, create_page
from ..bases import AbstractParams
from ..types import AdditionalData, AsyncItemsTransformer
from ..utils import verify_params
from .sqlalchemy import create_paginate_query


async def paginate(
    query: Union[Select[Tuple[Any, ...]], CRUDModel],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if isinstance(query, type) and issubclass(query, CRUDModel):
        query = query.query  # type: ignore[attr-defined]

    if raw_params.include_total:
        count_query = func.count(literal_column("*")).select().select_from(query.order_by(None).alias())
        total = await count_query.gino.scalar()  # type: ignore[attr-defined]
    else:
        total = None

    query = create_paginate_query(query, params)
    items = await query.gino.all()  # type: ignore[union-attr]
    t_items = await apply_items_transformer(items, transformer, async_=True)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
