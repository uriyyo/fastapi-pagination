from __future__ import annotations

from typing import TypeVar

from databases import Database
from sqlalchemy import select, func
from sqlalchemy.sql import Select

from .sqlalchemy import paginate_query
from ..page import create_page, BasePage
from ..params import PaginationParamsType

T = TypeVar("T")


async def paginate(
    db: Database, query: Select[T], params: PaginationParamsType
) -> BasePage[T]:
    total = await db.fetch_val(select([func.count()]).select_from(query))
    items = await db.fetch_all(paginate_query(query, params))

    return create_page(items, total, params)


__all__ = ["paginate"]
