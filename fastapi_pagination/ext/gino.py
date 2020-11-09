from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.sql import Select

from ..page import BasePage, create_page
from ..params import PaginationParamsType
from .sqlalchemy import paginate_query


async def paginate(query: Select, params: PaginationParamsType) -> BasePage:
    count_query = query

    # Check if it's a ModelLoader to add distinct columns to have correct count value
    loader = getattr(query, "_execution_options", {}).get("loader")
    if loader and loader._distinct:
        count_query = query.distinct(*loader._distinct)

    total = await func.count().select().select_from(count_query.alias()).gino.scalar()
    items = await paginate_query(query, params).gino.all()  # type: ignore

    return create_page(items, total, params)


__all__ = ["paginate"]
