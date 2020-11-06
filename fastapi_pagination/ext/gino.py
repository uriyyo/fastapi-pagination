from __future__ import annotations
from typing import TypeVar

from sqlalchemy.sql import Select

from .sqlalchemy import transform_query
from ..page import create_page, BasePage
from ..params import PaginationParamsType

T = TypeVar("T")


async def paginate(query: Select[T], params: PaginationParamsType) -> BasePage[T]:
    count, select = transform_query(query, params)

    total = await count.gino.scalar()  # type: ignore
    items = await select.gino.all()  # type: ignore

    return create_page(items, total, params)


__all__ = ["paginate"]
