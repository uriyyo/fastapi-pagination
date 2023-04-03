from __future__ import annotations

__all__ = ["paginate"]

from typing import Any, List, Optional

from databases import Database
from sqlalchemy import func, select
from sqlalchemy.sql import Select

from .sqlalchemy import paginate_query
from ..api import create_page
from ..bases import AbstractParams
from ..types import AdditionalData
from ..utils import verify_params


async def paginate(
    db: Database,
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
    convert_to_mapping: bool = True,
) -> Any:
    params, _ = verify_params(params, "limit-offset")

    total = await db.fetch_val(select([func.count()]).select_from(query.order_by(None).alias()))
    query = paginate_query(query, params)
    raw_items = await db.fetch_all(query)

    items: List[Any] = raw_items
    if convert_to_mapping:
        items = [{**item._mapping} for item in raw_items]

    return create_page(items, total, params, **(additional_data or {}))
