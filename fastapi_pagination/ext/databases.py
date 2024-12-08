from __future__ import annotations

__all__ = ["paginate"]

from typing import Any, List, Optional, Tuple

from databases import Database
from sqlalchemy.sql import Select

from ..api import apply_items_transformer, create_page
from ..bases import AbstractParams
from ..types import AdditionalData, AsyncItemsTransformer
from ..utils import verify_params
from .sqlalchemy import create_count_query, create_paginate_query


async def paginate(
    db: Database,
    query: Select[Tuple[Any, ...]],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    convert_to_mapping: bool = True,
    use_subquery: bool = True,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if raw_params.include_total:
        total = await db.fetch_val(create_count_query(query, use_subquery=use_subquery))
    else:
        total = None

    paginated_query = create_paginate_query(query, params)
    raw_items = await db.fetch_all(paginated_query)

    items: List[Any] = raw_items
    if convert_to_mapping:
        items = [{**item._mapping} for item in raw_items]

    t_items = await apply_items_transformer(items, transformer, async_=True)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
