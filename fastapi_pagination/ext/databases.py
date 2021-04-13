from __future__ import annotations

from typing import Optional

from databases import Database
from sqlalchemy import func, select
from sqlalchemy.sql import Select

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams
from .sqlalchemy import paginate_query


async def paginate(
    db: Database,
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    convert_to_mapping: bool = True,
) -> AbstractPage:
    params = resolve_params(params)

    total = await db.fetch_val(select([func.count()]).select_from(query.alias()))
    items = await db.fetch_all(paginate_query(query, params))

    if convert_to_mapping:
        items = [{**item} for item in items]

    return create_page(items, total, params)


__all__ = ["paginate"]
