from __future__ import annotations

from databases import Database
from sqlalchemy import func, select
from sqlalchemy.sql import Select

from ..page import BasePage, create_page
from ..params import PaginationParamsType
from .sqlalchemy import paginate_query


async def paginate(db: Database, query: Select, params: PaginationParamsType) -> BasePage:
    total = await db.fetch_val(select([func.count()]).select_from(query))
    items = await db.fetch_all(paginate_query(query, params))

    return create_page(items, total, params)


__all__ = ["paginate"]
