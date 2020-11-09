from __future__ import annotations

from typing import TypeVar

from sqlalchemy.orm import Query
from sqlalchemy.sql import Select

from ..page import BasePage, create_page
from ..params import PaginationParams, PaginationParamsType

T = TypeVar("T", Select, Query)


def paginate_query(query: T, params: PaginationParamsType) -> T:
    params = params.to_limit_offset()
    return query.limit(params.limit).offset(params.offset)  # type: ignore


def paginate(query: Query, params: PaginationParams) -> BasePage:
    total = query.count()
    items = paginate_query(query, params).all()

    return create_page(items, total, params)


__all__ = ["paginate_query", "paginate"]
