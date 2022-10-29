from __future__ import annotations

from typing import Any, List, Optional

from databases import Database
from sqlalchemy import func, select
from sqlalchemy.sql import Select

from ..api import create_page
from ..bases import AbstractPage, AbstractParams
from ..types import AdditionalData
from ..utils import verify_params
from .sqlalchemy import paginate_query


async def paginate(
    db: Database,
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
    convert_to_mapping: bool = True,
) -> AbstractPage[Any]:
    params, _ = verify_params(params, "limit-offset")

    total = await db.fetch_val(select([func.count()]).select_from(query.order_by(None).alias()))
    query = paginate_query(query, params)
    items: List[Any] = await db.fetch_all(query)

    if convert_to_mapping:
        items = [{**item} for item in items]

    return create_page(items, total, params, **(additional_data or {}))


__all__ = [
    "paginate",
]
