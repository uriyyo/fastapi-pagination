from __future__ import annotations

from typing import TypeVar

from sqlalchemy import func
from sqlalchemy.sql import Select

from ..page import BasePage, create_page
from ..params import PaginationParamsType
from .sqlalchemy import paginate_query


async def paginate(query: Select, params: PaginationParamsType) -> BasePage:
    total = await func.count().select().select_from(query.alias()).gino.scalar()
    items = await paginate_query(query, params).gino.all()  # type: ignore

    return create_page(items, total, params)


__all__ = ["paginate"]
