from __future__ import annotations

from typing import TypeVar

from sqlalchemy import func
from sqlalchemy.sql import Select

from .sqlalchemy import paginate_query
from ..page import create_page, BasePage
from ..params import PaginationParamsType

T = TypeVar("T")


async def paginate(query: Select[T], params: PaginationParamsType) -> BasePage[T]:
    total = await func.count().select().select_from(query.alias()).gino.scalar()  # type: ignore
    items = await paginate_query(query, params).gino.all()  # type: ignore

    return create_page(items, total, params)


__all__ = ["paginate"]
