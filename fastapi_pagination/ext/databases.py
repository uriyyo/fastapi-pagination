from __future__ import annotations

__all__ = ["paginate"]

from typing import Any, List, Optional

from databases import Database
from sqlalchemy import func, select
from sqlalchemy.sql import Select

from ..api import apply_items_transformer, create_page
from ..bases import AbstractParams
from ..types import AdditionalData, AsyncItemsTransformer
from ..utils import verify_params
from .sqlalchemy import paginate_query


async def paginate(
    db: Database,
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    convert_to_mapping: bool = True,
) -> Any:
    params, _ = verify_params(params, "limit-offset")

    total = await db.fetch_val(select([func.count()]).select_from(query.order_by(None).alias()))
    query = paginate_query(query, params)
    raw_items = await db.fetch_all(query)

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
